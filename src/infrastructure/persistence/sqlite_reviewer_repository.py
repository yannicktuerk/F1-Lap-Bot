"""SQLite repository for reviewer service data and evaluation tracking."""
import sqlite3
import aiosqlite
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from ...domain.value_objects.review_outcomes import (
    ReviewOutcome, AttemptPattern, ReviewClassification, PendingReview, PerformanceMetrics
)


class SQLiteReviewerRepository:
    """SQLite adapter for reviewer service data persistence."""
    
    def __init__(self, database_path: Optional[str] = None):
        if database_path is None:
            # Auto-detect database location
            import os
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(script_dir, "..", "..", "..")
            possible_paths = [
                os.path.join(project_root, "f1_lap_bot.db"),
                os.path.join(project_root, "data", "f1_lap_bot.db"),
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    self._database_path = path
                    break
            else:
                self._database_path = possible_paths[0]
        else:
            self._database_path = database_path
    
    async def _ensure_tables_exist(self):
        """Create reviewer tables if they don't exist."""
        async with aiosqlite.connect(self._database_path) as db:
            # Pending reviews table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS pending_reviews (
                    action_id TEXT PRIMARY KEY,
                    corner_id TEXT NOT NULL,
                    action_pattern TEXT NOT NULL,
                    intensity_level TEXT NOT NULL,
                    coaching_timestamp TEXT NOT NULL,
                    target_lap_count INTEGER NOT NULL DEFAULT 3,
                    laps_evaluated INTEGER NOT NULL DEFAULT 0,
                    baseline_metrics TEXT,
                    is_complete BOOLEAN NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    INDEX(corner_id),
                    INDEX(action_pattern),
                    INDEX(is_complete),
                    INDEX(coaching_timestamp)
                )
            """)
            
            # Performance metrics table (for evaluation laps)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    metrics_id TEXT PRIMARY KEY,
                    action_id TEXT NOT NULL,
                    lap_number INTEGER NOT NULL,
                    apex_speed_kmh REAL NOT NULL,
                    exit_speed_kmh REAL NOT NULL,
                    sector_time_ms REAL NOT NULL,
                    max_front_slip REAL NOT NULL,
                    max_rear_slip REAL NOT NULL,
                    slip_red_duration_ms REAL NOT NULL,
                    steering_smoothness REAL NOT NULL,
                    throttle_progression REAL NOT NULL,
                    brake_consistency REAL NOT NULL,
                    sector_delta_ms REAL NOT NULL,
                    corner_delta_ms REAL NOT NULL,
                    recorded_at TEXT NOT NULL,
                    FOREIGN KEY (action_id) REFERENCES pending_reviews (action_id),
                    INDEX(action_id),
                    INDEX(lap_number),
                    INDEX(recorded_at)
                )
            """)
            
            # Review classifications table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS review_classifications (
                    classification_id TEXT PRIMARY KEY,
                    action_id TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    primary_pattern TEXT,
                    performance_improvement BOOLEAN NOT NULL,
                    classification_reason TEXT NOT NULL,
                    recommendations TEXT NOT NULL,
                    pattern_detections TEXT NOT NULL,
                    classified_at TEXT NOT NULL,
                    FOREIGN KEY (action_id) REFERENCES pending_reviews (action_id),
                    INDEX(action_id),
                    INDEX(outcome),
                    INDEX(classified_at)
                )
            """)
            
            # Pattern detection results table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS pattern_detections (
                    detection_id TEXT PRIMARY KEY,
                    action_id TEXT NOT NULL,
                    pattern TEXT NOT NULL,
                    detected BOOLEAN NOT NULL,
                    confidence REAL NOT NULL,
                    evidence TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    FOREIGN KEY (action_id) REFERENCES pending_reviews (action_id),
                    INDEX(action_id),
                    INDEX(pattern),
                    INDEX(detected),
                    INDEX(detected_at)
                )
            """)
            
            # Reviewer statistics table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reviewer_statistics (
                    stat_id TEXT PRIMARY KEY,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    total_reviews INTEGER NOT NULL,
                    success_count INTEGER NOT NULL,
                    overshoot_count INTEGER NOT NULL,
                    no_attempt_count INTEGER NOT NULL,
                    inconclusive_count INTEGER NOT NULL,
                    avg_evaluation_laps REAL NOT NULL,
                    avg_confidence REAL NOT NULL,
                    computed_at TEXT NOT NULL,
                    INDEX(period_start),
                    INDEX(computed_at)
                )
            """)
            
            await db.commit()
    
    async def save_pending_review(self, pending_review: PendingReview) -> bool:
        """
        Save pending review to database.
        
        Args:
            pending_review: Pending review to save
            
        Returns:
            True if successful
        """
        await self._ensure_tables_exist()
        
        baseline_metrics_json = None
        if pending_review.baseline_metrics:
            baseline_metrics_json = json.dumps({
                'apex_speed_kmh': pending_review.baseline_metrics.apex_speed_kmh,
                'exit_speed_kmh': pending_review.baseline_metrics.exit_speed_kmh,
                'sector_time_ms': pending_review.baseline_metrics.sector_time_ms,
                'max_front_slip': pending_review.baseline_metrics.max_front_slip,
                'max_rear_slip': pending_review.baseline_metrics.max_rear_slip,
                'slip_red_duration_ms': pending_review.baseline_metrics.slip_red_duration_ms,
                'steering_smoothness': pending_review.baseline_metrics.steering_smoothness,
                'throttle_progression': pending_review.baseline_metrics.throttle_progression,
                'brake_consistency': pending_review.baseline_metrics.brake_consistency,
                'sector_delta_ms': pending_review.baseline_metrics.sector_delta_ms,
                'corner_delta_ms': pending_review.baseline_metrics.corner_delta_ms
            })
        
        try:
            async with aiosqlite.connect(self._database_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO pending_reviews (
                        action_id, corner_id, action_pattern, intensity_level,
                        coaching_timestamp, target_lap_count, laps_evaluated,
                        baseline_metrics, is_complete, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pending_review.action_id, pending_review.corner_id,
                    pending_review.action_pattern.value, pending_review.intensity_level,
                    pending_review.coaching_timestamp.isoformat(), pending_review.target_lap_count,
                    pending_review.laps_evaluated, baseline_metrics_json,
                    pending_review.is_complete, datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat()
                ))
                await db.commit()
            return True
        except Exception as e:
            print(f"Error saving pending review: {e}")
            return False
    
    async def save_performance_metrics(self, action_id: str, lap_number: int, metrics: PerformanceMetrics) -> str:
        """
        Save performance metrics for an evaluation lap.
        
        Args:
            action_id: Action being evaluated
            lap_number: Lap number in evaluation sequence
            metrics: Performance metrics
            
        Returns:
            Metrics ID
        """
        await self._ensure_tables_exist()
        
        metrics_id = f"metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("""
                INSERT INTO performance_metrics (
                    metrics_id, action_id, lap_number, apex_speed_kmh, exit_speed_kmh,
                    sector_time_ms, max_front_slip, max_rear_slip, slip_red_duration_ms,
                    steering_smoothness, throttle_progression, brake_consistency,
                    sector_delta_ms, corner_delta_ms, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics_id, action_id, lap_number, metrics.apex_speed_kmh,
                metrics.exit_speed_kmh, metrics.sector_time_ms, metrics.max_front_slip,
                metrics.max_rear_slip, metrics.slip_red_duration_ms, metrics.steering_smoothness,
                metrics.throttle_progression, metrics.brake_consistency, metrics.sector_delta_ms,
                metrics.corner_delta_ms, datetime.utcnow().isoformat()
            ))
            await db.commit()
        
        return metrics_id
    
    async def save_review_classification(self, classification: ReviewClassification, action_id: str) -> str:
        """
        Save review classification.
        
        Args:
            classification: Review classification
            action_id: Action that was classified
            
        Returns:
            Classification ID
        """
        await self._ensure_tables_exist()
        
        classification_id = f"class_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Convert pattern detections to JSON
        pattern_detections_json = json.dumps([
            {
                'pattern': detection.pattern.value,
                'detected': detection.detected,
                'confidence': detection.confidence,
                'evidence': detection.evidence
            }
            for detection in classification.pattern_detections
        ])
        
        # Convert recommendations to JSON
        recommendations_json = json.dumps(classification.recommendations)
        
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("""
                INSERT INTO review_classifications (
                    classification_id, action_id, outcome, confidence,
                    primary_pattern, performance_improvement, classification_reason,
                    recommendations, pattern_detections, classified_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                classification_id, action_id, classification.outcome.value,
                classification.confidence, 
                classification.primary_pattern.value if classification.primary_pattern else None,
                classification.performance_improvement, classification.classification_reason,
                recommendations_json, pattern_detections_json, datetime.utcnow().isoformat()
            ))
            await db.commit()
        
        return classification_id
    
    async def get_pending_review(self, action_id: str) -> Optional[PendingReview]:
        """
        Get pending review by action ID.
        
        Args:
            action_id: Action ID to look up
            
        Returns:
            PendingReview if found, None otherwise
        """
        await self._ensure_tables_exist()
        
        async with aiosqlite.connect(self._database_path) as db:
            cursor = await db.execute("""
                SELECT action_id, corner_id, action_pattern, intensity_level,
                       coaching_timestamp, target_lap_count, laps_evaluated,
                       baseline_metrics, is_complete
                FROM pending_reviews 
                WHERE action_id = ?
            """, (action_id,))
            row = await cursor.fetchone()
        
        if not row:
            return None
        
        # Parse baseline metrics
        baseline_metrics = None
        if row[7]:
            metrics_data = json.loads(row[7])
            baseline_metrics = PerformanceMetrics(**metrics_data)
        
        # Get evaluation metrics
        evaluation_metrics = await self._get_evaluation_metrics(action_id)
        
        pending_review = PendingReview(
            action_id=row[0],
            corner_id=row[1],
            action_pattern=AttemptPattern(row[2]),
            intensity_level=row[3],
            coaching_timestamp=datetime.fromisoformat(row[4]),
            target_lap_count=row[5],
            laps_evaluated=row[6],
            baseline_metrics=baseline_metrics,
            evaluation_metrics=evaluation_metrics,
            is_complete=bool(row[8])
        )
        
        # Get final classification if complete
        if pending_review.is_complete:
            pending_review.final_classification = await self._get_classification(action_id)
        
        return pending_review
    
    async def _get_evaluation_metrics(self, action_id: str) -> List[PerformanceMetrics]:
        """Get evaluation metrics for an action."""
        async with aiosqlite.connect(self._database_path) as db:
            cursor = await db.execute("""
                SELECT apex_speed_kmh, exit_speed_kmh, sector_time_ms, max_front_slip,
                       max_rear_slip, slip_red_duration_ms, steering_smoothness,
                       throttle_progression, brake_consistency, sector_delta_ms, corner_delta_ms
                FROM performance_metrics 
                WHERE action_id = ?
                ORDER BY lap_number
            """, (action_id,))
            rows = await cursor.fetchall()
        
        metrics_list = []
        for row in rows:
            metrics = PerformanceMetrics(
                apex_speed_kmh=row[0], exit_speed_kmh=row[1], sector_time_ms=row[2],
                max_front_slip=row[3], max_rear_slip=row[4], slip_red_duration_ms=row[5],
                steering_smoothness=row[6], throttle_progression=row[7], brake_consistency=row[8],
                sector_delta_ms=row[9], corner_delta_ms=row[10]
            )
            metrics_list.append(metrics)
        
        return metrics_list
    
    async def _get_classification(self, action_id: str) -> Optional[ReviewClassification]:
        """Get review classification for an action."""
        async with aiosqlite.connect(self._database_path) as db:
            cursor = await db.execute("""
                SELECT outcome, confidence, primary_pattern, performance_improvement,
                       classification_reason, recommendations, pattern_detections
                FROM review_classifications 
                WHERE action_id = ?
                ORDER BY classified_at DESC
                LIMIT 1
            """, (action_id,))
            row = await cursor.fetchone()
        
        if not row:
            return None
        
        # Parse pattern detections
        pattern_detections_data = json.loads(row[6])
        # Note: Would need to reconstruct PatternDetection objects here
        # For now, return basic classification without full pattern details
        
        # Parse recommendations
        recommendations = json.loads(row[5])
        
        # Get latest performance metrics
        evaluation_metrics = await self._get_evaluation_metrics(action_id)
        latest_metrics = evaluation_metrics[-1] if evaluation_metrics else None
        
        return ReviewClassification(
            outcome=ReviewOutcome(row[0]),
            confidence=row[1],
            pattern_detections=[],  # Simplified for now
            primary_pattern=AttemptPattern(row[2]) if row[2] else None,
            performance_metrics=latest_metrics,
            performance_improvement=bool(row[3]),
            classification_reason=row[4],
            recommendations=recommendations
        )
    
    async def get_active_reviews(self) -> List[PendingReview]:
        """Get all active (incomplete) reviews."""
        await self._ensure_tables_exist()
        
        async with aiosqlite.connect(self._database_path) as db:
            cursor = await db.execute("""
                SELECT action_id FROM pending_reviews 
                WHERE is_complete = 0
                ORDER BY coaching_timestamp DESC
            """)
            rows = await cursor.fetchall()
        
        active_reviews = []
        for row in rows:
            review = await self.get_pending_review(row[0])
            if review:
                active_reviews.append(review)
        
        return active_reviews
    
    async def get_review_statistics(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Get review statistics for the specified period.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Statistics dictionary
        """
        await self._ensure_tables_exist()
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        
        async with aiosqlite.connect(self._database_path) as db:
            # Get outcome counts
            cursor = await db.execute("""
                SELECT outcome, COUNT(*) 
                FROM review_classifications rc
                JOIN pending_reviews pr ON rc.action_id = pr.action_id
                WHERE pr.coaching_timestamp >= ?
                GROUP BY outcome
            """, (cutoff_date,))
            outcome_counts = dict(await cursor.fetchall())
            
            # Get average confidence
            cursor = await db.execute("""
                SELECT AVG(confidence)
                FROM review_classifications rc
                JOIN pending_reviews pr ON rc.action_id = pr.action_id
                WHERE pr.coaching_timestamp >= ?
            """, (cutoff_date,))
            avg_confidence = (await cursor.fetchone())[0] or 0.0
            
            # Get average evaluation laps
            cursor = await db.execute("""
                SELECT AVG(laps_evaluated)
                FROM pending_reviews
                WHERE coaching_timestamp >= ? AND is_complete = 1
            """, (cutoff_date,))
            avg_eval_laps = (await cursor.fetchone())[0] or 0.0
        
        total_reviews = sum(outcome_counts.values())
        
        return {
            "total_reviews": total_reviews,
            "outcome_counts": outcome_counts,
            "success_rate": outcome_counts.get("success", 0) / max(1, total_reviews),
            "overshoot_rate": outcome_counts.get("overshoot", 0) / max(1, total_reviews),
            "no_attempt_rate": outcome_counts.get("no_attempt", 0) / max(1, total_reviews),
            "average_confidence": avg_confidence,
            "average_evaluation_laps": avg_eval_laps,
            "period_days": days_back
        }
    
    async def get_pattern_detection_stats(self, days_back: int = 30) -> Dict[str, Any]:
        """Get pattern detection statistics."""
        await self._ensure_tables_exist()
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        
        async with aiosqlite.connect(self._database_path) as db:
            cursor = await db.execute("""
                SELECT pattern, detected, AVG(confidence), COUNT(*)
                FROM pattern_detections
                WHERE detected_at >= ?
                GROUP BY pattern, detected
                ORDER BY pattern, detected
            """, (cutoff_date,))
            rows = await cursor.fetchall()
        
        pattern_stats = {}
        for row in rows:
            pattern = row[0]
            if pattern not in pattern_stats:
                pattern_stats[pattern] = {"detected": 0, "not_detected": 0, "avg_confidence": 0}
            
            if row[1]:  # detected
                pattern_stats[pattern]["detected"] = row[3]
                pattern_stats[pattern]["avg_confidence"] = row[2]
            else:
                pattern_stats[pattern]["not_detected"] = row[3]
        
        return pattern_stats
    
    async def cleanup_old_reviews(self, days_to_keep: int = 90) -> int:
        """
        Cleanup old completed reviews.
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            Number of reviews cleaned up
        """
        await self._ensure_tables_exist()
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat()
        
        async with aiosqlite.connect(self._database_path) as db:
            # Get action IDs to cleanup
            cursor = await db.execute("""
                SELECT action_id FROM pending_reviews 
                WHERE is_complete = 1 AND coaching_timestamp < ?
            """, (cutoff_date,))
            action_ids = [row[0] for row in await cursor.fetchall()]
            
            if not action_ids:
                return 0
            
            # Delete related records
            placeholders = ','.join(['?' for _ in action_ids])
            
            await db.execute(f"DELETE FROM pattern_detections WHERE action_id IN ({placeholders})", action_ids)
            await db.execute(f"DELETE FROM performance_metrics WHERE action_id IN ({placeholders})", action_ids)
            await db.execute(f"DELETE FROM review_classifications WHERE action_id IN ({placeholders})", action_ids)
            await db.execute(f"DELETE FROM pending_reviews WHERE action_id IN ({placeholders})", action_ids)
            
            await db.commit()
        
        return len(action_ids)
    
    async def get_reviewer_repository_stats(self) -> Dict[str, Any]:
        """Get repository statistics."""
        await self._ensure_tables_exist()
        
        async with aiosqlite.connect(self._database_path) as db:
            pending_count = await db.execute("SELECT COUNT(*) FROM pending_reviews")
            pending_count = (await pending_count.fetchone())[0]
            
            completed_count = await db.execute("SELECT COUNT(*) FROM pending_reviews WHERE is_complete = 1")
            completed_count = (await completed_count.fetchone())[0]
            
            active_count = await db.execute("SELECT COUNT(*) FROM pending_reviews WHERE is_complete = 0")
            active_count = (await active_count.fetchone())[0]
            
            metrics_count = await db.execute("SELECT COUNT(*) FROM performance_metrics")
            metrics_count = (await metrics_count.fetchone())[0]
            
            classifications_count = await db.execute("SELECT COUNT(*) FROM review_classifications")
            classifications_count = (await classifications_count.fetchone())[0]
        
        return {
            "total_reviews": pending_count,
            "completed_reviews": completed_count,
            "active_reviews": active_count,
            "performance_metrics_stored": metrics_count,
            "classifications_stored": classifications_count,
            "database_path": self._database_path
        }
"""SQLite repository for utility estimation data and model tracking."""
import sqlite3
import aiosqlite
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from ...domain.value_objects.action_utility import (
    UtilityFeatures, UtilityEvaluation, ActionUtility, ConfidenceLevel
)


class SQLiteUtilityRepository:
    """SQLite adapter for utility estimation data persistence."""
    
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
        """Create utility estimation tables if they don't exist."""
        async with aiosqlite.connect(self._database_path) as db:
            # Utility features table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS utility_features (
                    feature_id TEXT PRIMARY KEY,
                    corner_id INTEGER NOT NULL,
                    corner_type TEXT NOT NULL,
                    entry_speed_kmh REAL NOT NULL,
                    min_speed_kmh REAL NOT NULL,
                    exit_speed_kmh REAL NOT NULL,
                    entry_delta_ms REAL NOT NULL,
                    rotation_delta_ms REAL NOT NULL,
                    exit_delta_ms REAL NOT NULL,
                    entry_slip_ratio REAL NOT NULL,
                    exit_slip_ratio REAL NOT NULL,
                    slip_band TEXT NOT NULL,
                    candidate_type TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    intensity TEXT NOT NULL,
                    assists_config TEXT NOT NULL,
                    device_config TEXT NOT NULL,
                    feature_vector TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    INDEX(corner_id),
                    INDEX(candidate_type),
                    INDEX(created_at)
                )
            """)
            
            # Utility evaluations table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS utility_evaluations (
                    evaluation_id TEXT PRIMARY KEY,
                    action_id TEXT NOT NULL,
                    feature_id TEXT NOT NULL,
                    realized_gain_ms REAL NOT NULL,
                    evaluation_confidence TEXT NOT NULL,
                    evaluation_source TEXT NOT NULL,
                    follow_up_laps INTEGER NOT NULL,
                    track_conditions TEXT NOT NULL,
                    driver_consistency REAL NOT NULL,
                    is_valid_evaluation BOOLEAN NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (feature_id) REFERENCES utility_features (feature_id),
                    INDEX(action_id),
                    INDEX(feature_id),
                    INDEX(is_valid_evaluation),
                    INDEX(created_at)
                )
            """)
            
            # Utility predictions table (for tracking ML predictions)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS utility_predictions (
                    prediction_id TEXT PRIMARY KEY,
                    feature_id TEXT NOT NULL,
                    expected_gain_ms REAL NOT NULL,
                    confidence_interval_ms REAL NOT NULL,
                    confidence_level TEXT NOT NULL,
                    source TEXT NOT NULL,
                    model_version TEXT,
                    predicted_at TEXT NOT NULL,
                    FOREIGN KEY (feature_id) REFERENCES utility_features (feature_id),
                    INDEX(feature_id),
                    INDEX(source),
                    INDEX(predicted_at)
                )
            """)
            
            # Model training history table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS utility_model_history (
                    training_id TEXT PRIMARY KEY,
                    model_type TEXT NOT NULL,
                    training_samples INTEGER NOT NULL,
                    training_score REAL NOT NULL,
                    feature_count INTEGER NOT NULL,
                    hyperparameters TEXT,
                    validation_score REAL,
                    training_duration_seconds REAL,
                    trained_at TEXT NOT NULL,
                    INDEX(trained_at),
                    INDEX(model_type)
                )
            """)
            
            await db.commit()
    
    async def save_utility_features(self, features: UtilityFeatures) -> str:
        """
        Save utility features to database.
        
        Args:
            features: Utility features to save
            
        Returns:
            Feature ID
        """
        await self._ensure_tables_exist()
        
        feature_id = f"feat_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        feature_vector_json = json.dumps(features.to_feature_vector())
        
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("""
                INSERT INTO utility_features (
                    feature_id, corner_id, corner_type, entry_speed_kmh, min_speed_kmh,
                    exit_speed_kmh, entry_delta_ms, rotation_delta_ms, exit_delta_ms,
                    entry_slip_ratio, exit_slip_ratio, slip_band, candidate_type,
                    phase, intensity, assists_config, device_config, feature_vector, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feature_id, features.corner_id, features.corner_type,
                features.entry_speed_kmh, features.min_speed_kmh, features.exit_speed_kmh,
                features.entry_delta_ms, features.rotation_delta_ms, features.exit_delta_ms,
                features.entry_slip_ratio, features.exit_slip_ratio, features.slip_band,
                features.candidate_type, features.phase, features.intensity,
                features.assists_config, features.device_config, feature_vector_json,
                datetime.utcnow().isoformat()
            ))
            await db.commit()
        
        return feature_id
    
    async def save_utility_evaluation(self, evaluation: UtilityEvaluation, feature_id: str) -> str:
        """
        Save utility evaluation to database.
        
        Args:
            evaluation: Utility evaluation to save
            feature_id: Associated feature ID
            
        Returns:
            Evaluation ID
        """
        await self._ensure_tables_exist()
        
        evaluation_id = f"eval_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("""
                INSERT INTO utility_evaluations (
                    evaluation_id, action_id, feature_id, realized_gain_ms,
                    evaluation_confidence, evaluation_source, follow_up_laps,
                    track_conditions, driver_consistency, is_valid_evaluation, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evaluation_id, evaluation.action_id, feature_id, evaluation.realized_gain_ms,
                evaluation.evaluation_confidence.value, evaluation.evaluation_source,
                evaluation.follow_up_laps, evaluation.track_conditions,
                evaluation.driver_consistency, evaluation.is_valid_evaluation(),
                datetime.utcnow().isoformat()
            ))
            await db.commit()
        
        return evaluation_id
    
    async def save_utility_prediction(self, prediction: ActionUtility, feature_id: str, model_version: Optional[str] = None) -> str:
        """
        Save utility prediction to database.
        
        Args:
            prediction: Utility prediction to save
            feature_id: Associated feature ID
            model_version: Version of model used
            
        Returns:
            Prediction ID
        """
        await self._ensure_tables_exist()
        
        prediction_id = f"pred_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("""
                INSERT INTO utility_predictions (
                    prediction_id, feature_id, expected_gain_ms, confidence_interval_ms,
                    confidence_level, source, model_version, predicted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction_id, feature_id, prediction.expected_gain_ms,
                prediction.confidence_interval_ms, prediction.confidence_level.value,
                prediction.source, model_version, datetime.utcnow().isoformat()
            ))
            await db.commit()
        
        return prediction_id
    
    async def get_training_data(self, limit: Optional[int] = None) -> List[tuple]:
        """
        Get feature-evaluation pairs for model training.
        
        Args:
            limit: Maximum number of samples to return
            
        Returns:
            List of (features, evaluation) tuples
        """
        await self._ensure_tables_exist()
        
        query = """
            SELECT f.feature_vector, e.realized_gain_ms
            FROM utility_features f
            JOIN utility_evaluations e ON f.feature_id = e.feature_id
            WHERE e.is_valid_evaluation = 1
            ORDER BY e.created_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        async with aiosqlite.connect(self._database_path) as db:
            cursor = await db.execute(query)
            rows = await cursor.fetchall()
        
        training_data = []
        for row in rows:
            feature_vector = json.loads(row[0])
            realized_gain = row[1]
            training_data.append((feature_vector, realized_gain))
        
        return training_data
    
    async def save_model_training_history(self, training_info: Dict[str, Any]) -> str:
        """
        Save model training history.
        
        Args:
            training_info: Training information dictionary
            
        Returns:
            Training ID
        """
        await self._ensure_tables_exist()
        
        training_id = f"train_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        hyperparams_json = json.dumps(training_info.get('hyperparameters', {}))
        
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("""
                INSERT INTO utility_model_history (
                    training_id, model_type, training_samples, training_score,
                    feature_count, hyperparameters, validation_score,
                    training_duration_seconds, trained_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                training_id, training_info.get('model_type', 'unknown'),
                training_info.get('training_samples', 0), training_info.get('training_score', 0.0),
                training_info.get('feature_count', 0), hyperparams_json,
                training_info.get('validation_score'), training_info.get('training_duration_seconds'),
                datetime.utcnow().isoformat()
            ))
            await db.commit()
        
        return training_id
    
    async def get_model_performance_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get model performance history.
        
        Args:
            limit: Number of recent training sessions to return
            
        Returns:
            List of training history records
        """
        await self._ensure_tables_exist()
        
        async with aiosqlite.connect(self._database_path) as db:
            cursor = await db.execute("""
                SELECT training_id, model_type, training_samples, training_score,
                       feature_count, hyperparameters, validation_score,
                       training_duration_seconds, trained_at
                FROM utility_model_history
                ORDER BY trained_at DESC
                LIMIT ?
            """, (limit,))
            rows = await cursor.fetchall()
        
        history = []
        for row in rows:
            history.append({
                'training_id': row[0],
                'model_type': row[1],
                'training_samples': row[2],
                'training_score': row[3],
                'feature_count': row[4],
                'hyperparameters': json.loads(row[5]) if row[5] else {},
                'validation_score': row[6],
                'training_duration_seconds': row[7],
                'trained_at': row[8]
            })
        
        return history
    
    async def get_prediction_accuracy_stats(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Get prediction accuracy statistics.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Accuracy statistics dictionary
        """
        await self._ensure_tables_exist()
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        
        async with aiosqlite.connect(self._database_path) as db:
            # Get predictions with evaluations
            cursor = await db.execute("""
                SELECT p.expected_gain_ms, e.realized_gain_ms, p.source, p.confidence_level
                FROM utility_predictions p
                JOIN utility_evaluations e ON p.feature_id = e.feature_id
                WHERE p.predicted_at >= ? AND e.is_valid_evaluation = 1
            """, (cutoff_date,))
            rows = await cursor.fetchall()
        
        if not rows:
            return {"total_predictions": 0, "accuracy_stats": {}}
        
        predictions = [(row[0], row[1], row[2], row[3]) for row in rows]
        
        # Calculate accuracy metrics
        errors = [abs(predicted - actual) for predicted, actual, _, _ in predictions]
        ml_errors = [abs(predicted - actual) for predicted, actual, source, _ in predictions if source == "ml"]
        heuristic_errors = [abs(predicted - actual) for predicted, actual, source, _ in predictions if source == "heuristic"]
        
        stats = {
            "total_predictions": len(predictions),
            "mean_absolute_error": sum(errors) / len(errors) if errors else 0,
            "median_absolute_error": sorted(errors)[len(errors)//2] if errors else 0,
            "ml_predictions": len(ml_errors),
            "ml_mean_error": sum(ml_errors) / len(ml_errors) if ml_errors else 0,
            "heuristic_predictions": len(heuristic_errors),
            "heuristic_mean_error": sum(heuristic_errors) / len(heuristic_errors) if heuristic_errors else 0
        }
        
        return {"total_predictions": len(predictions), "accuracy_stats": stats}
    
    async def get_utility_repository_stats(self) -> Dict[str, Any]:
        """Get repository statistics."""
        await self._ensure_tables_exist()
        
        async with aiosqlite.connect(self._database_path) as db:
            # Count records in each table
            features_count = await db.execute("SELECT COUNT(*) FROM utility_features")
            features_count = (await features_count.fetchone())[0]
            
            evaluations_count = await db.execute("SELECT COUNT(*) FROM utility_evaluations")
            evaluations_count = (await evaluations_count.fetchone())[0]
            
            predictions_count = await db.execute("SELECT COUNT(*) FROM utility_predictions")
            predictions_count = (await predictions_count.fetchone())[0]
            
            training_count = await db.execute("SELECT COUNT(*) FROM utility_model_history")
            training_count = (await training_count.fetchone())[0]
            
            # Valid evaluations count
            valid_evaluations = await db.execute("SELECT COUNT(*) FROM utility_evaluations WHERE is_valid_evaluation = 1")
            valid_evaluations = (await valid_evaluations.fetchone())[0]
        
        return {
            "features_stored": features_count,
            "evaluations_stored": evaluations_count,
            "valid_evaluations": valid_evaluations,
            "predictions_stored": predictions_count,
            "training_sessions": training_count,
            "database_path": self._database_path
        }
"""SQLite implementation of the CoachingRepository interface."""
import sqlite3
import aiosqlite
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from ...domain.entities.corner_analysis import (
    SelectedAction, ActionResult, ActionType, ActionIntensity
)
from ...domain.interfaces.coaching_repository import CoachingRepository
from ...domain.value_objects.slip_indicators import TurnPhase, AmpelColor


class SQLiteCoachingRepository(CoachingRepository):
    """SQLite adapter implementing the CoachingRepository port."""
    
    def __init__(self, database_path: Optional[str] = None):
        if database_path is None:
            # Auto-detect database location - prioritize project root
            import os
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(script_dir, "..", "..", "..")
            possible_paths = [
                os.path.join(project_root, "f1_lap_bot.db"),  # Project root (server location)
                os.path.join(project_root, "data", "f1_lap_bot.db"),  # data folder (local dev)
            ]
            
            # Use the first path that exists, or default to project root
            for path in possible_paths:
                if os.path.exists(path):
                    self._database_path = path
                    break
            else:
                # Default to project root if none exist yet
                self._database_path = possible_paths[0]
        else:
            self._database_path = database_path
    
    async def _ensure_tables_exist(self):
        """Create the coaching tables if they don't exist."""
        async with aiosqlite.connect(self._database_path) as db:
            # Coaching actions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS coaching_actions (
                    action_id TEXT PRIMARY KEY,
                    corner_id INTEGER NOT NULL,
                    phase TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    intensity TEXT NOT NULL,
                    expected_gain_ms REAL NOT NULL,
                    confidence REAL NOT NULL,
                    safety_ampel_color TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    user_text TEXT NOT NULL,
                    focus_hint TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Action results table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS coaching_action_results (
                    result_id TEXT PRIMARY KEY,
                    action_id TEXT NOT NULL,
                    corner_id INTEGER NOT NULL,
                    attempt_detected BOOLEAN NOT NULL,
                    success BOOLEAN NOT NULL,
                    overtrained BOOLEAN NOT NULL,
                    actual_gain_ms REAL,
                    slip_violations_json TEXT,
                    evaluation_laps INTEGER NOT NULL,
                    evaluation_completed_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (action_id) REFERENCES coaching_actions (action_id)
                )
            """)
            
            # Create indexes for better query performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_coaching_corner ON coaching_actions(corner_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_coaching_generated ON coaching_actions(generated_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_coaching_type ON coaching_actions(action_type, phase)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_results_action ON coaching_action_results(action_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_results_completed ON coaching_action_results(evaluation_completed_at)")
            
            await db.commit()
    
    async def save_action(self, action: SelectedAction) -> str:
        """Save a coaching action and return the generated ID."""
        await self._ensure_tables_exist()
        
        action_id = str(uuid.uuid4())
        
        try:
            async with aiosqlite.connect(self._database_path) as db:
                await db.execute("""
                    INSERT INTO coaching_actions (
                        action_id, corner_id, phase, action_type, intensity,
                        expected_gain_ms, confidence, safety_ampel_color,
                        generated_at, user_text, focus_hint, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    action_id,
                    action.corner_id,
                    action.phase.value,
                    action.action_type.value,
                    action.intensity.value,
                    action.expected_gain_ms,
                    action.confidence,
                    action.safety_ampel_color.value,
                    action.generated_at.isoformat(),
                    action.user_text,
                    action.focus_hint,
                    datetime.now().isoformat()
                ))
                
                await db.commit()
                
        except Exception as save_error:
            print(f"❌ COACHING REPOSITORY: Save action error: {save_error}")
            raise
        
        return action_id
    
    async def save_action_result(self, result: ActionResult) -> str:
        """Save an action result and return the generated ID."""
        await self._ensure_tables_exist()
        
        result_id = str(uuid.uuid4())
        
        try:
            async with aiosqlite.connect(self._database_path) as db:
                await db.execute("""
                    INSERT INTO coaching_action_results (
                        result_id, action_id, corner_id, attempt_detected,
                        success, overtrained, actual_gain_ms, slip_violations_json,
                        evaluation_laps, evaluation_completed_at, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result_id,
                    result.action_id,
                    result.corner_id,
                    result.attempt_detected,
                    result.success,
                    result.overtrained,
                    result.actual_gain_ms,
                    json.dumps(result.slip_violations),
                    result.evaluation_laps,
                    result.evaluation_completed_at.isoformat(),
                    datetime.now().isoformat()
                ))
                
                await db.commit()
                
        except Exception as save_error:
            print(f"❌ COACHING REPOSITORY: Save result error: {save_error}")
            raise
        
        return result_id
    
    async def find_action_by_id(self, action_id: str) -> Optional[SelectedAction]:
        """Find a coaching action by its ID."""
        await self._ensure_tables_exist()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM coaching_actions WHERE action_id = ?
            """, (action_id,))
            row = await cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_selected_action(row)
    
    async def find_result_by_action_id(self, action_id: str) -> Optional[ActionResult]:
        """Find an action result by the action ID."""
        await self._ensure_tables_exist()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM coaching_action_results WHERE action_id = ?
            """, (action_id,))
            row = await cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_action_result(row)
    
    async def find_recent_actions_by_corner(
        self, 
        corner_id: int, 
        days_back: int = 7,
        limit: int = 10
    ) -> List[SelectedAction]:
        """Find recent coaching actions for a specific corner."""
        await self._ensure_tables_exist()
        
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM coaching_actions 
                WHERE corner_id = ? AND generated_at >= ?
                ORDER BY generated_at DESC
                LIMIT ?
            """, (corner_id, cutoff_date, limit))
            rows = await cursor.fetchall()
            
            return [self._row_to_selected_action(row) for row in rows]
    
    async def get_action_success_rate(
        self,
        action_type: str,
        phase: str,
        days_back: int = 30
    ) -> Dict[str, float]:
        """Get success rate statistics for a specific action type and phase."""
        await self._ensure_tables_exist()
        
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        async with aiosqlite.connect(self._database_path) as db:
            # Total actions of this type
            cursor = await db.execute("""
                SELECT COUNT(*) FROM coaching_actions a
                LEFT JOIN coaching_action_results r ON a.action_id = r.action_id
                WHERE a.action_type = ? AND a.phase = ? AND a.generated_at >= ?
                AND r.result_id IS NOT NULL
            """, (action_type, phase, cutoff_date))
            total_evaluated = (await cursor.fetchone())[0]
            
            if total_evaluated == 0:
                return {
                    'total_evaluated': 0,
                    'attempt_rate': 0.0,
                    'success_rate': 0.0,
                    'overtrain_rate': 0.0
                }
            
            # Successful attempts
            cursor = await db.execute("""
                SELECT COUNT(*) FROM coaching_actions a
                JOIN coaching_action_results r ON a.action_id = r.action_id
                WHERE a.action_type = ? AND a.phase = ? AND a.generated_at >= ?
                AND r.attempt_detected = 1
            """, (action_type, phase, cutoff_date))
            attempts = (await cursor.fetchone())[0]
            
            # Successful outcomes
            cursor = await db.execute("""
                SELECT COUNT(*) FROM coaching_actions a
                JOIN coaching_action_results r ON a.action_id = r.action_id
                WHERE a.action_type = ? AND a.phase = ? AND a.generated_at >= ?
                AND r.success = 1
            """, (action_type, phase, cutoff_date))
            successes = (await cursor.fetchone())[0]
            
            # Overtraining
            cursor = await db.execute("""
                SELECT COUNT(*) FROM coaching_actions a
                JOIN coaching_action_results r ON a.action_id = r.action_id
                WHERE a.action_type = ? AND a.phase = ? AND a.generated_at >= ?
                AND r.overtrained = 1
            """, (action_type, phase, cutoff_date))
            overtrains = (await cursor.fetchone())[0]
            
            return {
                'total_evaluated': total_evaluated,
                'attempt_rate': attempts / total_evaluated,
                'success_rate': successes / total_evaluated,
                'overtrain_rate': overtrains / total_evaluated
            }
    
    async def find_pending_evaluations(self, max_age_hours: int = 24) -> List[SelectedAction]:
        """Find coaching actions that need evaluation (no result yet)."""
        await self._ensure_tables_exist()
        
        cutoff_date = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()
        
        async with aiosqlite.connect(self._database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT a.* FROM coaching_actions a
                LEFT JOIN coaching_action_results r ON a.action_id = r.action_id
                WHERE r.result_id IS NULL AND a.generated_at >= ?
                ORDER BY a.generated_at ASC
            """, (cutoff_date,))
            rows = await cursor.fetchall()
            
            return [self._row_to_selected_action(row) for row in rows]
    
    async def get_coaching_statistics(self) -> Dict[str, any]:
        """Get overall coaching statistics."""
        await self._ensure_tables_exist()
        
        async with aiosqlite.connect(self._database_path) as db:
            # Total actions
            cursor = await db.execute("SELECT COUNT(*) FROM coaching_actions")
            total_actions = (await cursor.fetchone())[0]
            
            # Total results
            cursor = await db.execute("SELECT COUNT(*) FROM coaching_action_results")
            total_results = (await cursor.fetchone())[0]
            
            # Success rate
            cursor = await db.execute("""
                SELECT COUNT(*) FROM coaching_action_results WHERE success = 1
            """)
            successes = (await cursor.fetchone())[0]
            
            # Attempt rate
            cursor = await db.execute("""
                SELECT COUNT(*) FROM coaching_action_results WHERE attempt_detected = 1
            """)
            attempts = (await cursor.fetchone())[0]
            
            # Average expected vs actual gains
            cursor = await db.execute("""
                SELECT AVG(a.expected_gain_ms), AVG(r.actual_gain_ms)
                FROM coaching_actions a
                JOIN coaching_action_results r ON a.action_id = r.action_id
                WHERE r.actual_gain_ms IS NOT NULL
            """)
            gain_stats = await cursor.fetchone()
            
            return {
                'total_actions': total_actions,
                'total_evaluations': total_results,
                'evaluation_rate': total_results / total_actions if total_actions > 0 else 0,
                'attempt_rate': attempts / total_results if total_results > 0 else 0,
                'success_rate': successes / total_results if total_results > 0 else 0,
                'avg_expected_gain_ms': gain_stats[0] or 0,
                'avg_actual_gain_ms': gain_stats[1] or 0,
                'pending_evaluations': total_actions - total_results
            }
    
    def _row_to_selected_action(self, row: aiosqlite.Row) -> SelectedAction:
        """Convert a database row to a SelectedAction entity."""
        try:
            return SelectedAction(
                corner_id=row['corner_id'],
                phase=TurnPhase(row['phase']),
                action_type=ActionType(row['action_type']),
                intensity=ActionIntensity(row['intensity']),
                expected_gain_ms=row['expected_gain_ms'],
                confidence=row['confidence'],
                safety_ampel_color=AmpelColor(row['safety_ampel_color']),
                generated_at=datetime.fromisoformat(row['generated_at']),
                user_text=row['user_text'],
                focus_hint=row['focus_hint']
            )
        except (KeyError, ValueError) as e:
            action_id = row['action_id'] if 'action_id' in row.keys() else "Unknown"
            print(f"Error converting row to SelectedAction for action_id={action_id}: {e}")
            raise ValueError(f"Corrupt coaching action data for action_id={action_id}") from e
    
    def _row_to_action_result(self, row: aiosqlite.Row) -> ActionResult:
        """Convert a database row to an ActionResult entity."""
        try:
            return ActionResult(
                action_id=row['action_id'],
                corner_id=row['corner_id'],
                attempt_detected=bool(row['attempt_detected']),
                success=bool(row['success']),
                overtrained=bool(row['overtrained']),
                actual_gain_ms=row['actual_gain_ms'],
                slip_violations=json.loads(row['slip_violations_json']),
                evaluation_laps=row['evaluation_laps'],
                evaluation_completed_at=datetime.fromisoformat(row['evaluation_completed_at'])
            )
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            result_id = row['result_id'] if 'result_id' in row.keys() else "Unknown"
            print(f"Error converting row to ActionResult for result_id={result_id}: {e}")
            raise ValueError(f"Corrupt action result data for result_id={result_id}") from e
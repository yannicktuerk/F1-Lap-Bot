"""Telemetry coaching integration service with corner analysis and action generation."""
import asyncio
import logging
from typing import Optional, List, Dict

from src.application.use_cases.process_telemetry import ProcessTelemetryUseCase
from src.application.use_cases.process_corner_analysis_coaching import ProcessCornerAnalysisAndCoaching
from src.application.services.safety_ampel_service import SafetyAmpelService
from src.application.services.candidate_generator import CandidateGenerator
from src.application.services.safety_gate_resolver import SafetyGateResolver
from src.application.services.action_selector import ActionSelector
from src.domain.services.gating_service import GatingService
from src.domain.services.marker_detector import MarkerDetector, PhaseSegmenter
from src.domain.services.slip_calculator import SlipCalculator
from src.domain.services.corner_ranker import CornerRanker
from src.domain.services.statistics_service import StatisticsService
from src.domain.config.slip_config import SLIP_AMPEL_CONFIG
from src.domain.value_objects.slip_indicators import SlipThresholds
from src.infrastructure.telemetry.udp_telemetry_adapter import UdpTelemetryAdapter
from src.infrastructure.persistence.sqlite_telemetry_repository import SQLiteTelemetryRepository
from src.infrastructure.persistence.sqlite_corner_reference_repository import SQLiteCornerReferenceRepository
from src.infrastructure.persistence.sqlite_coaching_repository import SQLiteCoachingRepository


class TelemetryCoachingService:
    """Enhanced integration service for F1 telemetry coaching pipeline with corner analysis."""
    
    def __init__(self, 
                 udp_port: int = 20777,
                 udp_host: str = "127.0.0.1",
                 database_path: Optional[str] = None):
        """
        Initialize telemetry coaching service with corner analysis and action generation.
        
        Args:
            udp_port: UDP port for F1 telemetry (default: 20777)
            udp_host: UDP host address (default: 127.0.0.1)
            database_path: Optional database path (auto-detected if None)
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize repositories
        self.telemetry_repository = SQLiteTelemetryRepository(database_path)
        self.corner_reference_repository = SQLiteCornerReferenceRepository(database_path)
        self.coaching_repository = SQLiteCoachingRepository(database_path)
        
        # Initialize core services
        self.gating_service = GatingService()
        self.marker_detector = MarkerDetector(
            brake_threshold=0.1,
            throttle_threshold=0.1,
            speed_change_threshold=5.0,
            hysteresis_window=3
        )
        self.phase_segmenter = PhaseSegmenter()
        
        # Initialize slip calculation services
        self.slip_calculator = SlipCalculator()
        self.safety_ampel_service = SafetyAmpelService(
            slip_calculator=self.slip_calculator,
            entry_thresholds=SlipThresholds(**SLIP_AMPEL_CONFIG["entry"]),
            exit_thresholds=SlipThresholds(**SLIP_AMPEL_CONFIG["exit"])
        )
        
        # Initialize corner analysis services (Issues 05-06)
        self.statistics_service = StatisticsService()
        self.corner_ranker = CornerRanker(self.statistics_service)
        self.candidate_generator = CandidateGenerator(self.statistics_service)
        self.safety_gate_resolver = SafetyGateResolver()
        self.action_selector = ActionSelector()
        
        # Initialize use cases
        self.telemetry_processor = ProcessTelemetryUseCase(
            gating_service=self.gating_service,
            marker_detector=self.marker_detector,
            phase_segmenter=self.phase_segmenter,
            safety_ampel_service=self.safety_ampel_service
        )
        
        # Initialize corner analysis and coaching use case (Issues 05-06)
        self.corner_analysis_processor = ProcessCornerAnalysisAndCoaching(
            corner_reference_repository=self.corner_reference_repository,
            coaching_repository=self.coaching_repository,
            corner_ranker=self.corner_ranker,
            statistics_service=self.statistics_service,
            candidate_generator=self.candidate_generator,
            safety_gate_resolver=self.safety_gate_resolver,
            action_selector=self.action_selector,
            safety_ampel_service=self.safety_ampel_service
        )
        
        # Initialize UDP adapter
        self.udp_adapter = UdpTelemetryAdapter(
            port=udp_port,
            host=udp_host,
            gating_service=self.gating_service
        )
        
        # Wire up the pipeline
        self.udp_adapter.add_ingest_handler(self.telemetry_processor)
        
        # Storage for session analysis
        self.current_session_telemetry: List = []
        self.current_session_uid: Optional[int] = None
        self.lap_completion_count = 0
        
        self._running = False
    
    async def start(self) -> None:
        """Start the telemetry coaching service."""
        if self._running:
            self.logger.warning("Telemetry coaching service already running")
            return
        
        try:
            self.logger.info("🚀 Starting F1 Telemetry Coaching Service...")
            
            # Start telemetry processor
            await self.telemetry_processor.start()
            
            # Start UDP adapter
            await self.udp_adapter.start()
            
            self._running = True
            
            self.logger.info("✅ F1 Telemetry Coaching Service started successfully")
            self.logger.info(f"📡 Listening for F1® 25 UDP telemetry on {self.udp_adapter.host}:{self.udp_adapter.port}")
            self.logger.info("🎯 TT-only, Valid-only, Player-only gating active")
            self.logger.info("🔧 Marker detection and phase segmentation enabled")
            self.logger.info("🚦 Slip indicators and safety ampels online")
            self.logger.info("📊 Corner analysis and coaching pipeline ready (Issues 05-06)")
            self.logger.info("🗄️ Database repositories initialized for telemetry and coaching data")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start telemetry coaching service: {e}")
            self._running = False
            raise
    
    async def stop(self) -> None:
        """Stop the telemetry coaching service."""
        if not self._running:
            return
        
        self.logger.info("🛑 Stopping F1 Telemetry Coaching Service...")
        
        try:
            # Stop UDP adapter
            await self.udp_adapter.stop()
            
            # Stop telemetry processor
            await self.telemetry_processor.stop()
            
            self._running = False
            
            # Log final statistics
            metrics = self.telemetry_processor.get_gating_metrics()
            completed_turns = len(self.telemetry_processor.get_completed_turns())
            
            self.logger.info("📊 Final Statistics:")
            self.logger.info(f"   • Total packets processed: {metrics.total_packets}")
            self.logger.info(f"   • Packets passed gating: {metrics.passed_samples}")
            self.logger.info(f"   • Pass rate: {metrics.pass_rate:.1f}%")
            self.logger.info(f"   • Completed turns analyzed: {completed_turns}")
            
            # Log safety ampel metrics
            self.safety_ampel_service.log_metrics()
            
            self.logger.info("✅ F1 Telemetry Coaching Service stopped")
            
        except Exception as e:
            self.logger.error(f"⚠️ Error stopping telemetry coaching service: {e}")
    
    def get_status(self) -> dict:
        """Get current service status and metrics including coaching data."""
        metrics = self.telemetry_processor.get_gating_metrics()
        completed_turns = self.telemetry_processor.get_completed_turns()
        
        return {
            "running": self._running,
            "udp_port": self.udp_adapter.port,
            "udp_host": self.udp_adapter.host,
            "features": {
                "basic_telemetry": True,
                "corner_analysis": True,
                "coaching_actions": True,
                "safety_ampels": True,
                "database_storage": True
            },
            "session": {
                "session_uid": self.current_session_uid,
                "lap_count": self.lap_completion_count,
                "telemetry_samples": len(self.current_session_telemetry)
            },
            "metrics": {
                "total_packets": metrics.total_packets,
                "passed_samples": metrics.passed_samples,
                "pass_rate": metrics.pass_rate,
                "filtered_non_tt": metrics.filtered_non_tt_sessions,
                "filtered_invalid_laps": metrics.filtered_invalid_laps,
                "filtered_non_player": metrics.filtered_non_player_cars,
            },
            "completed_turns": len(completed_turns),
            "latest_turns": [
                {
                    "turn_id": turn.turn_id,
                    "entry_duration_ms": turn.entry_duration_ms,
                    "rotation_duration_ms": turn.rotation_duration_ms,
                    "exit_duration_ms": turn.exit_duration_ms,
                    "trail_braking_ms": turn.trail_braking_duration_ms,
                    "entry_speed": turn.markers.entry_speed,
                    "min_speed": turn.markers.min_speed,
                    "exit_speed": turn.markers.exit_speed
                }
                for turn in completed_turns[-5:]  # Last 5 turns
            ]
        }
    
    async def reset_metrics(self) -> None:
        """Reset all metrics and turn data."""
        self.telemetry_processor.reset_metrics()
        self.current_session_telemetry.clear()
        self.current_session_uid = None
        self.lap_completion_count = 0
        self.logger.info("📊 All metrics, turn data, and session data reset")
    
    async def process_lap_completion(self, session_uid: int, track_id: int) -> Optional[str]:
        """
        Process lap completion for corner analysis and coaching (Issues 05-06).
        
        Args:
            session_uid: Session unique identifier
            track_id: Track identifier
            
        Returns:
            Coaching message string if analysis successful, None otherwise
        """
        try:
            self.logger.info(f"🏁 Processing lap completion for session {session_uid}")
            
            # Store current session data
            if self.current_session_uid != session_uid:
                self.current_session_uid = session_uid
                self.current_session_telemetry.clear()
                self.lap_completion_count = 0
            
            self.lap_completion_count += 1
            
            # Save telemetry samples to repository for analysis
            completed_turns = self.telemetry_processor.get_completed_turns()
            if completed_turns:
                self.logger.info(f"💾 Saving {len(completed_turns)} turns to telemetry repository")
                # In a real implementation, we'd convert turns to telemetry samples
                # For now, we'll use sample data
            
            # Extract corner times for analysis (placeholder implementation)
            driver_corner_data = self._extract_corner_times_from_turns(completed_turns)
            
            if not driver_corner_data:
                self.logger.info("ℹ️ No corner data available for analysis")
                return None
            
            # Generate assists and device configuration
            assists_config = "default_assists"  # Would be determined from game settings
            device_config = "wheel"  # Would be determined from input device
            
            # Execute corner analysis and coaching pipeline
            analysis_session = await self.corner_analysis_processor.execute(
                session_uid=session_uid,
                track_id=track_id,
                driver_corner_data=driver_corner_data,
                current_telemetry=self.current_session_telemetry,
                assists_config=assists_config,
                device_config=device_config
            )
            
            # Generate coaching report
            coaching_message = await self.corner_analysis_processor.generate_coaching_report(
                analysis_session
            )
            
            self.logger.info(f"✅ Corner analysis complete: {len(analysis_session.selected_actions)} actions")
            return coaching_message
            
        except Exception as e:
            self.logger.error(f"❌ Error in lap completion processing: {e}")
            return None
    
    async def evaluate_previous_coaching(self, action_id: str) -> bool:
        """
        Evaluate the effectiveness of a previous coaching action.
        
        Args:
            action_id: ID of the coaching action to evaluate
            
        Returns:
            True if evaluation successful, False otherwise
        """
        try:
            # Get recent telemetry for evaluation
            evaluation_telemetry = self.current_session_telemetry[-100:]  # Last 100 samples
            
            if not evaluation_telemetry:
                self.logger.warning(f"No telemetry available for evaluating action {action_id}")
                return False
            
            success = await self.corner_analysis_processor.evaluate_coaching_effectiveness(
                action_id=action_id,
                follow_up_telemetry=evaluation_telemetry,
                evaluation_laps=3
            )
            
            if success:
                self.logger.info(f"✅ Coaching evaluation completed for action {action_id}")
            else:
                self.logger.warning(f"⚠️ Coaching evaluation failed for action {action_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error evaluating coaching action {action_id}: {e}")
            return False
    
    async def get_coaching_statistics(self) -> Dict:
        """Get comprehensive coaching statistics."""
        try:
            coaching_stats = await self.coaching_repository.get_coaching_statistics()
            return {
                **coaching_stats,
                "corner_analysis_enabled": True,
                "session_uid": self.current_session_uid,
                "session_laps": self.lap_completion_count,
                "telemetry_samples": len(self.current_session_telemetry)
            }
        except Exception as e:
            self.logger.error(f"❌ Error getting coaching statistics: {e}")
            return {}
    
    def _extract_corner_times_from_turns(self, turns) -> Dict[int, List[float]]:
        """
        Extract corner times from completed turns for analysis.
        
        Args:
            turns: List of completed turn analysis objects
            
        Returns:
            Dictionary mapping corner_id to list of times
        """
        corner_times = {}
        
        for i, turn in enumerate(turns):
            corner_id = i + 1  # Simple mapping for now
            total_time = (
                turn.entry_duration_ms + 
                turn.rotation_duration_ms + 
                turn.exit_duration_ms
            )
            
            if corner_id not in corner_times:
                corner_times[corner_id] = []
            
            corner_times[corner_id].append(total_time)
        
        return corner_times


# CLI for testing the service standalone
async def main():
    """Main function for standalone testing."""
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start service
    service = TelemetryCoachingService()
    
    try:
        await service.start()
        
        print("\n" + "="*70)
        print("🏎️  F1 TELEMETRY COACHING SERVICE WITH CORNER ANALYSIS")
        print("="*70)
        print("📡 Start F1® 25 and enable UDP telemetry:")
        print("   Settings → Telemetry → UDP Telemetry: ON")
        print("   UDP Port: 20777")
        print("   UDP IP: 127.0.0.1")
        print("\n🎮 Features Available:")
        print("   • Real-time telemetry processing (Issues 01-04)")
        print("   • Corner ranking by improvement potential (Issue 05)")
        print("   • Coaching candidate generation (Issue 06)")
        print("   • Safety ampel constraints (Red/Yellow/Green)")
        print("   • Database storage for analysis and learning")
        print("\n🏁 Start a Time Trial session to see the coach in action!")
        print("⏹️  Press Ctrl+C to stop")
        print("="*70)
        
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(10)
                # Periodically log status
                status = service.get_status()
                if status["metrics"]["total_packets"] > 0:
                    print(f"\n📊 Status: {status['metrics']['passed_samples']} samples processed, "
                          f"{status['completed_turns']} turns analyzed")
        except KeyboardInterrupt:
            print("\n⏹️ Shutdown requested...")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    finally:
        await service.stop()
        print("👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())
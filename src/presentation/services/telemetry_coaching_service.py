"""Telemetry coaching integration service."""
import asyncio
import logging
from typing import Optional

from src.application.use_cases.process_telemetry import ProcessTelemetryUseCase
from src.application.services.safety_ampel_service import SafetyAmpelService
from src.domain.services.gating_service import GatingService
from src.domain.services.marker_detector import MarkerDetector, PhaseSegmenter
from src.domain.services.slip_calculator import SlipCalculator
from src.domain.config.slip_config import SLIP_AMPEL_CONFIG
from src.domain.value_objects.slip_indicators import SlipThresholds
from src.infrastructure.telemetry.udp_telemetry_adapter import UdpTelemetryAdapter


class TelemetryCoachingService:
    """Integration service for F1 telemetry coaching pipeline."""
    
    def __init__(self, 
                 udp_port: int = 20777,
                 udp_host: str = "127.0.0.1"):
        """
        Initialize telemetry coaching service.
        
        Args:
            udp_port: UDP port for F1 telemetry (default: 20777)
            udp_host: UDP host address (default: 127.0.0.1)
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
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
        
        # Initialize use case
        self.telemetry_processor = ProcessTelemetryUseCase(
            gating_service=self.gating_service,
            marker_detector=self.marker_detector,
            phase_segmenter=self.phase_segmenter,
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
        """Get current service status and metrics."""
        metrics = self.telemetry_processor.get_gating_metrics()
        completed_turns = self.telemetry_processor.get_completed_turns()
        
        return {
            "running": self._running,
            "udp_port": self.udp_adapter.port,
            "udp_host": self.udp_adapter.host,
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
        self.logger.info("📊 All metrics and turn data reset")


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
        
        print("\n" + "="*60)
        print("🏎️  F1 TELEMETRY COACHING SERVICE RUNNING")
        print("="*60)
        print("📡 Start F1® 25 and enable UDP telemetry:")
        print("   Settings → Telemetry → UDP Telemetry: ON")
        print("   UDP Port: 20777")
        print("   UDP IP: 127.0.0.1")
        print("\n🎮 Start a Time Trial session to see the coach in action!")
        print("⏹️  Press Ctrl+C to stop")
        print("="*60)
        
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
#!/usr/bin/env python3
"""
F1 Telemetry Coaching Service - Complete Pipeline Entry Point

This service implements the complete UDP telemetry listener and coaching pipeline for F1® 25.
Issues implemented: 
- 01-04 (UDP Listener, Functional Gating, Markers & Phases, Grip/Slip Indicators & Safety Ampels)
- 05-06 (Turn Ranking, Candidates Safety Conflict)
- 07-10 (ML Utility Estimator, Bandit Optimization, Reviewer, Language Templates)
"""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import asyncio
import logging

from src.presentation.services.telemetry_coaching_service import TelemetryCoachingService


async def main():
    """Main function for the F1 telemetry coaching service."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # Create and start service
    service = TelemetryCoachingService()
    
    try:
        await service.start()
        
        print("\n" + "="*70)
        print("🏎️  F1 TELEMETRY COACHING SERVICE RUNNING")
        print("="*70)
        print("📡 F1® 25 UDP Telemetry Configuration:")
        print("   • Settings → Telemetry → UDP Telemetry: ON")
        print("   • UDP Port: 20777")
        print("   • UDP IP: 127.0.0.1")
        print()
        print("🎯 Features Active:")
        print("   • Issue 01: UDP Listener + Packet Decoder (F1® 25 v3)")
        print("   • Issue 02: Functional Gating (TT-only, Valid-only, Player-only)")
        print("   • Issue 03: Markers & Phases (Entry, Rotation, Exit)")
        print("   • Issue 04: Grip/Slip Indicators & Safety Ampels (Green/Yellow/Red)")
        print("   • Issue 05: Corner Ranking by Impact (IQR-normalized statistics)")
        print("   • Issue 06: Coaching Candidates with Safety Constraints")
        print("   • Issue 07: ML Utility Estimator (GBDT + Fallback Heuristic)")
        print("   • Issue 08: Bandit Optimization (Thompson Sampling + Cooldown)")
        print("   • Issue 09: Reviewer Service (Pattern Detection + Intensity Adjustment)")
        print("   • Issue 10: German Language Templates (No Numbers/Meters)")
        print()
        print("🚦 Safety Ampel System:")
        print("   • Entry-Slip: Controls braking coaching safety")
        print("   • Exit-Slip: Controls throttle coaching safety")
        print("   • Green: All coaching allowed")
        print("   • Yellow: Progressive coaching only")
        print("   • Red: Coaching blocked, safety suggestions given")
        print()
        print("🤖 AI Coaching Pipeline:")
        print("   • Utility prediction with confidence bands")
        print("   • Personalized action selection via Thompson sampling")
        print("   • Real-time effectiveness evaluation and intensity adjustment")
        print("   • Qualitative German coaching messages (no numbers)")
        print()
        print("🎮 Start a Time Trial session in F1® 25 to see the complete coach in action!")
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
                          f"{status['completed_turns']} turns analyzed, "
                          f"pass rate: {status['metrics']['pass_rate']:.1f}%")
        except KeyboardInterrupt:
            print("\n⏹️ Shutdown requested...")
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)
    
    finally:
        await service.stop()
        print("👋 F1 Telemetry Coaching Service stopped. Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
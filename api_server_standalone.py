#!/usr/bin/env python3
"""Standalone HTTP API Server für F1 Telemetrie-Tests."""
import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from presentation.api.telemetry_api import TelemetryAPI
from infrastructure.persistence.sqlite_lap_time_repository import SQLiteLapTimeRepository


async def main():
    """Start nur den HTTP API Server für Tests."""
    print("🚀 Starting standalone F1 Telemetry API Server...")
    
    # Create repository
    repository = SQLiteLapTimeRepository("test_lap_times.db")
    
    # Create API server (ohne Discord Bot)
    api_server = TelemetryAPI(
        lap_time_repository=repository,
        host="0.0.0.0",
        port=8080,
        discord_bot=None  # Kein Discord Bot für Tests
    )
    
    try:
        # Start API server
        await api_server.start()
        print("✅ API Server läuft auf http://localhost:8080")
        print("📡 Teste mit: curl -X GET http://localhost:8080/api/health")
        print("🛑 Stoppen mit Ctrl+C")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Shutdown requested...")
    finally:
        await api_server.stop()
        print("👋 API Server stopped.")


if __name__ == "__main__":
    asyncio.run(main())

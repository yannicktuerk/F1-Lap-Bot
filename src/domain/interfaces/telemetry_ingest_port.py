"""Telemetry ingest port interface."""
from abc import ABC, abstractmethod
from typing import Protocol

from src.domain.entities.telemetry_sample import (
    PlayerTelemetrySample,
    SessionInfo,
    LapInfo,
    CarTelemetryInfo,
    TimeTrialInfo
)


class TelemetryIngestPort(Protocol):
    """Port interface for telemetry ingestion."""
    
    async def on_session(self, session_info: SessionInfo) -> None:
        """Handle session information update."""
        ...
    
    async def on_lap_data(self, lap_info: LapInfo) -> None:
        """Handle lap data update."""
        ...
    
    async def on_car_telemetry(self, car_telemetry: CarTelemetryInfo) -> None:
        """Handle car telemetry update."""
        ...
    
    async def on_time_trial(self, time_trial_info: TimeTrialInfo) -> None:
        """Handle time trial specific information."""
        ...
    
    async def on_player_telemetry_sample(self, sample: PlayerTelemetrySample) -> None:
        """Handle complete player telemetry sample."""
        ...


class TelemetryIngestHandler(ABC):
    """Base class for telemetry ingest handlers."""
    
    @abstractmethod
    async def handle_telemetry_sample(self, sample: PlayerTelemetrySample) -> None:
        """Process a complete telemetry sample."""
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Start the telemetry handler."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the telemetry handler."""
        pass
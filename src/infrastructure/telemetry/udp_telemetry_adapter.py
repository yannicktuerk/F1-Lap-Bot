"""UDP telemetry adapter for F1® 25 v3."""
import asyncio
import logging
import socket
from datetime import datetime
from typing import Optional, Dict, Any, Callable, Awaitable
import struct

from f1.listener import PacketListener
from f1.packets import (
    resolve,
    PacketHeader,
    PacketSessionData,
    PacketLapData,
    PacketCarTelemetryData,
    PacketTimeTrialData,
    PacketParticipantsData
)

from src.domain.entities.telemetry_sample import (
    PlayerTelemetrySample,
    SessionInfo,
    LapInfo,
    CarTelemetryInfo,
    TimeTrialInfo
)
from src.domain.interfaces.telemetry_ingest_port import TelemetryIngestPort
from src.domain.services.gating_service import GatingService


class UdpTelemetryAdapter:
    """Infrastructure adapter for UDP telemetry ingestion."""
    
    # Packet IDs from F1® 25 v3 specification
    PACKET_ID_SESSION = 1
    PACKET_ID_LAP_DATA = 2
    PACKET_ID_EVENT = 3
    PACKET_ID_PARTICIPANTS = 4
    PACKET_ID_CAR_TELEMETRY = 6
    PACKET_ID_MOTION_EX = 13
    PACKET_ID_TIME_TRIAL = 14
    
    def __init__(
        self,
        port: int = 20777,
        host: str = "127.0.0.1",
        gating_service: Optional[GatingService] = None
    ):
        self.port = port
        self.host = host
        self.logger = logging.getLogger(__name__)
        self.gating_service = gating_service or GatingService()
        
        # State tracking
        self._current_session: Optional[SessionInfo] = None
        self._current_lap_data: Dict[int, LapInfo] = {}  # car_index -> LapInfo
        self._current_telemetry_data: Dict[int, CarTelemetryInfo] = {}  # car_index -> CarTelemetryInfo
        self._current_time_trial: Optional[TimeTrialInfo] = None
        self._player_car_index: Optional[int] = None
        
        # UDP listener
        self._listener: Optional[PacketListener] = None
        self._running = False
        
        # Handlers
        self._ingest_handlers: list[TelemetryIngestPort] = []
        
        # Jitter handling - soft windows for packet aggregation
        self._frame_window_size = 5  # Allow 5 frame tolerance for packet aggregation
        self._last_processed_frame = 0
        
    def add_ingest_handler(self, handler: TelemetryIngestPort) -> None:
        """Add a telemetry ingest handler."""
        self._ingest_handlers.append(handler)
        self.logger.info(f"Added ingest handler: {type(handler).__name__}")
    
    async def start(self) -> None:
        """Start the UDP telemetry listener."""
        if self._running:
            self.logger.warning("UDP telemetry adapter already running")
            return
        
        try:
            self.logger.info(f"Starting UDP telemetry listener on {self.host}:{self.port}")
            
            # Create and configure UDP listener
            self._listener = PacketListener(host=self.host, port=self.port)
            
            self._running = True
            
            # Start listening in background task
            asyncio.create_task(self._run_listener())
            
        except Exception as e:
            self.logger.error(f"Failed to start UDP telemetry adapter: {e}")
            self._running = False
            raise
    
    async def stop(self) -> None:
        """Stop the UDP telemetry listener."""
        if not self._running:
            return
        
        self.logger.info("Stopping UDP telemetry adapter")
        self._running = False
        
        if self._listener:
            self._listener.close()
            self._listener = None
        
        # Log final metrics
        self.gating_service.log_metrics()
    
    async def _run_listener(self) -> None:
        """Run the UDP listener in async mode."""
        try:
            self.logger.info("UDP listener started, waiting for packets...")
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            while self._running:
                try:
                    # Get packet from listener (this blocks, so run in executor)
                    packet = await loop.run_in_executor(None, self._listener.get)
                    
                    if packet:
                        await self._handle_packet(packet)
                        
                except Exception as e:
                    if self._running:  # Only log if we're still supposed to be running
                        self.logger.error(f"Error processing packet: {e}")
                    
        except Exception as e:
            self.logger.error(f"UDP listener error: {e}")
            self._running = False
    
    async def _handle_packet(self, packet) -> None:
        """Handle incoming packet based on its type."""
        try:
            packet_id = packet.header.packet_id
            
            if packet_id == self.PACKET_ID_SESSION:
                self._handle_session_packet(packet)
            elif packet_id == self.PACKET_ID_LAP_DATA:
                self._handle_lap_data_packet(packet)
            elif packet_id == self.PACKET_ID_CAR_TELEMETRY:
                self._handle_car_telemetry_packet(packet)
            elif packet_id == self.PACKET_ID_TIME_TRIAL:
                self._handle_time_trial_packet(packet)
            elif packet_id == self.PACKET_ID_PARTICIPANTS:
                self._handle_participants_packet(packet)
                
        except Exception as e:
            self.logger.error(f"Error handling packet type {packet_id if 'packet_id' in locals() else 'unknown'}: {e}")
    
    def _handle_session_packet(self, packet: PacketSessionData) -> None:
        """Handle session data packet (ID 1)."""
        try:
            header = packet.header
            self._player_car_index = header.player_car_index
            
            # Map session information
            session_info = SessionInfo(
                session_uid=header.session_uid,
                session_type=packet.session_type,
                track_id=packet.track_id,
                session_time=header.session_time,
                remaining_time=packet.session_time_left,
                is_time_trial=(packet.session_type == self.gating_service.SESSION_TYPE_TIME_TRIAL),
                frame_identifier=header.frame_identifier,
                overall_frame_identifier=header.overall_frame_identifier
            )
            
            # Apply gating rules
            if not self.gating_service.should_process_session(session_info, self._player_car_index):
                return
            
            self._current_session = session_info
            self.logger.debug(f"Session update: type={session_info.session_type}, track={session_info.track_id}")
            
            # Notify handlers
            asyncio.create_task(self._notify_handlers_session(session_info))
            
        except Exception as e:
            self.logger.error(f"Error handling session packet: {e}")
    
    def _handle_lap_data_packet(self, packet: PacketLapData) -> None:
        """Handle lap data packet (ID 2)."""
        try:
            if self._player_car_index is None:
                return
            
            # Get player car lap data
            lap_data = packet.lap_data[self._player_car_index]
            
            # Convert sector times (they are split into ms_part and minutes_part)
            sector1_ms = None
            if lap_data.sector1_time_ms_part > 0:
                sector1_ms = lap_data.sector1_time_ms_part + (lap_data.sector1_time_minutes_part * 60000)
            
            sector2_ms = None
            if lap_data.sector2_time_ms_part > 0:
                sector2_ms = lap_data.sector2_time_ms_part + (lap_data.sector2_time_minutes_part * 60000)
            
            lap_info = LapInfo(
                lap_time_ms=lap_data.last_lap_time_in_ms if lap_data.last_lap_time_in_ms > 0 else None,
                sector1_time_ms=sector1_ms,
                sector2_time_ms=sector2_ms,
                sector3_time_ms=None,  # Sector 3 is calculated as lap_time - sector1 - sector2
                lap_distance=lap_data.lap_distance,
                total_distance=lap_data.total_distance,
                is_valid_lap=(lap_data.result_status == 2 and lap_data.current_lap_invalid == 0),  # 2 = Active/Valid, 0 = valid lap
                current_lap_number=lap_data.current_lap_num,
                car_position=lap_data.car_position
            )
            
            # Calculate sector 3 time if we have lap time and other sectors
            if (lap_info.lap_time_ms and lap_info.sector1_time_ms and lap_info.sector2_time_ms):
                lap_info.sector3_time_ms = lap_info.lap_time_ms - lap_info.sector1_time_ms - lap_info.sector2_time_ms
            
            # Apply gating rules
            if not self.gating_service.should_process_lap(lap_info, self._player_car_index):
                return
            
            self._current_lap_data[self._player_car_index] = lap_info
            self.logger.debug(f"Lap update: lap={lap_info.current_lap_number}, valid={lap_info.is_valid_lap}")
            
            # Notify handlers
            asyncio.create_task(self._notify_handlers_lap_data(lap_info))
            
            # Try to create complete telemetry sample
            asyncio.create_task(self._try_create_telemetry_sample(packet.header))
            
        except Exception as e:
            self.logger.error(f"Error handling lap data packet: {e}")
    
    def _handle_car_telemetry_packet(self, packet: PacketCarTelemetryData) -> None:
        """Handle car telemetry packet (ID 6)."""
        try:
            if self._player_car_index is None:
                return
            
            # Get player car telemetry
            telemetry = packet.car_telemetry_data[self._player_car_index]
            
            car_telemetry = CarTelemetryInfo(
                speed=telemetry.speed,
                throttle=telemetry.throttle,
                steer=telemetry.steer,
                brake=telemetry.brake,
                clutch=telemetry.clutch,
                gear=telemetry.gear,
                engine_rpm=telemetry.engine_rpm,
                drs=(telemetry.drs == 1),
                rev_lights_percent=telemetry.rev_lights_percent,
                brake_temperature=[
                    telemetry.brakes_temperature[0],  # RL
                    telemetry.brakes_temperature[1],  # RR
                    telemetry.brakes_temperature[2],  # FL
                    telemetry.brakes_temperature[3]   # FR
                ],
                tyre_surface_temperature=[
                    telemetry.tyres_surface_temperature[0],  # RL
                    telemetry.tyres_surface_temperature[1],  # RR
                    telemetry.tyres_surface_temperature[2],  # FL
                    telemetry.tyres_surface_temperature[3]   # FR
                ],
                tyre_inner_temperature=[
                    telemetry.tyres_inner_temperature[0],  # RL
                    telemetry.tyres_inner_temperature[1],  # RR
                    telemetry.tyres_inner_temperature[2],  # FL
                    telemetry.tyres_inner_temperature[3]   # FR
                ],
                engine_temperature=telemetry.engine_temperature
            )
            
            self._current_telemetry_data[self._player_car_index] = car_telemetry
            
            # Notify handlers
            asyncio.create_task(self._notify_handlers_car_telemetry(car_telemetry))
            
            # Try to create complete telemetry sample
            asyncio.create_task(self._try_create_telemetry_sample(packet.header))
            
        except Exception as e:
            self.logger.error(f"Error handling car telemetry packet: {e}")
    
    def _handle_time_trial_packet(self, packet: PacketTimeTrialData) -> None:
        """Handle time trial packet (ID 14)."""
        try:
            # Time trial data has current session best, personal best, and rival data
            player_best = packet.player_session_best_data_set
            personal_best = packet.personal_best_data_set
            
            time_trial_info = TimeTrialInfo(
                is_personal_best=(personal_best.lap_time_in_ms > 0 and personal_best.valid == 1),
                is_best_overall=False,  # Would need to compare with other data
                sector1_personal_best_ms=personal_best.sector1_time_in_ms if personal_best.sector1_time_in_ms > 0 else None,
                sector2_personal_best_ms=personal_best.sector2_time_in_ms if personal_best.sector2_time_in_ms > 0 else None,
                sector3_personal_best_ms=personal_best.sector3_time_in_ms if personal_best.sector3_time_in_ms > 0 else None,
                sector1_best_overall_ms=player_best.sector1_time_in_ms if player_best.sector1_time_in_ms > 0 else None,
                sector2_best_overall_ms=player_best.sector2_time_in_ms if player_best.sector2_time_in_ms > 0 else None,
                sector3_best_overall_ms=player_best.sector3_time_in_ms if player_best.sector3_time_in_ms > 0 else None
            )
            
            self._current_time_trial = time_trial_info
            
            # Notify handlers
            asyncio.create_task(self._notify_handlers_time_trial(time_trial_info))
            
        except Exception as e:
            self.logger.error(f"Error handling time trial packet: {e}")
    
    def _handle_participants_packet(self, packet: PacketParticipantsData) -> None:
        """Handle participants packet (ID 4) - for player index mapping if needed."""
        try:
            # This packet can help verify player car index if needed
            # For now, we rely on header.m_playerCarIndex
            pass
        except Exception as e:
            self.logger.error(f"Error handling participants packet: {e}")
    
    async def _try_create_telemetry_sample(self, header: PacketHeader) -> None:
        """Try to create a complete telemetry sample if all data is available."""
        if (
            self._current_session is not None and
            self._player_car_index is not None and
            self._player_car_index in self._current_lap_data and
            self._player_car_index in self._current_telemetry_data
        ):
            # Handle jitter with frame window tolerance
            frame_diff = header.frame_identifier - self._last_processed_frame
            if frame_diff < self._frame_window_size and frame_diff >= 0:
                return  # Skip if within soft window
            
            sample = PlayerTelemetrySample(
                timestamp=datetime.now(),
                session_info=self._current_session,
                lap_info=self._current_lap_data[self._player_car_index],
                car_telemetry=self._current_telemetry_data[self._player_car_index],
                time_trial_info=self._current_time_trial,
                player_car_index=self._player_car_index
            )
            
            # Apply final gating check
            if self.gating_service.should_process_telemetry_sample(sample):
                self._last_processed_frame = header.frame_identifier
                await self._notify_handlers_telemetry_sample(sample)
    
    async def _notify_handlers_session(self, session_info: SessionInfo) -> None:
        """Notify all handlers of session update."""
        for handler in self._ingest_handlers:
            try:
                await handler.on_session(session_info)
            except Exception as e:
                self.logger.error(f"Error notifying handler {type(handler).__name__} of session: {e}")
    
    async def _notify_handlers_lap_data(self, lap_info: LapInfo) -> None:
        """Notify all handlers of lap data update."""
        for handler in self._ingest_handlers:
            try:
                await handler.on_lap_data(lap_info)
            except Exception as e:
                self.logger.error(f"Error notifying handler {type(handler).__name__} of lap data: {e}")
    
    async def _notify_handlers_car_telemetry(self, car_telemetry: CarTelemetryInfo) -> None:
        """Notify all handlers of car telemetry update."""
        for handler in self._ingest_handlers:
            try:
                await handler.on_car_telemetry(car_telemetry)
            except Exception as e:
                self.logger.error(f"Error notifying handler {type(handler).__name__} of car telemetry: {e}")
    
    async def _notify_handlers_time_trial(self, time_trial_info: TimeTrialInfo) -> None:
        """Notify all handlers of time trial update."""
        for handler in self._ingest_handlers:
            try:
                await handler.on_time_trial(time_trial_info)
            except Exception as e:
                self.logger.error(f"Error notifying handler {type(handler).__name__} of time trial: {e}")
    
    async def _notify_handlers_telemetry_sample(self, sample: PlayerTelemetrySample) -> None:
        """Notify all handlers of complete telemetry sample."""
        for handler in self._ingest_handlers:
            try:
                await handler.on_player_telemetry_sample(sample)
            except Exception as e:
                self.logger.error(f"Error notifying handler {type(handler).__name__} of telemetry sample: {e}")
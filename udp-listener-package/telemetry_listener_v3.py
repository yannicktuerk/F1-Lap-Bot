"""F1 2025 UDP Telemetry Listener with Full Telemetry Capture (v3.0).

This module extends the UDP listener to capture complete telemetry traces
for physics-based coaching analysis (Mathe-Coach). It captures:
- Lap times for leaderboards (existing functionality)
- Full telemetry traces (Position, Velocity, Inputs) for coaching

Features:
- Real-time F1 2025 UDP telemetry processing (Packet IDs 0, 1, 2, 6)
- Time Trial session detection with user_id tracking
- Complete LapTrace capture (300-500 samples per lap)
- Automatic submission to Discord bot API
- Personal best tracking for leaderboards

Author: F1 Lap Bot Team
Version: 3.0
License: MIT
"""

import socket
import json
import struct
import requests
from typing import Optional, Dict, List
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict

# Import f1-packets library for official F1 2025 packet parsing
try:
    from f1.packets import (
        PacketSessionData,
        PacketLapData,
        PacketMotionData,
        PacketCarTelemetryData,
        PacketEventData
    )
    F1_PACKETS_AVAILABLE = True
except ImportError:
    print("⚠️ f1-packets library not found. Install with: pip install f1-packets")
    F1_PACKETS_AVAILABLE = False

# Session Types
SESSION_TYPE_TIME_TRIAL = 18

# Track mapping (F1 2025 track IDs)
TRACK_MAPPING = {
    0: "melbourne", 2: "shanghai", 3: "bahrain", 4: "spain", 5: "monaco",
    6: "canada", 7: "silverstone", 9: "hungary", 10: "spa", 11: "monza",
    12: "singapore", 13: "japan", 14: "abu-dhabi", 15: "usa", 16: "brazil",
    17: "austria", 19: "mexico", 20: "baku", 26: "netherlands", 27: "imola",
    29: "jeddah", 30: "miami", 31: "las-vegas", 32: "qatar",
    39: "silverstone-reverse", 40: "austria-reverse", 41: "netherlands-reverse"
}


@dataclass
class TelemetrySampleData:
    """Single telemetry sample with all required fields for TelemetrySample value object."""
    timestamp_ms: int
    world_position_x: float
    world_position_y: float
    world_position_z: float
    world_velocity_x: float
    world_velocity_y: float
    world_velocity_z: float
    g_force_lateral: float
    g_force_longitudinal: float
    yaw: float
    speed: float
    throttle: float
    steer: float
    brake: float
    gear: int
    engine_rpm: int
    drs: int
    lap_distance: float
    lap_number: int


@dataclass
class SessionInfo:
    """Session information from F1 2025."""
    session_type: int
    track_id: int
    session_uid: str
    is_time_trial: bool = False
    track_name: str = "Unknown"


class LapTraceBuilder:
    """Builds a complete lap trace by collecting telemetry samples."""
    
    def __init__(self, session_uid: str, lap_number: int, car_index: int, track_id: str):
        self.session_uid = session_uid
        self.lap_number = lap_number
        self.car_index = car_index
        self.track_id = track_id
        self.samples: List[TelemetrySampleData] = []
        self.is_valid = True
        self.lap_time_ms: Optional[int] = None
        self.sector1_ms: Optional[int] = None
        self.sector2_ms: Optional[int] = None
        self.sector3_ms: Optional[int] = None
        self.ever_invalid = False  # Track if lap was ever marked invalid
        
    def add_sample(self, sample: TelemetrySampleData):
        """Add telemetry sample to this lap."""
        if sample.lap_number == self.lap_number:
            self.samples.append(sample)
    
    def mark_invalid(self):
        """Mark lap as invalid (corner cutting, penalties, etc.)."""
        self.is_valid = False
        self.ever_invalid = True
    
    def complete(self, lap_time_ms: int, sector1_ms: int, sector2_ms: int, sector3_ms: int):
        """Mark lap as complete with final time."""
        self.lap_time_ms = lap_time_ms
        self.sector1_ms = sector1_ms
        self.sector2_ms = sector2_ms
        self.sector3_ms = sector3_ms
    
    def is_complete(self) -> bool:
        """Check if lap is complete."""
        return self.lap_time_ms is not None
    
    def to_api_payload(self, user_id: str) -> dict:
        """Convert lap trace to API payload for bot submission."""
        return {
            "session_uid": self.session_uid,
            "track_id": self.track_id,
            "lap_number": self.lap_number,
            "car_index": self.car_index,
            "lap_time_ms": self.lap_time_ms,
            "is_valid": self.is_valid,
            "user_id": user_id,
            "sector_times": {
                "sector1_ms": self.sector1_ms,
                "sector2_ms": self.sector2_ms,
                "sector3_ms": self.sector3_ms
            },
            "telemetry_samples": [
                {
                    "timestamp_ms": s.timestamp_ms,
                    "world_position_x": s.world_position_x,
                    "world_position_y": s.world_position_y,
                    "world_position_z": s.world_position_z,
                    "world_velocity_x": s.world_velocity_x,
                    "world_velocity_y": s.world_velocity_y,
                    "world_velocity_z": s.world_velocity_z,
                    "g_force_lateral": s.g_force_lateral,
                    "g_force_longitudinal": s.g_force_longitudinal,
                    "yaw": s.yaw,
                    "speed": s.speed,
                    "throttle": s.throttle,
                    "steer": s.steer,
                    "brake": s.brake,
                    "gear": s.gear,
                    "engine_rpm": s.engine_rpm,
                    "drs": s.drs,
                    "lap_distance": s.lap_distance,
                    "lap_number": s.lap_number
                }
                for s in self.samples
            ]
        }


class F1TelemetryListenerV3:
    """F1 2025 UDP Telemetry Listener with full trace capture."""
    
    def __init__(self, port: int = 20777, bot_integration: bool = False,
                 discord_user_id: str = None, bot_api_url: str = None):
        if not F1_PACKETS_AVAILABLE:
            raise ImportError("f1-packets library is required. Install with: pip install f1-packets")
        
        self.port = port
        self.bot_integration = bot_integration
        self.discord_user_id = discord_user_id
        self.bot_api_url = bot_api_url or "http://localhost:8080"
        self.socket = None
        self.running = False
        
        # Session tracking
        self.session_info: Optional[SessionInfo] = None
        self.session_registered = False  # Track if we registered session with bot
        self.player_car_index = 0
        
        # Lap trace building
        self.current_lap_trace: Optional[LapTraceBuilder] = None
        self.completed_lap_traces: List[LapTraceBuilder] = []
        
        # Telemetry buffer (store latest data from each packet type)
        self.latest_motion_data = None  # From Packet ID 0
        self.latest_telemetry_data = None  # From Packet ID 6
        self.latest_lap_data = None  # From Packet ID 2
        
        # Personal bests for leaderboard submission
        self.personal_bests: Dict[str, int] = {}
        
        # Baseline tracking
        self.baseline_lap_established = False
        self.current_lap_number = 0
        self.current_lap_ever_invalid = False
        
        print("🏎️ F1 2025 Telemetry Listener v3.0 initialized")
        print("📡 Capturing: Lap Times + Full Telemetry Traces")
    
    def start(self):
        """Start the UDP listener."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('0.0.0.0', self.port))
            self.running = True
            
            print(f"\n🌐 Listening on port {self.port}")
            print("⏰ Started at:", datetime.now().strftime('%H:%M:%S'))
            print("🎯 Monitoring for Time Trial sessions...")
            print("📊 Will capture: Position, Velocity, Inputs, G-Forces\n")
            
            while self.running:
                try:
                    data, addr = self.socket.recvfrom(2048)
                    self.process_packet(data)
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"❌ Error receiving data: {e}")
        
        except Exception as e:
            print(f"❌ Failed to start listener: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the UDP listener."""
        self.running = False
        if self.socket:
            self.socket.close()
        print("🛑 Telemetry listener stopped")
    
    def process_packet(self, data: bytes):
        """Process incoming UDP packet."""
        try:
            if len(data) < 29:
                return
            
            # Parse header
            header = struct.unpack('<HBBBBBQffIBB', data[:29])
            (packet_format, game_year, game_major_version, game_minor_version,
             packet_version, packet_id, session_uid, session_time,
             frame_identifier, overall_frame_identifier,
             player_car_index, secondary_player_car_index) = header
            
            self.player_car_index = player_car_index
            
            # Parse packet based on ID
            buffer = bytearray(data)
            
            try:
                if packet_id == 1:  # Session data
                    packet = PacketSessionData.from_buffer(buffer)
                    self.process_session_data(packet, session_uid)
                
                elif packet_id == 0:  # Motion data
                    packet = PacketMotionData.from_buffer(buffer)
                    self.process_motion_data(packet)
                
                elif packet_id == 6:  # Car telemetry data
                    packet = PacketCarTelemetryData.from_buffer(buffer)
                    self.process_car_telemetry_data(packet)
                
                elif packet_id == 2:  # Lap data
                    packet = PacketLapData.from_buffer(buffer)
                    self.process_lap_data(packet, int(session_time * 1000))
            
            except Exception as e:
                # Suppress parse errors for unknown/unsupported packets
                pass
        
        except Exception as e:
            pass  # Suppress errors
    
    def process_session_data(self, packet: PacketSessionData, session_uid: int):
        """Process session data packet."""
        try:
            session_type = packet.session_type
            track_id = packet.track_id
            track_name = TRACK_MAPPING.get(track_id, f"track_{track_id}")
            is_time_trial = session_type == SESSION_TYPE_TIME_TRIAL
            
            # Convert session_uid to string to avoid SQLite INTEGER overflow
            session_uid_str = str(session_uid)
            
            # Detect new session
            if is_time_trial and (not self.session_info or 
                                 self.session_info.session_uid != session_uid_str):
                self.session_info = SessionInfo(
                    session_type=session_type,
                    track_id=track_id,
                    session_uid=session_uid_str,
                    is_time_trial=True,
                    track_name=track_name
                )
                self.session_registered = False
                self.baseline_lap_established = False
                self.current_lap_number = 0
                
                print(f"\n🏆 TIME TRIAL SESSION DETECTED")
                print(f"📍 Track: {track_name.title()} (ID: {track_id})")
                print(f"🆔 Session UID: {session_uid}")
                print("✅ Ready to capture telemetry!\n")
                
                # Register session with bot
                if self.bot_integration and self.discord_user_id:
                    self.register_session()
            
            elif not is_time_trial and self.session_info:
                print("🚫 Session changed - no longer Time Trial")
                self.session_info = None
                self.session_registered = False
        
        except Exception as e:
            print(f"❌ Error processing session data: {e}")
    
    def register_session(self):
        """Register new session with bot API."""
        if self.session_registered or not self.session_info:
            return
        
        try:
            response = requests.post(
                f"{self.bot_api_url}/api/telemetry/session/register",
                json={
                    "session_uid": self.session_info.session_uid,
                    "track_id": self.session_info.track_name,
                    "session_type": self.session_info.session_type,
                    "user_id": self.discord_user_id
                },
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"✅ Session registered with bot (UID: {self.session_info.session_uid})")
                self.session_registered = True
            else:
                print(f"⚠️ Failed to register session: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"⚠️ Could not register session: {e}")
            # Continue anyway - session registration is optional
    
    def process_motion_data(self, packet: PacketMotionData):
        """Store latest motion data (position, velocity, g-forces)."""
        if not self.session_info or not self.session_info.is_time_trial:
            return
        
        if self.player_car_index < len(packet.car_motion_data):
            self.latest_motion_data = packet.car_motion_data[self.player_car_index]
    
    def process_car_telemetry_data(self, packet: PacketCarTelemetryData):
        """Store latest car telemetry data (speed, throttle, brake, etc.)."""
        if not self.session_info or not self.session_info.is_time_trial:
            return
        
        if self.player_car_index < len(packet.car_telemetry_data):
            self.latest_telemetry_data = packet.car_telemetry_data[self.player_car_index]
    
    def process_lap_data(self, packet: PacketLapData, timestamp_ms: int):
        """Process lap data and create telemetry samples."""
        if not self.session_info or not self.session_info.is_time_trial:
            return
        
        if self.player_car_index >= len(packet.lap_data):
            return
        
        lap_data = packet.lap_data[self.player_car_index]
        
        # Extract lap information
        current_lap_num = getattr(lap_data, 'current_lap_num', 0)
        lap_time_ms = getattr(lap_data, 'last_lap_time_in_ms', 0)
        current_lap_invalid = getattr(lap_data, 'current_lap_invalid', False)
        penalties = getattr(lap_data, 'penalties', 0)
        lap_distance = getattr(lap_data, 'lap_distance', 0.0)
        
        # Store latest lap data
        self.latest_lap_data = lap_data
        
        # Establish baseline on first lap data (start tracking immediately)
        if not self.baseline_lap_established:
            print(f"🔄 Baseline established: Starting from Lap {current_lap_num}")
            self.baseline_lap_established = True
            self.current_lap_number = current_lap_num - 1  # Set to previous lap so next lap triggers new lap logic
        
        # Track lap number changes (new lap started)
        if current_lap_num != self.current_lap_number:
            # Complete previous lap if exists
            if self.current_lap_trace and self.current_lap_trace.lap_number == self.current_lap_number:
                if lap_time_ms > 0 and 30000 < lap_time_ms < 300000:
                    # Extract sector times
                    sector1_ms = self._extract_sector_time(lap_data, 1)
                    sector2_ms = self._extract_sector_time(lap_data, 2)
                    sector3_ms = lap_time_ms - sector1_ms - sector2_ms if sector1_ms > 0 and sector2_ms > 0 else 0
                    
                    # Complete the lap
                    self.current_lap_trace.complete(lap_time_ms, sector1_ms, sector2_ms, sector3_ms)
                    
                    # In Time Trial, trust the game's judgment
                    # If we got a lap time, the lap is valid unless there are penalties
                    # Note: In Time Trial mode, penalties are extremely rare
                    if penalties == 0:
                        print(f"\n✅ LAP {self.current_lap_number} COMPLETED")
                        print(f"   Time: {self._format_time(lap_time_ms)}")
                        print(f"   Samples: {len(self.current_lap_trace.samples)}")
                        print(f"   Valid: Yes")
                        
                        self.completed_lap_traces.append(self.current_lap_trace)
                        
                        # Submit to bot
                        self._submit_lap(self.current_lap_trace)
                    else:
                        print(f"\n❌ LAP {self.current_lap_number} INVALID (penalties={penalties})")
            
            # Start new lap
            print(f"\n🏁 Starting Lap {current_lap_num}")
            self.current_lap_number = current_lap_num
            self.current_lap_trace = LapTraceBuilder(
                session_uid=self.session_info.session_uid,
                lap_number=current_lap_num,
                car_index=self.player_car_index,
                track_id=self.session_info.track_name
            )
        
        # In Time Trial, we don't track invalid status during the lap
        # We only check for penalties at completion
        # Removed: invalid tracking during lap causes false positives
        
        # Create telemetry sample if all data is available
        if (self.current_lap_trace and self.latest_motion_data and 
            self.latest_telemetry_data and self.latest_lap_data):
            
            sample = self._create_telemetry_sample(timestamp_ms)
            if sample:
                self.current_lap_trace.add_sample(sample)
    
    def _create_telemetry_sample(self, timestamp_ms: int) -> Optional[TelemetrySampleData]:
        """Create telemetry sample from latest packet data."""
        try:
            motion = self.latest_motion_data
            telemetry = self.latest_telemetry_data
            lap = self.latest_lap_data
            
            return TelemetrySampleData(
                timestamp_ms=timestamp_ms,
                world_position_x=motion.world_position_x,
                world_position_y=motion.world_position_y,
                world_position_z=motion.world_position_z,
                world_velocity_x=motion.world_velocity_x,
                world_velocity_y=motion.world_velocity_y,
                world_velocity_z=motion.world_velocity_z,
                g_force_lateral=motion.g_force_lateral,
                g_force_longitudinal=motion.g_force_longitudinal,
                yaw=motion.yaw,
                speed=telemetry.speed,
                throttle=telemetry.throttle / 100.0,  # Convert percentage to 0-1
                steer=telemetry.steer / 100.0,  # Convert percentage to -1-1
                brake=telemetry.brake / 100.0,  # Convert percentage to 0-1
                gear=telemetry.gear,
                engine_rpm=telemetry.engine_rpm,
                drs=telemetry.drs,
                lap_distance=lap.lap_distance,
                lap_number=lap.current_lap_num
            )
        except Exception as e:
            return None
    
    def _extract_sector_time(self, lap_data, sector_num: int) -> int:
        """Extract sector time from lap data."""
        try:
            if sector_num == 1:
                ms = getattr(lap_data, 'sector1_time_ms_part', 0)
                min = getattr(lap_data, 'sector1_time_minutes_part', 0)
                return (min * 60000) + ms
            elif sector_num == 2:
                ms = getattr(lap_data, 'sector2_time_ms_part', 0)
                min = getattr(lap_data, 'sector2_time_minutes_part', 0)
                return (min * 60000) + ms
        except:
            return 0
        return 0
    
    def _submit_lap(self, lap_trace: LapTraceBuilder):
        """Submit completed lap to bot API."""
        if not self.bot_integration or not self.discord_user_id:
            print("💡 Bot integration disabled - lap not submitted")
            return
        
        track_name = self.session_info.track_name
        lap_time_ms = lap_trace.lap_time_ms
        
        # Track local PB for info (server decides official PB)
        current_pb = self.personal_bests.get(track_name)
        is_local_pb = current_pb is None or lap_time_ms < current_pb
        
        if is_local_pb:
            print(f"🆕 Local Personal Best! Submitting to bot...")
            self.personal_bests[track_name] = lap_time_ms
        else:
            print(f"⏱️ Valid lap time: {self._format_time(lap_time_ms)} (Local PB: {self._format_time(current_pb)})")
            print("📤 Submitting lap to server...")
        
        try:
            # Submit lap time (leaderboard)
            lap_time_str = self._format_time(lap_time_ms)
            response = requests.post(
                f"{self.bot_api_url}/api/telemetry/submit",
                json={
                    'time': lap_time_str,
                    'track': track_name,
                    'user_id': self.discord_user_id,
                    'source': 'telemetry',
                    'timestamp': datetime.now().isoformat(),
                    'sector_times': {
                        'sector1_ms': lap_trace.sector1_ms,
                        'sector2_ms': lap_trace.sector2_ms,
                        'sector3_ms': lap_trace.sector3_ms
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Lap time submitted to leaderboard")
            else:
                print(f"⚠️ Leaderboard submission failed: HTTP {response.status_code}")
            
            # Submit full telemetry trace (for Mathe-Coach)
            trace_response = requests.post(
                f"{self.bot_api_url}/api/telemetry/trace",
                json=lap_trace.to_api_payload(self.discord_user_id),
                timeout=30  # Longer timeout for large payload
            )
            
            if trace_response.status_code == 200:
                print(f"✅ Telemetry trace submitted ({len(lap_trace.samples)} samples)")
            else:
                print(f"⚠️ Trace submission failed: HTTP {trace_response.status_code}")
        
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to bot server")
        except requests.exceptions.Timeout:
            print("❌ Request timed out")
        except Exception as e:
            print(f"❌ Error submitting lap: {e}")
    
    def _format_time(self, time_ms: int) -> str:
        """Format milliseconds to MM:SS.mmm."""
        if time_ms <= 0:
            return "0:00.000"
        
        total_seconds = time_ms / 1000.0
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        
        if minutes > 0:
            return f"{minutes}:{seconds:06.3f}"
        else:
            return f"{seconds:.3f}"


def load_config():
    """Load configuration from config.json."""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ config.json not found, using defaults")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config.json: {e}")
        return {}


def main():
    """Main entry point."""
    print("🏎️ F1 2025 UDP Telemetry Listener v3.0")
    print("=" * 50)
    print("📡 Full Telemetry Capture for Mathe-Coach")
    print("=" * 50)
    
    config = load_config()
    
    listener = F1TelemetryListenerV3(
        port=config.get('port', 20777),
        bot_integration=config.get('bot_integration', False),
        discord_user_id=config.get('discord_user_id'),
        bot_api_url=config.get('bot_api_url', 'http://localhost:8080')
    )
    
    try:
        listener.start()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        listener.stop()


if __name__ == "__main__":
    main()

"""F1 2025 UDP Telemetry Listener for Time Trial Mode.

This module listens for UDP telemetry data from F1 2025 and automatically
submits lap times to the Discord bot when valid time trial laps are completed.
"""

import socket
import struct
import asyncio
import threading
import time
import json
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

# F1 2025 UDP Packet IDs (based on Codemasters telemetry specification)
PACKET_SESSION_DATA = 1
PACKET_LAP_DATA = 2
PACKET_EVENT = 3
PACKET_PARTICIPANTS = 4
PACKET_CAR_SETUPS = 5
PACKET_CAR_TELEMETRY = 6
PACKET_CAR_STATUS = 7
PACKET_FINAL_CLASSIFICATION = 8
PACKET_LOBBY_INFO = 9
PACKET_CAR_DAMAGE = 10
PACKET_SESSION_HISTORY = 11

# Session Types
SESSION_TYPE_TIME_TRIAL = 10
SESSION_TYPE_PRACTICE_1 = 1
SESSION_TYPE_PRACTICE_2 = 2
SESSION_TYPE_PRACTICE_3 = 3
SESSION_TYPE_SHORT_PRACTICE = 4
SESSION_TYPE_QUALIFYING_1 = 5
SESSION_TYPE_QUALIFYING_2 = 6
SESSION_TYPE_QUALIFYING_3 = 7
SESSION_TYPE_SHORT_QUALIFYING = 8
SESSION_TYPE_OSQ = 9
SESSION_TYPE_RACE = 12
SESSION_TYPE_RACE_2 = 13

# Lap validity flags
LAP_VALID = 0x01
LAP_INVALID_CORNER_CUTTING = 0x02
LAP_INVALID_PARKING = 0x04
LAP_INVALID_PIT_LANE = 0x08
LAP_INVALID_WALL_RIDING = 0x10
LAP_INVALID_FLASHBACK = 0x20

@dataclass
class SessionInfo:
    """Session information from F1 2025."""
    session_type: int
    track_id: int
    session_uid: int
    is_time_trial: bool = False
    track_name: str = "Unknown"

@dataclass
class LapData:
    """Lap data from F1 2025."""
    lap_time_ms: int
    sector1_time_ms: int
    sector2_time_ms: int
    sector3_time_ms: int
    lap_distance: float
    total_distance: float
    safety_car_delta: float
    car_position: int
    current_lap_num: int
    pit_status: int
    sector: int
    current_lap_invalid: bool
    penalties: int
    grid_position: int
    driver_status: int
    result_status: int
    lap_valid_bit_flags: int

class F1TelemetryListener:
    """F1 2025 UDP Telemetry Listener with validation."""
    
    def __init__(self, port: int = 20777, bot_integration: bool = False, 
                 discord_user_id: str = None, bot_api_url: str = None):
        self.port = port
        self.bot_integration = bot_integration
        self.discord_user_id = discord_user_id  # Discord User ID für Bot-Integration
        self.bot_api_url = bot_api_url or "http://localhost:8080/api/telemetry/submit"
        self.socket = None
        self.running = False
        self.session_info: Optional[SessionInfo] = None
        self.last_lap_time = 0
        self.player_car_index = 0  # Usually 0 for the player
        
        # Personal best times per track (in milliseconds)
        self.personal_bests: Dict[str, int] = {}
        
        # Track mapping (F1 2025 track IDs to our track names)
        self.track_mapping = {
            0: "bahrain",
            1: "jeddah",
            2: "australia",
            3: "baku",
            4: "miami",
            5: "imola",
            6: "monaco",
            7: "spain",
            8: "canada",
            9: "austria",
            10: "silverstone",
            11: "hungary",
            12: "spa",
            13: "netherlands",
            14: "monza",
            15: "singapore",
            16: "japan",
            17: "qatar",
            18: "usa",
            19: "mexico",
            20: "brazil",
            21: "las-vegas",
            22: "abu-dhabi"
        }
    
    def start(self):
        """Start the UDP listener."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('0.0.0.0', self.port))
            self.running = True
            
            print(f"🏎️ F1 2025 Telemetry Listener started on port {self.port}")
            print("🎯 Monitoring for Time Trial sessions...")
            print("⚠️  Make sure F1 2025 UDP telemetry is enabled in game settings!")
            print("📡 Waiting for telemetry data...\n")
            
            while self.running:
                try:
                    data, addr = self.socket.recvfrom(2048)
                    self.process_packet(data)
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"❌ Error receiving data: {e}")
                    
        except Exception as e:
            print(f"❌ Failed to start telemetry listener: {e}")
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
        if len(data) < 24:  # Minimum packet size
            return
        
        try:
            # Parse packet header
            header = struct.unpack('<HHBBBBBQ', data[:24])
            packet_format = header[0]
            game_major_version = header[1]
            game_minor_version = header[2]
            packet_version = header[3]
            packet_id = header[4]
            session_uid = header[5]
            session_time = header[6]
            frame_identifier = header[7]
            
            # Process different packet types
            if packet_id == PACKET_SESSION_DATA:
                self.process_session_data(data[24:])
            elif packet_id == PACKET_LAP_DATA:
                self.process_lap_data(data[24:])
            elif packet_id == PACKET_EVENT:
                self.process_event_data(data[24:])
                
        except struct.error as e:
            print(f"⚠️  Error parsing packet: {e}")
        except Exception as e:
            print(f"❌ Unexpected error processing packet: {e}")
    
    def process_session_data(self, data: bytes):
        """Process session data packet."""
        try:
            # Parse session data (simplified structure)
            session_type = struct.unpack('<B', data[0:1])[0]
            track_id = struct.unpack('<b', data[1:2])[0]
            
            # Check if this is a time trial session
            is_time_trial = session_type == SESSION_TYPE_TIME_TRIAL
            
            if is_time_trial and (not self.session_info or self.session_info.track_id != track_id):
                track_name = self.track_mapping.get(track_id, f"track_{track_id}")
                
                self.session_info = SessionInfo(
                    session_type=session_type,
                    track_id=track_id,
                    session_uid=0,  # Would need to parse from header
                    is_time_trial=is_time_trial,
                    track_name=track_name
                )
                
                print(f"🏁 Time Trial session detected!")
                print(f"📍 Track: {track_name.title()} (ID: {track_id})")
                print(f"🎮 Session Type: Time Trial")
                print("✅ Ready to capture lap times!\n")
                
            elif not is_time_trial and self.session_info and self.session_info.is_time_trial:
                print("🚫 Session changed - no longer Time Trial mode")
                self.session_info = None
                
        except Exception as e:
            print(f"❌ Error processing session data: {e}")
    
    def process_lap_data(self, data: bytes):
        """Process lap data packet."""
        if not self.session_info or not self.session_info.is_time_trial:
            return
            
        try:
            # Parse lap data for player car (car index 0)
            car_data_size = 53  # Size of each car's lap data
            player_data_offset = self.player_car_index * car_data_size
            
            if len(data) < player_data_offset + car_data_size:
                return
                
            player_data = data[player_data_offset:player_data_offset + car_data_size]
            
            # Parse player lap data
            lap_data = struct.unpack('<IfffffBBBBBBBBBBBf', player_data)
            
            lap_time_ms = lap_data[0]
            sector1_ms = int(lap_data[1] * 1000) if lap_data[1] > 0 else 0
            sector2_ms = int(lap_data[2] * 1000) if lap_data[2] > 0 else 0
            sector3_ms = int(lap_data[3] * 1000) if lap_data[3] > 0 else 0
            lap_distance = lap_data[4]
            total_distance = lap_data[5]
            current_lap_invalid = bool(lap_data[8])
            lap_valid_flags = lap_data[16]
            
            # Check if this is a completed, valid lap
            if (lap_time_ms > 0 and 
                lap_time_ms != self.last_lap_time and 
                lap_time_ms > 30000 and  # Minimum 30 seconds
                lap_time_ms < 300000):   # Maximum 5 minutes
                
                # Validate lap
                is_valid_lap = self.validate_lap(
                    lap_time_ms, current_lap_invalid, lap_valid_flags
                )
                
                if is_valid_lap:
                    self.handle_completed_lap(
                        lap_time_ms, sector1_ms, sector2_ms, sector3_ms
                    )
                else:
                    print(f"⚠️  Invalid lap detected (time: {self.format_time(lap_time_ms)}) - not submitted")
                
                self.last_lap_time = lap_time_ms
                
        except Exception as e:
            print(f"❌ Error processing lap data: {e}")
    
    def process_event_data(self, data: bytes):
        """Process event data packet."""
        try:
            # Parse event string code (4 characters)
            event_code = data[:4].decode('ascii', errors='ignore')
            
            if event_code == "SSTA":  # Session Started
                print("🚀 Session started")
            elif event_code == "SEND":  # Session Ended
                print("🏁 Session ended")
                self.session_info = None
            elif event_code == "FTLP":  # Fastest Lap
                print("⚡ Fastest lap achieved!")
                
        except Exception as e:
            print(f"❌ Error processing event data: {e}")
    
    def validate_lap(self, lap_time_ms: int, current_lap_invalid: bool, lap_valid_flags: int) -> bool:
        """Validate if a lap is legitimate and should be submitted."""
        # Check basic lap validity
        if current_lap_invalid:
            return False
            
        # Check lap validity flags
        if lap_valid_flags & (LAP_INVALID_CORNER_CUTTING | 
                             LAP_INVALID_PARKING |
                             LAP_INVALID_PIT_LANE |
                             LAP_INVALID_WALL_RIDING |
                             LAP_INVALID_FLASHBACK):
            return False
            
        # Time range validation (30 seconds to 5 minutes)
        if lap_time_ms < 30000 or lap_time_ms > 300000:
            return False
            
        return True
    
    def handle_completed_lap(self, lap_time_ms: int, sector1_ms: int, 
                           sector2_ms: int, sector3_ms: int):
        """Handle a completed valid lap."""
        if not self.session_info:
            return
            
        lap_time_str = self.format_time(lap_time_ms)
        track_name = self.session_info.track_name
        
        # Check if this is a personal best time
        current_pb = self.personal_bests.get(track_name)
        is_personal_best = current_pb is None or lap_time_ms < current_pb
        
        print(f"🏆 Valid lap completed!")
        print(f"⏱️  Time: {lap_time_str}")
        print(f"📍 Track: {track_name.title()}")
        print(f"🎯 Sectors: S1: {self.format_time(sector1_ms)} | S2: {self.format_time(sector2_ms)} | S3: {self.format_time(sector3_ms)}")
        
        if is_personal_best:
            improvement = ""
            if current_pb:
                improvement_ms = current_pb - lap_time_ms
                improvement = f" (🚀 -{self.format_time(improvement_ms)} improvement!)"
            else:
                improvement = " (🎉 First time on this track!)"
            
            print(f"🆕 Personal Best{improvement}")
            self.personal_bests[track_name] = lap_time_ms
            
            if self.bot_integration:
                self.submit_to_bot(lap_time_str, track_name)
            else:
                print("💡 Bot integration disabled - lap time not submitted automatically")
                print(f"📝 To submit manually: /lap submit {lap_time_str} {track_name}")
        else:
            slower_by_ms = lap_time_ms - current_pb
            print(f"⏱️  Not a personal best (+{self.format_time(slower_by_ms)} slower than PB: {self.format_time(current_pb)})")
            print("❌ Lap time not submitted (only personal bests are sent to Discord)")
        
        print("-" * 60)
    
    def submit_to_bot(self, lap_time: str, track_name: str):
        """Submit lap time to Discord bot (placeholder for integration)."""
        # TODO: Integrate with Discord bot API
        # This would make an API call to your bot to submit the lap time
        print(f"🤖 Submitting to bot: /lap submit {lap_time} {track_name}")
        
        # Example integration:
        # try:
        #     response = requests.post(
        #         'http://localhost:3000/api/submit-lap',
        #         json={
        #             'time': lap_time,
        #             'track': track_name,
        #             'user_id': 'telemetry_user'  # Would need to be configured
        #         }
        #     )
        #     if response.status_code == 200:
        #         print("✅ Lap time submitted successfully!")
        #     else:
        #         print(f"❌ Failed to submit lap time: {response.status_code}")
        # except Exception as e:
        #     print(f"❌ Error submitting to bot: {e}")
    
    def format_time(self, time_ms: int) -> str:
        """Format milliseconds to MM:SS.mmm format."""
        if time_ms <= 0:
            return "0:00.000"
            
        total_seconds = time_ms / 1000.0
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        
        if minutes > 0:
            return f"{minutes}:{seconds:06.3f}"
        else:
            return f"{seconds:.3f}"


def main():
    """Main function to run the telemetry listener."""
    print("🏎️ F1 2025 UDP Telemetry Listener")
    print("=" * 40)
    print("🎯 Time Trial Mode Only")
    print("📡 Listening for valid lap completions...")
    print("\n⚙️  Setup Instructions:")
    print("1. Enable UDP telemetry in F1 2025 settings")
    print("2. Start a Time Trial session")
    print("3. Complete valid laps to see them captured")
    print("\n🛑 Press Ctrl+C to stop\n")
    
    listener = F1TelemetryListener(port=20777, bot_integration=False)
    
    try:
        listener.start()
    except KeyboardInterrupt:
        print("\n🛑 Stopping telemetry listener...")
        listener.stop()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        listener.stop()


if __name__ == "__main__":
    main()

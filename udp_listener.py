"""F1 2025 UDP Telemetry Listener for Time Trial Mode.

This module listens for UDP telemetry data from F1 2025 and automatically
submits lap times to the Discord bot when valid time trial laps are completed.

Using f1-packets library for official F1 2025 packet parsing.
"""

import socket
import json
import requests
from typing import Optional, Dict
from datetime import datetime
from dataclasses import dataclass

# Import f1-packets library for official F1 2025 packet parsing
from f1.listener import PacketListener
from f1.packets import (
    PacketSessionData, PacketLapData, PacketEventData, PacketTimeTrialData, Packet
)

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
            4: "spain",     # Fixed: Spain, not Miami
            5: "miami",     # Fixed: Miami is track 5
            6: "imola",
            7: "monaco",
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
        """Process incoming UDP packet using f1-packets library."""
        try:
            # Parse the packet header first to determine packet type
            if len(data) < 29:  # Minimum header size for F1 2025
                return
            
            # Parse header manually to get packet ID
            import struct
            header_data = struct.unpack('<HBBBBBQffIBB', data[:29])
            packet_format, game_year, game_major_version, game_minor_version, packet_version, packet_id, session_uid, session_time, frame_identifier, overall_frame_identifier, player_car_index, secondary_player_car_index = header_data
            
            self.player_car_index = player_car_index
            
            # Debug: Show all packet types and analyze their content
            if packet_id not in [6, 7]:  # Only skip telemetry and car status spam
                print(f"📦 Packet ID: {packet_id}, Size: {len(data)} bytes")
                
                # Try to extract useful info from unknown packets
                if packet_id not in [1, 2, 3, 13] and len(data) > 29:
                    try:
                        # Try to find track info in other packets
                        raw_data = data[29:50] if len(data) > 50 else data[29:]
                        print(f"🔍 Raw data sample: {raw_data.hex()[:40]}...")
                    except:
                        pass
            
            # Create mutable buffer and parse specific packet type
            mutable_buffer = bytearray(data)
            
            try:
                # Parse based on packet ID
                if packet_id == 1:  # Session data
                    packet = PacketSessionData.from_buffer(mutable_buffer)
                    self.process_session_data_official(packet, session_uid)
                elif packet_id == 2:  # Lap data  
                    packet = PacketLapData.from_buffer(mutable_buffer)
                    self.process_lap_data_official(packet)
                elif packet_id == 3:  # Event data
                    packet = PacketEventData.from_buffer(mutable_buffer)
                    self.process_event_data_official(packet)
                elif packet_id == 13:  # Time Trial data
                    packet = PacketTimeTrialData.from_buffer(mutable_buffer)
                    self.process_time_trial_data_official(packet)
                # Ignore other packet types for now
                    
            except Exception as parse_error:
                if not hasattr(self, '_packet_parse_errors'):
                    self._packet_parse_errors = {}
                if packet_id not in self._packet_parse_errors:
                    print(f"⚠️  Could not parse packet type {packet_id}: {parse_error}")
                    self._packet_parse_errors[packet_id] = True
                
        except Exception as e:
            # Only show error for first few packets to avoid spam
            if not hasattr(self, '_error_count'):
                self._error_count = 0
            
            if self._error_count < 3:
                print(f"⚠️  Error parsing packet (size: {len(data)} bytes): {e}")
                if len(data) <= 100:
                    print(f"🔍 Raw packet data: {data.hex()[:200]}...")
                self._error_count += 1
            elif self._error_count == 3:
                print("⚠️  Suppressing further parsing errors (enable debug mode for more details)...")
                self._error_count += 1
    
    def process_session_data_official(self, packet: PacketSessionData, session_uid: int):
        """Process session data packet using f1-packets official classes."""
        try:
            # Access fields directly from packet (not m_sessionData)
            weather = packet.weather
            track_temperature = packet.track_temperature
            air_temperature = packet.air_temperature
            total_laps = packet.total_laps
            track_length = packet.track_length
            session_type = packet.session_type
            track_id = packet.track_id
            
            session_type_names = {
                1: "Practice 1", 2: "Practice 2", 3: "Practice 3", 4: "Short Practice",
                5: "Qualifying 1", 6: "Qualifying 2", 7: "Qualifying 3", 8: "Short Qualifying",
                9: "OSQ", 10: "Time Trial", 12: "Race", 13: "Race 2"
            }
            
            session_name = session_type_names.get(session_type, f"Unknown ({session_type})")
            track_name = self.track_mapping.get(track_id, f"track_{track_id}")
            
            print(f"📍 {session_name} at {track_name.title()} ({track_temperature}°C)")
            print(f"🔍 DEBUG: session_type={session_type}, track_id={track_id}, track_name={track_name}")
            
            # Check if this is a time trial session
            is_time_trial = session_type == SESSION_TYPE_TIME_TRIAL
            
            if is_time_trial and (not self.session_info or self.session_info.track_id != track_id):
                self.session_info = SessionInfo(
                    session_type=session_type,
                    track_id=track_id,
                    session_uid=session_uid,  # Use parsed session_uid from header
                    is_time_trial=True,
                    track_name=track_name
                )
                
                print(f"🏆 TIME TRIAL SESSION DETECTED!")
                print(f"📍 Track: {track_name.title()} (ID: {track_id})")
                print(f"🎮 Session Type: Time Trial")
                print("✅ Ready to capture lap times!\n")
                
            elif not is_time_trial and self.session_info and self.session_info.is_time_trial:
                print("🚫 Session changed - no longer Time Trial mode")
                self.session_info = None
                
        except Exception as e:
            print(f"❌ Error processing session data: {e}")
    
    def process_lap_data_official(self, packet: PacketLapData):
        """Process lap data packet using f1-packets official classes."""
        if not self.session_info or not self.session_info.is_time_trial:
            return
            
        try:
            # Get lap data for the player's car (use correct field name without m_ prefix)
            if self.player_car_index >= len(packet.lap_data):
                return
                
            player_lap_data = packet.lap_data[self.player_car_index]
            
            # Use the correct field names from the debug output
            try:
                lap_time_ms = player_lap_data.last_lap_time_in_ms
                
                # Calculate sector times - sector times might be 0 if lap just completed
                sector1_ms = (player_lap_data.sector1_time_minutes_part * 60000) + player_lap_data.sector1_time_ms_part
                sector2_ms = (player_lap_data.sector2_time_minutes_part * 60000) + player_lap_data.sector2_time_ms_part
                
                # Calculate sector 3 from total lap time
                if lap_time_ms > 0:
                    if sector1_ms > 0 and sector2_ms > 0:
                        sector3_ms = lap_time_ms - sector1_ms - sector2_ms
                    else:
                        # Fallback: Use average sector times if individual sectors are 0
                        sector1_ms = sector1_ms or int(lap_time_ms * 0.33)
                        sector2_ms = sector2_ms or int(lap_time_ms * 0.33) 
                        sector3_ms = lap_time_ms - sector1_ms - sector2_ms
                else:
                    sector3_ms = 0
                
                current_lap_invalid = player_lap_data.current_lap_invalid
                
                # Lap valid flags don't seem to be available in this structure, use penalties as fallback
                lap_valid_flags = player_lap_data.penalties if hasattr(player_lap_data, 'penalties') else 0
                
                print(f"🎯 Lap time: {lap_time_ms}ms, Sectors: {sector1_ms}|{sector2_ms}|{sector3_ms}, Invalid: {current_lap_invalid}, Penalties: {lap_valid_flags}")
            except Exception as field_error:
                print(f"❌ Field access error: {field_error}")
                return
            
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
    
    def process_event_data_official(self, packet: PacketEventData):
        """Process event data packet using f1-packets official classes."""
        try:
            # Use correct field name from f1-packets library
            event_code_bytes = bytes(packet.event_string_code)
            event_code = event_code_bytes.decode('ascii', errors='ignore').strip('\x00')
            
            if event_code == "SSTA":  # Session Started
                print("🚀 Session started")
            elif event_code == "SEND":  # Session Ended
                print("🏁 Session ended")
                self.session_info = None
            elif event_code == "FTLP":  # Fastest Lap
                print("⚡ Fastest lap achieved!")
                
        except Exception as e:
            print(f"❌ Error processing event data: {e}")
    
    def process_time_trial_data_official(self, packet: PacketTimeTrialData):
        """Process Time Trial packet using f1-packets official classes."""
        try:
            print(f"\n🏆 TIME TRIAL PACKET DETECTED (OFFICIAL)!")
            
            # Access the correct field names from f1-packets library
            player_data = packet.player_session_best_data_set
            
            # Use correct field names for TimeTrialDataSet (no 'm_' prefix)
            car_idx = player_data.car_idx
            team_id = player_data.team_id
            lap_time_ms = player_data.lap_time_in_ms
            sector1_ms = player_data.sector1_time_in_ms
            sector2_ms = player_data.sector2_time_in_ms
            sector3_ms = player_data.sector3_time_in_ms
            traction_control = player_data.traction_control
            gearbox_assist = player_data.gearbox_assist
            anti_lock_brakes = player_data.anti_lock_brakes
            equal_car_performance = player_data.equal_car_performance
            custom_setup = player_data.custom_setup
            valid = player_data.valid
            
            print(f"🚗 Car Index: {car_idx}, Team: {team_id}")
            
            if valid and lap_time_ms > 0:
                print(f"⏱️  Session Best: {self.format_time(lap_time_ms)}")
                print(f"🎯 Sectors: S1: {self.format_time(sector1_ms)} | S2: {self.format_time(sector2_ms)} | S3: {self.format_time(sector3_ms)}")
                print(f"🎮 Assists: TC:{traction_control}, Gearbox:{gearbox_assist}, ABS:{anti_lock_brakes}")
                
                # Don't override session info if we already have proper track data from session packet
                if not self.session_info:
                    # F1 2025 Time Trial doesn't send Session Data packets!
                    # Ask user for track name or use a default
                    print("⚠️  F1 2025 Time Trial mode doesn't provide track information!")
                    print("📝 Please specify track name in config.json or use manual submission")
                    
                    # Try to get track from config or use spain as fallback
                    config = load_config()
                    fallback_track = config.get('default_track', 'spain')
                    
                    self.session_info = SessionInfo(
                        session_type=10,  # Time Trial
                        track_id=-1,     # Unknown from this packet
                        session_uid=0,   # Unknown from this packet
                        is_time_trial=True,
                        track_name=fallback_track  # Use config fallback
                    )
                    
                    print(f"🔧 Using fallback track: {fallback_track}")
                    print(f"💡 To change track: Add 'default_track': 'track_name' to config.json")
                    
                    print(f"✅ TIME TRIAL MODE CONFIRMED!")
                    print(f"🎯 Ready to capture lap times!\n")
            else:
                print(f"⚠️  No valid session best yet")
                
        except Exception as e:
            print(f"❌ Error processing Time Trial data: {e}")
    
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
        """Submit lap time to Discord bot running on central server."""
        if not self.discord_user_id:
            print("❌ Discord User ID not configured - cannot submit to bot")
            print(f"📝 To submit manually: /lap submit {lap_time} {track_name}")
            return
            
        print(f"🤖 Submitting to central bot server: {lap_time} on {track_name}")
        
        try:
            # Submit to central Discord bot server
            response = requests.post(
                self.bot_api_url,
                json={
                    'time': lap_time,
                    'track': track_name,
                    'user_id': self.discord_user_id,
                    'source': 'telemetry',
                    'timestamp': datetime.now().isoformat()
                },
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'F1-2025-UDP-Listener/1.0'
                },
                timeout=10  # 10 second timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Lap time submitted successfully to Discord!")
                if 'message' in result:
                    print(f"📝 Server response: {result['message']}")
            elif response.status_code == 400:
                error = response.json().get('error', 'Bad request')
                print(f"❌ Invalid submission: {error}")
            elif response.status_code == 409:
                print("⚠️  Lap time not faster than personal best - not submitted")
            else:
                print(f"❌ Failed to submit lap time: HTTP {response.status_code}")
                print(f"📝 Fallback: /lap submit {lap_time} {track_name}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to Discord bot server")
            print("📝 Check if bot server is running and URL is correct")
            print(f"📝 Manual submission: /lap submit {lap_time} {track_name}")
        except requests.exceptions.Timeout:
            print("❌ Request to bot server timed out")
            print(f"📝 Manual submission: /lap submit {lap_time} {track_name}")
        except Exception as e:
            print(f"❌ Error submitting to bot server: {e}")
            print(f"📝 Manual submission: /lap submit {lap_time} {track_name}")
    
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


def load_config():
    """Load configuration from config.json file."""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️  config.json not found, using default settings")
        print("📝 Copy config_example.json to config.json and configure your settings")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config.json: {e}")
        return {}

def main():
    """Main function to run the telemetry listener."""
    print("🏎️ F1 2025 UDP Telemetry Listener")
    print("=" * 40)
    print("🎯 Time Trial Mode Only")
    print("📡 Listening for valid lap completions...")
    
    # Load configuration
    config = load_config()
    
    discord_user_id = config.get('discord_user_id')
    bot_api_url = config.get('bot_api_url')
    port = config.get('port', 20777)
    bot_integration = config.get('bot_integration', False)
    player_name = config.get('player_name', 'Unknown Player')
    
    if bot_integration and discord_user_id:
        print(f"🤖 Bot integration: ENABLED")
        print(f"👤 Player: {player_name}")
        print(f"📱 Discord User ID: {discord_user_id}")
        print(f"🌐 Bot Server: {bot_api_url}")
    else:
        print("📝 Bot integration: DISABLED (manual submission required)")
        if bot_integration and not discord_user_id:
            print("❌ Discord User ID missing - check config.json")
    
    print("\n⚙️  Setup Instructions:")
    print("1. Enable UDP telemetry in F1 2025 settings")
    print("2. Start a Time Trial session")
    print("3. Complete valid laps to see them captured")
    print("\n🛑 Press Ctrl+C to stop\n")
    
    listener = F1TelemetryListener(
        port=port, 
        bot_integration=bot_integration,
        discord_user_id=discord_user_id,
        bot_api_url=bot_api_url
    )
    
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

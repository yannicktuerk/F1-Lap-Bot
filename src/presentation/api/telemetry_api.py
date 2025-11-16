"""HTTP API server for receiving telemetry data from UDP listeners."""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from aiohttp import web, WSMsgType
from aiohttp.web import Request, Response
import aiohttp_cors

from src.application.use_cases.submit_lap_time import SubmitLapTimeUseCase
from src.application.use_cases.update_elo_ratings import UpdateEloRatingsUseCase
from src.domain.value_objects.time_format import TimeFormat
from src.domain.value_objects.track_name import TrackName
from src.infrastructure.persistence.sqlite_lap_time_repository import SQLiteLapTimeRepository
import discord


class TelemetryAPI:
    """HTTP API server for receiving telemetry data."""
    
    def __init__(self, lap_time_repository: SQLiteLapTimeRepository, driver_rating_repository, host: str = "0.0.0.0", port: int = 8080, discord_bot=None):
        self.host = host
        self.port = port
        self.lap_time_repository = lap_time_repository
        self.driver_rating_repository = driver_rating_repository
        self.submit_use_case = SubmitLapTimeUseCase(lap_time_repository, driver_rating_repository)
        self.update_elo_use_case = UpdateEloRatingsUseCase(driver_rating_repository, lap_time_repository)
        self.discord_bot = discord_bot  # Reference to Discord bot for user lookup
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        
        # Setup routes
        self._setup_routes()
        self._setup_cors()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def _setup_routes(self):
        """Setup API routes."""
        self.app.router.add_post('/api/telemetry/submit', self.submit_telemetry)
        self.app.router.add_post('/api/telemetry/session/register', self.register_session)
        self.app.router.add_post('/api/telemetry/trace', self.submit_trace)
        self.app.router.add_get('/api/health', self.health_check)
        self.app.router.add_get('/api/status', self.status_check)
        
    def _setup_cors(self):
        """Setup CORS for cross-origin requests."""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods=["GET", "POST", "OPTIONS"]
            )
        })
        
        # Add CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def start(self):
        """Start the HTTP API server."""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()
            
            print(f"🌐 Telemetry API server started on http://{self.host}:{self.port}")
            print(f"📡 Ready to receive telemetry data at /api/telemetry/submit")
            
        except Exception as e:
            print(f"❌ Failed to start API server: {e}")
            raise
    
    async def stop(self):
        """Stop the HTTP API server."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        print("🛑 Telemetry API server stopped")
    
    async def submit_telemetry(self, request: Request) -> Response:
        """Handle telemetry data submission from UDP listeners."""
        try:
            # Parse JSON request
            data = await request.json()
            
            # Full debug logging of received data
            print(f"\n📡 TELEMETRY API: Received request")
            print(f"🔍 Full request data: {json.dumps(data, indent=2)}")
            
            # Extract and validate required fields
            required_fields = {'user_id': 'user_id', 'time': 'time', 'track': 'track'}
            missing_fields = [name for key, name in required_fields.items() if not data.get(key)]
            
            if missing_fields:
                return web.json_response(
                    {'error': f'Missing required field(s): {", ".join(missing_fields)}'},
                    status=400
                )
            
            user_id = data['user_id']
            time_str = data['time']
            track_str = data['track']
            source = data.get('source', 'telemetry')
            
            # Extract sector times if provided
            sector_times = data.get('sector_times', {})
            sector1_ms = sector_times.get('sector1_ms')
            sector2_ms = sector_times.get('sector2_ms')
            sector3_ms = sector_times.get('sector3_ms')
            
            # Debug logging for sector times
            print(f"🔍 EXTRACTED: User={user_id}, Time={time_str}, Track={track_str}")
            print(f"🔍 SECTORS: S1={sector1_ms}ms, S2={sector2_ms}ms, S3={sector3_ms}ms")
            
            # Get user info (we need username for the submission)
            username = await self._get_discord_username(user_id)
            
            try:
                # Submit the lap time using the use case
                lap_time, is_personal_best, is_overall_best = await self.submit_use_case.execute(
                    user_id=user_id,
                    username=username,
                    time_string=time_str,
                    track_string=track_str,
                    sector1_ms=sector1_ms,
                    sector2_ms=sector2_ms,
                    sector3_ms=sector3_ms
                )

                # Update ELO ratings
                await self.update_elo_use_case.execute(lap_time)

                # Log successful submission
                self.logger.info(f"Telemetry lap submitted: {username} - {time_str} on {track_str}")
                print(f"📊 Telemetry lap received: {username} - {time_str} on {track_str}")
                
                # Return success response
                response_data = {
                    'status': 'success',
                    'message': 'Lap time submitted successfully',
                    'lap_id': lap_time.lap_id,
                    'is_personal_best': is_personal_best,
                    'is_overall_best': is_overall_best,
                    'time': time_str,
                    'track': track_str,
                    'user_id': user_id,
                    'source': source,
                    'received_at': datetime.now().isoformat()
                }
                
                if is_personal_best:
                    response_data['improvement'] = 'Personal Best!'
                if is_overall_best:
                    response_data['improvement'] = 'Overall Best!'
                
                return web.json_response(response_data, status=200)
                
            except ValueError as e:
                # Invalid time or track format
                return web.json_response(
                    {'error': f'Invalid data format: {str(e)}'},
                    status=400
                )
                
        except json.JSONDecodeError:
            return web.json_response(
                {'error': 'Invalid JSON format'},
                status=400
            )
        except Exception as e:
            self.logger.error(f"Error processing telemetry submission: {e}")
            return web.json_response(
                {'error': 'Internal server error'},
                status=500
            )
    
    async def health_check(self, request: Request) -> Response:
        """Health check endpoint."""
        return web.json_response({
            'status': 'healthy',
            'service': 'F1 Lap Bot Telemetry API',
            'timestamp': datetime.now().isoformat()
        })
    
    async def status_check(self, request: Request) -> Response:
        """Status check endpoint with database info."""
        try:
            # Get some basic stats from the database
            # TODO: Implement get_all() method or use async method
            total_laps = 0  # Placeholder
            
            return web.json_response({
                'status': 'operational',
                'service': 'F1 Lap Bot Telemetry API',
                'database': 'connected',
                'total_laps': total_laps,
                'api_version': '1.0.0',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return web.json_response({
                'status': 'degraded',
                'service': 'F1 Lap Bot Telemetry API',
                'database': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }, status=503)
    
    async def register_session(self, request: Request) -> Response:
        """Register new telemetry session with user_id."""
        try:
            data = await request.json()
            
            # Extract required fields
            session_uid = data.get('session_uid')
            track_id = data.get('track_id')
            session_type = data.get('session_type')
            user_id = data.get('user_id')
            
            if not all([session_uid, track_id, session_type, user_id]):
                return web.json_response(
                    {'error': 'Missing required fields: session_uid, track_id, session_type, user_id'},
                    status=400
                )
            
            # Get telemetry repository (need to inject it)
            if not hasattr(self, 'telemetry_repository'):
                return web.json_response(
                    {'error': 'Telemetry repository not configured'},
                    status=503
                )
            
            # Register session
            await self.telemetry_repository.save_session(
                session_uid=str(session_uid),
                track_id=track_id,
                session_type=int(session_type),
                user_id=user_id
            )
            
            print(f"✅ Session registered: UID={session_uid}, Track={track_id}, User={user_id}")
            
            return web.json_response({
                'status': 'success',
                'message': 'Session registered successfully',
                'session_uid': session_uid,
                'track_id': track_id,
                'user_id': user_id
            }, status=200)
        
        except Exception as e:
            self.logger.error(f"Error registering session: {e}")
            return web.json_response(
                {'error': f'Failed to register session: {str(e)}'},
                status=500
            )
    
    async def submit_trace(self, request: Request) -> Response:
        """Submit complete telemetry trace for a lap."""
        try:
            data = await request.json()
            
            # Extract required fields
            session_uid = data.get('session_uid')
            track_id = data.get('track_id')
            lap_number = data.get('lap_number')
            car_index = data.get('car_index')
            lap_time_ms = data.get('lap_time_ms')
            is_valid = data.get('is_valid', True)
            user_id = data.get('user_id')
            samples = data.get('telemetry_samples', [])
            sector_times = data.get('sector_times', {})
            
            if not all([session_uid, track_id, lap_number is not None, car_index is not None, lap_time_ms, user_id]):
                return web.json_response(
                    {'error': 'Missing required fields'},
                    status=400
                )
            
            # Get telemetry repository
            if not hasattr(self, 'telemetry_repository'):
                return web.json_response(
                    {'error': 'Telemetry repository not configured'},
                    status=503
                )
            
            # Import domain entities
            from src.domain.entities.lap_trace import LapTrace
            from src.domain.value_objects.telemetry_sample import TelemetrySample
            
            # Create LapTrace entity
            lap_trace = LapTrace(
                session_uid=str(session_uid),
                lap_number=int(lap_number),
                car_index=int(car_index),
                is_valid=bool(is_valid),
                track_id=track_id,
                lap_time_ms=int(lap_time_ms)
            )
            
            # Add telemetry samples
            for sample_data in samples:
                try:
                    sample = TelemetrySample(
                        timestamp_ms=int(sample_data['timestamp_ms']),
                        world_position_x=float(sample_data['world_position_x']),
                        world_position_y=float(sample_data['world_position_y']),
                        world_position_z=float(sample_data['world_position_z']),
                        world_velocity_x=float(sample_data['world_velocity_x']),
                        world_velocity_y=float(sample_data['world_velocity_y']),
                        world_velocity_z=float(sample_data['world_velocity_z']),
                        g_force_lateral=float(sample_data['g_force_lateral']),
                        g_force_longitudinal=float(sample_data['g_force_longitudinal']),
                        yaw=float(sample_data['yaw']),
                        speed=float(sample_data['speed']),
                        throttle=float(sample_data['throttle']),
                        steer=float(sample_data['steer']),
                        brake=float(sample_data['brake']),
                        gear=int(sample_data['gear']),
                        engine_rpm=int(sample_data['engine_rpm']),
                        drs=int(sample_data['drs']),
                        lap_distance=float(sample_data['lap_distance']),
                        lap_number=int(sample_data['lap_number'])
                    )
                    lap_trace.add_sample(sample)
                except (KeyError, ValueError) as e:
                    self.logger.warning(f"Skipping invalid sample: {e}")
                    continue
            
            # Mark lap as complete
            lap_trace.mark_complete(int(lap_time_ms))
            
            # Save to telemetry database
            await self.telemetry_repository.save_lap_trace(lap_trace)
            
            print(f"✅ Telemetry trace saved: Session={session_uid}, Lap={lap_number}, Samples={len(samples)}")
            
            return web.json_response({
                'status': 'success',
                'message': 'Telemetry trace submitted successfully',
                'trace_id': lap_trace.trace_id,
                'session_uid': session_uid,
                'lap_number': lap_number,
                'samples_count': len(samples)
            }, status=200)
        
        except Exception as e:
            self.logger.error(f"Error submitting telemetry trace: {e}")
            import traceback
            traceback.print_exc()
            return web.json_response(
                {'error': f'Failed to submit trace: {str(e)}'},
                status=500
            )
    
    async def _get_discord_username(self, user_id: str) -> str:
        """Get Discord username from user ID, with fallback to anonymous name."""
        try:
            if self.discord_bot and not self.discord_bot.is_closed():
                # Try to fetch user from Discord
                user = await self.discord_bot.fetch_user(int(user_id))
                if user:
                    # Use display name if available, otherwise username
                    return user.display_name or user.name
        except Exception as e:
            self.logger.warning(f"Could not fetch Discord user {user_id}: {e}")
        
        # Fallback: Use last 4 digits of user ID
        return f"Player_{user_id[-4:]}"

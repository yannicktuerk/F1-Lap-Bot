"""HTTP API server for receiving telemetry data from UDP listeners."""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from aiohttp import web, WSMsgType
from aiohttp.web import Request, Response
import aiohttp_cors

from src.application.use_cases.submit_lap_time_use_case import SubmitLapTimeUseCase
from src.domain.value_objects.lap_time import LapTime
from src.domain.value_objects.track import TrackName
from src.infrastructure.persistence.sqlite_lap_time_repository import SqliteLapTimeRepository
import discord


class TelemetryAPI:
    """HTTP API server for receiving telemetry data."""
    
    def __init__(self, lap_time_repository: SqliteLapTimeRepository, host: str = "0.0.0.0", port: int = 8080, discord_bot=None):
        self.host = host
        self.port = port
        self.lap_time_repository = lap_time_repository
        self.submit_use_case = SubmitLapTimeUseCase(lap_time_repository)
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
            
            # Extract required fields
            user_id = data.get('user_id')
            time_str = data.get('time')
            track_str = data.get('track') 
            source = data.get('source', 'telemetry')
            timestamp = data.get('timestamp')
            
            # Validate required fields
            if not user_id:
                return web.json_response(
                    {'error': 'Missing user_id field'},
                    status=400
                )
            
            if not time_str:
                return web.json_response(
                    {'error': 'Missing time field'},
                    status=400
                )
                
            if not track_str:
                return web.json_response(
                    {'error': 'Missing track field'},
                    status=400
                )
            
            # Get user info (we need username for the submission)
            username = await self._get_discord_username(user_id)
            
            try:
                # Parse time and track
                lap_time = LapTime.from_string(time_str)
                track_name = TrackName.from_string(track_str)
                
                # Submit the lap time using the use case
                result = self.submit_use_case.execute(
                    user_id=user_id,
                    username=username,
                    time=lap_time,
                    track=track_name
                )
                
                # Log successful submission
                self.logger.info(f"Telemetry lap submitted: {username} - {time_str} on {track_str}")
                print(f"📊 Telemetry lap received: {username} - {time_str} on {track_str}")
                
                # Return success response
                response_data = {
                    'status': 'success',
                    'message': 'Lap time submitted successfully',
                    'lap_id': result.lap_id,
                    'is_personal_best': result.is_personal_best,
                    'is_overall_best': result.is_overall_best,
                    'time': time_str,
                    'track': track_str,
                    'user_id': user_id,
                    'source': source,
                    'received_at': datetime.now().isoformat()
                }
                
                if result.is_personal_best:
                    response_data['improvement'] = 'Personal Best!'
                if result.is_overall_best:
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
            total_laps = len(self.lap_time_repository.get_all())
            
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

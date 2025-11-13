"""Value object for F1 25 telemetry sample data.

This module defines the TelemetrySample value object representing a single
telemetry data point captured from F1 25 UDP packets. Each sample contains
position, velocity, control inputs, and lap metadata at a specific timestamp.

F1 25 UDP Packet Mapping:
- PacketHeader: timestamp
- PacketMotionData / CarMotionData: position, velocity, g-forces, yaw
- PacketCarTelemetryData / CarTelemetryData: speed, throttle, brake, steer, gear, RPM, DRS
- PacketLapData / LapData: lap distance, lap number
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TelemetrySample:
    """Immutable value object representing a single F1 25 telemetry sample.
    
    This is the atomic unit of telemetry data containing all relevant information
    about the car's state at a specific point in time. Fields are directly mapped
    from F1 25 UDP specification to maintain traceability.
    
    Attributes:
        timestamp_ms (int): Session time in milliseconds.
            F1 25 UDP: PacketHeader.m_sessionTime
            
        world_position_x (float): World space X position in meters.
            F1 25 UDP: CarMotionData.m_worldPositionX
            
        world_position_y (float): World space Y position in meters.
            F1 25 UDP: CarMotionData.m_worldPositionY
            
        world_position_z (float): World space Z position in meters.
            F1 25 UDP: CarMotionData.m_worldPositionZ
            
        world_velocity_x (float): Velocity in world space X axis (m/s).
            F1 25 UDP: CarMotionData.m_worldVelocityX
            
        world_velocity_y (float): Velocity in world space Y axis (m/s).
            F1 25 UDP: CarMotionData.m_worldVelocityY
            
        world_velocity_z (float): Velocity in world space Z axis (m/s).
            F1 25 UDP: CarMotionData.m_worldVelocityZ
            
        g_force_lateral (float): Lateral G-force.
            F1 25 UDP: CarMotionData.m_gForceLateral
            
        g_force_longitudinal (float): Longitudinal G-force.
            F1 25 UDP: CarMotionData.m_gForceLongitudinal
            
        yaw (float): Yaw angle in radians.
            F1 25 UDP: CarMotionData.m_yaw
            
        speed (float): Speed in km/h.
            F1 25 UDP: CarTelemetryData.m_speed
            
        throttle (float): Throttle input (0.0 to 1.0).
            F1 25 UDP: CarTelemetryData.m_throttle
            
        steer (float): Steering input (-1.0 to 1.0, left to right).
            F1 25 UDP: CarTelemetryData.m_steer
            
        brake (float): Brake input (0.0 to 1.0).
            F1 25 UDP: CarTelemetryData.m_brake
            
        gear (int): Current gear (0 = neutral, 1-8 = gears, -1 = reverse).
            F1 25 UDP: CarTelemetryData.m_gear
            
        engine_rpm (int): Engine RPM.
            F1 25 UDP: CarTelemetryData.m_engineRPM
            
        drs (int): DRS status (0 = off, 1 = on).
            F1 25 UDP: CarTelemetryData.m_drs
            
        lap_distance (float): Distance around current lap in meters.
            F1 25 UDP: LapData.m_lapDistance
            
        lap_number (int): Current lap number.
            F1 25 UDP: LapData.m_currentLapNum
    """
    
    # Timestamp
    timestamp_ms: int
    
    # Position (world space)
    world_position_x: float
    world_position_y: float
    world_position_z: float
    
    # Velocity (world space)
    world_velocity_x: float
    world_velocity_y: float
    world_velocity_z: float
    
    # G-forces
    g_force_lateral: float
    g_force_longitudinal: float
    
    # Orientation
    yaw: float
    
    # Car telemetry
    speed: float
    throttle: float
    steer: float
    brake: float
    gear: int
    engine_rpm: int
    drs: int
    
    # Lap data
    lap_distance: float
    lap_number: int
    
    def __post_init__(self):
        """Validate telemetry sample fields after initialization.
        
        Raises:
            ValueError: If any field fails validation with descriptive error message.
        """
        # Timestamp validation
        if self.timestamp_ms < 0:
            raise ValueError(
                f"timestamp_ms must be non-negative, got {self.timestamp_ms}"
            )
        
        # Speed validation
        if self.speed < 0:
            raise ValueError(
                f"speed must be non-negative (km/h), got {self.speed}"
            )
        
        # Throttle validation (0.0 to 1.0)
        if not 0.0 <= self.throttle <= 1.0:
            raise ValueError(
                f"throttle must be in range [0.0, 1.0], got {self.throttle}"
            )
        
        # Brake validation (0.0 to 1.0)
        if not 0.0 <= self.brake <= 1.0:
            raise ValueError(
                f"brake must be in range [0.0, 1.0], got {self.brake}"
            )
        
        # Steering validation (-1.0 to 1.0)
        if not -1.0 <= self.steer <= 1.0:
            raise ValueError(
                f"steer must be in range [-1.0, 1.0], got {self.steer}"
            )
        
        # Gear validation (0 to 8, -1 for reverse)
        if self.gear < -1 or self.gear > 8:
            raise ValueError(
                f"gear must be in range [-1, 8] (reverse, neutral, gears 1-8), got {self.gear}"
            )
        
        # Engine RPM validation
        if self.engine_rpm < 0:
            raise ValueError(
                f"engine_rpm must be non-negative, got {self.engine_rpm}"
            )
        
        # DRS validation (0 or 1)
        if self.drs not in (0, 1):
            raise ValueError(
                f"drs must be 0 (off) or 1 (on), got {self.drs}"
            )
        
        # Lap distance validation
        if self.lap_distance < 0:
            raise ValueError(
                f"lap_distance must be non-negative (meters), got {self.lap_distance}"
            )
        
        # Lap number validation (must be at least 1)
        if self.lap_number < 1:
            raise ValueError(
                f"lap_number must be at least 1, got {self.lap_number}"
            )
    
    def __eq__(self, other) -> bool:
        """Check equality based on all field values.
        
        Args:
            other: Object to compare with.
            
        Returns:
            bool: True if all fields are equal, False otherwise.
        """
        if not isinstance(other, TelemetrySample):
            return False
        return (
            self.timestamp_ms == other.timestamp_ms
            and self.world_position_x == other.world_position_x
            and self.world_position_y == other.world_position_y
            and self.world_position_z == other.world_position_z
            and self.world_velocity_x == other.world_velocity_x
            and self.world_velocity_y == other.world_velocity_y
            and self.world_velocity_z == other.world_velocity_z
            and self.g_force_lateral == other.g_force_lateral
            and self.g_force_longitudinal == other.g_force_longitudinal
            and self.yaw == other.yaw
            and self.speed == other.speed
            and self.throttle == other.throttle
            and self.steer == other.steer
            and self.brake == other.brake
            and self.gear == other.gear
            and self.engine_rpm == other.engine_rpm
            and self.drs == other.drs
            and self.lap_distance == other.lap_distance
            and self.lap_number == other.lap_number
        )
    
    def __hash__(self) -> int:
        """Generate hash based on all field values.
        
        Returns:
            int: Hash value for this telemetry sample.
        """
        return hash((
            self.timestamp_ms,
            self.world_position_x,
            self.world_position_y,
            self.world_position_z,
            self.world_velocity_x,
            self.world_velocity_y,
            self.world_velocity_z,
            self.g_force_lateral,
            self.g_force_longitudinal,
            self.yaw,
            self.speed,
            self.throttle,
            self.steer,
            self.brake,
            self.gear,
            self.engine_rpm,
            self.drs,
            self.lap_distance,
            self.lap_number,
        ))

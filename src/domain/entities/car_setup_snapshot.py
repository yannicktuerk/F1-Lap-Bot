"""Domain entity representing a car setup snapshot from F1 25 telemetry.

This module defines the CarSetupSnapshot entity which captures the complete
car configuration at a specific moment, enabling setup tracking, comparison,
and correlation with lap performance.

F1 25 UDP Packet Mapping: PacketCarSetupData
"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime


class CarSetupSnapshot:
    """Rich domain entity for F1 25 car setup snapshots with validation and comparison.
    
    Represents a complete snapshot of car setup parameters captured from F1 25 UDP
    telemetry at a specific point in time. Entity identity is based on setup_id (UUID).
    
    Attributes:
        setup_id (str): Unique identifier for this setup snapshot (UUID).
        session_uid (str): Session identifier from F1 25 (links to session).
        timestamp_ms (int): Session time when snapshot was captured (milliseconds).
        
        front_wing (int): Front wing aero angle (F1 25: m_frontWing).
        rear_wing (int): Rear wing aero angle (F1 25: m_rearWing).
        
        on_throttle (int): Differential adjustment on throttle (F1 25: m_onThrottle).
        off_throttle (int): Differential adjustment off throttle (F1 25: m_offThrottle).
        
        front_camber (float): Front camber angle (F1 25: m_frontCamber).
        rear_camber (float): Rear camber angle (F1 25: m_rearCamber).
        front_toe (float): Front toe angle (F1 25: m_frontToe).
        rear_toe (float): Rear toe angle (F1 25: m_rearToe).
        
        front_suspension (int): Front suspension stiffness (F1 25: m_frontSuspension).
        rear_suspension (int): Rear suspension stiffness (F1 25: m_rearSuspension).
        front_anti_roll_bar (int): Front ARB stiffness (F1 25: m_frontAntiRollBar).
        rear_anti_roll_bar (int): Rear ARB stiffness (F1 25: m_rearAntiRollBar).
        front_suspension_height (int): Front ride height (F1 25: m_frontSuspensionHeight).
        rear_suspension_height (int): Rear ride height (F1 25: m_rearSuspensionHeight).
        
        brake_pressure (int): Brake pressure percentage (F1 25: m_brakePressure).
        brake_bias (int): Front/rear brake balance (F1 25: m_brakeBias).
        engine_braking (int): Engine braking setting (F1 25: m_engineBraking).
        
        front_left_tyre_pressure (float): FL tyre PSI (F1 25: m_frontLeftTyrePressure).
        front_right_tyre_pressure (float): FR tyre PSI (F1 25: m_frontRightTyrePressure).
        rear_left_tyre_pressure (float): RL tyre PSI (F1 25: m_rearLeftTyrePressure).
        rear_right_tyre_pressure (float): RR tyre PSI (F1 25: m_rearRightTyrePressure).
        
        ballast (int): Ballast weight (F1 25: m_ballast).
        fuel_load (float): Starting fuel load in kg (F1 25: m_fuelLoad).
        
        setup_schema_version (int): Schema version for future compatibility.
        created_at (datetime): When this snapshot was created in the system.
    """
    
    # Schema version for future compatibility
    CURRENT_SCHEMA_VERSION = 1
    
    # Valid parameter ranges (from F1 25 game limits)
    WING_ANGLE_MIN = 0
    WING_ANGLE_MAX = 50
    DIFF_MIN = 0
    DIFF_MAX = 100
    SUSPENSION_MIN = 1
    SUSPENSION_MAX = 11
    ARB_MIN = 1
    ARB_MAX = 11
    SUSPENSION_HEIGHT_MIN = 0
    SUSPENSION_HEIGHT_MAX = 10
    BRAKE_PRESSURE_MIN = 50
    BRAKE_PRESSURE_MAX = 120
    BRAKE_BIAS_MIN = 50
    BRAKE_BIAS_MAX = 70
    ENGINE_BRAKING_MIN = 0
    ENGINE_BRAKING_MAX = 100
    TYRE_PRESSURE_MIN = 19.0
    TYRE_PRESSURE_MAX = 30.0
    BALLAST_MIN = 0
    BALLAST_MAX = 50
    FUEL_LOAD_MIN = 0.0
    FUEL_LOAD_MAX = 110.0
    
    def __init__(
        self,
        session_uid: str,
        timestamp_ms: int,
        # Aerodynamics
        front_wing: int,
        rear_wing: int,
        # Differential
        on_throttle: int,
        off_throttle: int,
        # Camber & Toe
        front_camber: float,
        rear_camber: float,
        front_toe: float,
        rear_toe: float,
        # Suspension
        front_suspension: int,
        rear_suspension: int,
        front_anti_roll_bar: int,
        rear_anti_roll_bar: int,
        front_suspension_height: int,
        rear_suspension_height: int,
        # Brakes
        brake_pressure: int,
        brake_bias: int,
        engine_braking: int,
        # Tyres
        front_left_tyre_pressure: float,
        front_right_tyre_pressure: float,
        rear_left_tyre_pressure: float,
        rear_right_tyre_pressure: float,
        # Weight
        ballast: int,
        fuel_load: float,
        # Optional parameters
        setup_id: Optional[str] = None,
        setup_schema_version: int = CURRENT_SCHEMA_VERSION,
        created_at: Optional[datetime] = None,
    ):
        """Initialize car setup snapshot with validation.
        
        Args:
            session_uid: F1 25 session unique identifier.
            timestamp_ms: Session time when snapshot was taken (ms).
            All other parameters: See class docstring for details.
            
        Raises:
            ValueError: If any parameter is outside valid range.
        """
        # Entity identity
        self._setup_id = setup_id or str(uuid.uuid4())
        self._session_uid = session_uid
        self._timestamp_ms = timestamp_ms
        self._created_at = created_at or datetime.utcnow()
        self._setup_schema_version = setup_schema_version
        
        # Validate and assign aerodynamics
        self._validate_wing_angle("front_wing", front_wing)
        self._validate_wing_angle("rear_wing", rear_wing)
        self._front_wing = front_wing
        self._rear_wing = rear_wing
        
        # Validate and assign differential
        self._validate_differential("on_throttle", on_throttle)
        self._validate_differential("off_throttle", off_throttle)
        self._on_throttle = on_throttle
        self._off_throttle = off_throttle
        
        # Assign camber & toe (ranges vary, stored as-is from telemetry)
        self._front_camber = front_camber
        self._rear_camber = rear_camber
        self._front_toe = front_toe
        self._rear_toe = rear_toe
        
        # Validate and assign suspension
        self._validate_suspension("front_suspension", front_suspension)
        self._validate_suspension("rear_suspension", rear_suspension)
        self._validate_arb("front_anti_roll_bar", front_anti_roll_bar)
        self._validate_arb("rear_anti_roll_bar", rear_anti_roll_bar)
        self._validate_suspension_height("front_suspension_height", front_suspension_height)
        self._validate_suspension_height("rear_suspension_height", rear_suspension_height)
        self._front_suspension = front_suspension
        self._rear_suspension = rear_suspension
        self._front_anti_roll_bar = front_anti_roll_bar
        self._rear_anti_roll_bar = rear_anti_roll_bar
        self._front_suspension_height = front_suspension_height
        self._rear_suspension_height = rear_suspension_height
        
        # Validate and assign brakes
        self._validate_brake_pressure(brake_pressure)
        self._validate_brake_bias(brake_bias)
        self._validate_engine_braking(engine_braking)
        self._brake_pressure = brake_pressure
        self._brake_bias = brake_bias
        self._engine_braking = engine_braking
        
        # Validate and assign tyre pressures
        self._validate_tyre_pressure("front_left_tyre_pressure", front_left_tyre_pressure)
        self._validate_tyre_pressure("front_right_tyre_pressure", front_right_tyre_pressure)
        self._validate_tyre_pressure("rear_left_tyre_pressure", rear_left_tyre_pressure)
        self._validate_tyre_pressure("rear_right_tyre_pressure", rear_right_tyre_pressure)
        self._front_left_tyre_pressure = front_left_tyre_pressure
        self._front_right_tyre_pressure = front_right_tyre_pressure
        self._rear_left_tyre_pressure = rear_left_tyre_pressure
        self._rear_right_tyre_pressure = rear_right_tyre_pressure
        
        # Validate and assign weight
        self._validate_ballast(ballast)
        self._validate_fuel_load(fuel_load)
        self._ballast = ballast
        self._fuel_load = fuel_load
    
    # Validation methods
    
    def _validate_wing_angle(self, field_name: str, value: int) -> None:
        if not self.WING_ANGLE_MIN <= value <= self.WING_ANGLE_MAX:
            raise ValueError(
                f"{field_name} must be in range [{self.WING_ANGLE_MIN}, {self.WING_ANGLE_MAX}], got {value}"
            )
    
    def _validate_differential(self, field_name: str, value: int) -> None:
        if not self.DIFF_MIN <= value <= self.DIFF_MAX:
            raise ValueError(
                f"{field_name} must be in range [{self.DIFF_MIN}, {self.DIFF_MAX}], got {value}"
            )
    
    def _validate_suspension(self, field_name: str, value: int) -> None:
        if not self.SUSPENSION_MIN <= value <= self.SUSPENSION_MAX:
            raise ValueError(
                f"{field_name} must be in range [{self.SUSPENSION_MIN}, {self.SUSPENSION_MAX}], got {value}"
            )
    
    def _validate_arb(self, field_name: str, value: int) -> None:
        if not self.ARB_MIN <= value <= self.ARB_MAX:
            raise ValueError(
                f"{field_name} must be in range [{self.ARB_MIN}, {self.ARB_MAX}], got {value}"
            )
    
    def _validate_suspension_height(self, field_name: str, value: int) -> None:
        if not self.SUSPENSION_HEIGHT_MIN <= value <= self.SUSPENSION_HEIGHT_MAX:
            raise ValueError(
                f"{field_name} must be in range [{self.SUSPENSION_HEIGHT_MIN}, {self.SUSPENSION_HEIGHT_MAX}], got {value}"
            )
    
    def _validate_brake_pressure(self, value: int) -> None:
        if not self.BRAKE_PRESSURE_MIN <= value <= self.BRAKE_PRESSURE_MAX:
            raise ValueError(
                f"brake_pressure must be in range [{self.BRAKE_PRESSURE_MIN}, {self.BRAKE_PRESSURE_MAX}], got {value}"
            )
    
    def _validate_brake_bias(self, value: int) -> None:
        if not self.BRAKE_BIAS_MIN <= value <= self.BRAKE_BIAS_MAX:
            raise ValueError(
                f"brake_bias must be in range [{self.BRAKE_BIAS_MIN}, {self.BRAKE_BIAS_MAX}], got {value}"
            )
    
    def _validate_engine_braking(self, value: int) -> None:
        if not self.ENGINE_BRAKING_MIN <= value <= self.ENGINE_BRAKING_MAX:
            raise ValueError(
                f"engine_braking must be in range [{self.ENGINE_BRAKING_MIN}, {self.ENGINE_BRAKING_MAX}], got {value}"
            )
    
    def _validate_tyre_pressure(self, field_name: str, value: float) -> None:
        if not self.TYRE_PRESSURE_MIN <= value <= self.TYRE_PRESSURE_MAX:
            raise ValueError(
                f"{field_name} must be in range [{self.TYRE_PRESSURE_MIN}, {self.TYRE_PRESSURE_MAX}] PSI, got {value}"
            )
    
    def _validate_ballast(self, value: int) -> None:
        if not self.BALLAST_MIN <= value <= self.BALLAST_MAX:
            raise ValueError(
                f"ballast must be in range [{self.BALLAST_MIN}, {self.BALLAST_MAX}] kg, got {value}"
            )
    
    def _validate_fuel_load(self, value: float) -> None:
        if not self.FUEL_LOAD_MIN <= value <= self.FUEL_LOAD_MAX:
            raise ValueError(
                f"fuel_load must be in range [{self.FUEL_LOAD_MIN}, {self.FUEL_LOAD_MAX}] kg, got {value}"
            )
    
    # Properties (read-only access to internal state)
    
    @property
    def setup_id(self) -> str:
        return self._setup_id
    
    @property
    def session_uid(self) -> str:
        return self._session_uid
    
    @property
    def timestamp_ms(self) -> int:
        return self._timestamp_ms
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def setup_schema_version(self) -> int:
        return self._setup_schema_version
    
    # Aerodynamics
    @property
    def front_wing(self) -> int:
        return self._front_wing
    
    @property
    def rear_wing(self) -> int:
        return self._rear_wing
    
    # Differential
    @property
    def on_throttle(self) -> int:
        return self._on_throttle
    
    @property
    def off_throttle(self) -> int:
        return self._off_throttle
    
    # Camber & Toe
    @property
    def front_camber(self) -> float:
        return self._front_camber
    
    @property
    def rear_camber(self) -> float:
        return self._rear_camber
    
    @property
    def front_toe(self) -> float:
        return self._front_toe
    
    @property
    def rear_toe(self) -> float:
        return self._rear_toe
    
    # Suspension
    @property
    def front_suspension(self) -> int:
        return self._front_suspension
    
    @property
    def rear_suspension(self) -> int:
        return self._rear_suspension
    
    @property
    def front_anti_roll_bar(self) -> int:
        return self._front_anti_roll_bar
    
    @property
    def rear_anti_roll_bar(self) -> int:
        return self._rear_anti_roll_bar
    
    @property
    def front_suspension_height(self) -> int:
        return self._front_suspension_height
    
    @property
    def rear_suspension_height(self) -> int:
        return self._rear_suspension_height
    
    # Brakes
    @property
    def brake_pressure(self) -> int:
        return self._brake_pressure
    
    @property
    def brake_bias(self) -> int:
        return self._brake_bias
    
    @property
    def engine_braking(self) -> int:
        return self._engine_braking
    
    # Tyres
    @property
    def front_left_tyre_pressure(self) -> float:
        return self._front_left_tyre_pressure
    
    @property
    def front_right_tyre_pressure(self) -> float:
        return self._front_right_tyre_pressure
    
    @property
    def rear_left_tyre_pressure(self) -> float:
        return self._rear_left_tyre_pressure
    
    @property
    def rear_right_tyre_pressure(self) -> float:
        return self._rear_right_tyre_pressure
    
    # Weight
    @property
    def ballast(self) -> int:
        return self._ballast
    
    @property
    def fuel_load(self) -> float:
        return self._fuel_load
    
    # Business logic methods
    
    def compare_to(self, other: 'CarSetupSnapshot') -> Dict[str, Dict[str, Any]]:
        """Compare this setup to another and return differences.
        
        Args:
            other: Another CarSetupSnapshot to compare against.
            
        Returns:
            Dictionary with field names as keys and difference details as values.
            Only fields that differ are included. Each difference contains:
            - 'this': Value in this setup
            - 'other': Value in other setup
            - 'diff': Numeric difference (this - other) if applicable
            
        Raises:
            ValueError: If other is not a CarSetupSnapshot.
        """
        if not isinstance(other, CarSetupSnapshot):
            raise ValueError("Can only compare with another CarSetupSnapshot")
        
        differences = {}
        
        # Compare all setup parameters
        fields = [
            ("front_wing", self._front_wing, other._front_wing),
            ("rear_wing", self._rear_wing, other._rear_wing),
            ("on_throttle", self._on_throttle, other._on_throttle),
            ("off_throttle", self._off_throttle, other._off_throttle),
            ("front_camber", self._front_camber, other._front_camber),
            ("rear_camber", self._rear_camber, other._rear_camber),
            ("front_toe", self._front_toe, other._front_toe),
            ("rear_toe", self._rear_toe, other._rear_toe),
            ("front_suspension", self._front_suspension, other._front_suspension),
            ("rear_suspension", self._rear_suspension, other._rear_suspension),
            ("front_anti_roll_bar", self._front_anti_roll_bar, other._front_anti_roll_bar),
            ("rear_anti_roll_bar", self._rear_anti_roll_bar, other._rear_anti_roll_bar),
            ("front_suspension_height", self._front_suspension_height, other._front_suspension_height),
            ("rear_suspension_height", self._rear_suspension_height, other._rear_suspension_height),
            ("brake_pressure", self._brake_pressure, other._brake_pressure),
            ("brake_bias", self._brake_bias, other._brake_bias),
            ("engine_braking", self._engine_braking, other._engine_braking),
            ("front_left_tyre_pressure", self._front_left_tyre_pressure, other._front_left_tyre_pressure),
            ("front_right_tyre_pressure", self._front_right_tyre_pressure, other._front_right_tyre_pressure),
            ("rear_left_tyre_pressure", self._rear_left_tyre_pressure, other._rear_left_tyre_pressure),
            ("rear_right_tyre_pressure", self._rear_right_tyre_pressure, other._rear_right_tyre_pressure),
            ("ballast", self._ballast, other._ballast),
            ("fuel_load", self._fuel_load, other._fuel_load),
        ]
        
        for field_name, this_value, other_value in fields:
            if this_value != other_value:
                differences[field_name] = {
                    "this": this_value,
                    "other": other_value,
                    "diff": this_value - other_value if isinstance(this_value, (int, float)) else None
                }
        
        return differences
    
    def __eq__(self, other) -> bool:
        """Entity equality based on setup_id (identity)."""
        if not isinstance(other, CarSetupSnapshot):
            return False
        return self._setup_id == other._setup_id
    
    def __hash__(self) -> int:
        """Hash based on entity identity (setup_id)."""
        return hash(self._setup_id)
    
    def __str__(self) -> str:
        return f"CarSetupSnapshot(id={self._setup_id[:8]}, session={self._session_uid}, timestamp={self._timestamp_ms}ms)"
    
    def __repr__(self) -> str:
        return (
            f"CarSetupSnapshot(setup_id='{self._setup_id}', session_uid={self._session_uid}, "
            f"timestamp_ms={self._timestamp_ms}, front_wing={self._front_wing}, rear_wing={self._rear_wing})"
        )

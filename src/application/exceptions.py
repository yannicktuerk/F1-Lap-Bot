"""Custom exceptions for application layer use cases.

These exceptions represent application-specific error conditions that occur
during use case execution. They are part of the application layer and should
be caught and handled appropriately in the presentation layer.
"""


class SessionNotFoundError(Exception):
    """Raised when a requested session does not exist in the telemetry database.
    
    This typically occurs when:
    - User requests track reconstruction for a non-existent session
    - Session UID is invalid or hasn't been persisted yet
    - Session was deleted or expired
    
    Args:
        session_uid: The session UID that was not found.
        message: Optional custom error message.
    
    Example:
        >>> raise SessionNotFoundError(12345)
        SessionNotFoundError: Session with UID 12345 not found
    """
    
    def __init__(self, session_uid: int, message: str = None):
        self.session_uid = session_uid
        if message is None:
            message = f"Session with UID {session_uid} not found"
        super().__init__(message)


class InsufficientDataError(Exception):
    """Raised when insufficient telemetry data is available for an operation.
    
    This typically occurs when:
    - Not enough laps recorded to perform track reconstruction
    - Not enough telemetry samples in a lap for analysis
    - Data quality is too poor for reliable computation
    
    Args:
        required: Minimum amount of data required.
        actual: Actual amount of data available.
        data_type: Type of data that is insufficient (e.g., "laps", "samples").
        message: Optional custom error message.
    
    Example:
        >>> raise InsufficientDataError(required=3, actual=1, data_type="laps")
        InsufficientDataError: Insufficient laps: need at least 3, got 1
    """
    
    def __init__(
        self,
        required: int,
        actual: int,
        data_type: str = "data points",
        message: str = None
    ):
        self.required = required
        self.actual = actual
        self.data_type = data_type
        
        if message is None:
            message = (
                f"Insufficient {data_type}: need at least {required}, got {actual}"
            )
        super().__init__(message)


class InvalidTrackDataError(Exception):
    """Raised when track data is invalid or corrupted.
    
    This typically occurs when:
    - Track length is invalid (zero or negative)
    - Track ID is missing or invalid
    - Telemetry samples contain invalid position data
    
    Args:
        field: The invalid field name.
        value: The invalid value.
        message: Optional custom error message.
    
    Example:
        >>> raise InvalidTrackDataError("track_length_m", 0)
        InvalidTrackDataError: Invalid track data: track_length_m = 0
    """
    
    def __init__(self, field: str, value: any, message: str = None):
        self.field = field
        self.value = value
        
        if message is None:
            message = f"Invalid track data: {field} = {value}"
        super().__init__(message)


class LapNotFoundError(Exception):
    """Raised when a requested lap does not exist in the telemetry database.
    
    This typically occurs when:
    - User requests analysis for a non-existent lap number
    - No laps recorded yet in the session
    - Lap was deleted or invalidated
    
    Args:
        message: Error message describing which lap was not found.
    
    Example:
        >>> raise LapNotFoundError("No lap found for session 12345")
        LapNotFoundError: No lap found for session 12345
    """
    
    def __init__(self, message: str):
        super().__init__(message)

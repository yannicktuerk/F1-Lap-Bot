"""Configuration settings for slip indicators and safety ampels."""

# Slip ampel thresholds (from coaching specification example)
SLIP_AMPEL_CONFIG = {
    "entry": {
        "green_max": 0.6,    # Green zone: 0.0 to 0.6
        "yellow_max": 0.85   # Yellow zone: 0.6 to 0.85, Red: 0.85 to 1.0
    },
    "rotation": {
        "green_max": 0.6,
        "yellow_max": 0.85
    },
    "exit": {
        "green_max": 0.6,
        "yellow_max": 0.85
    }
}

# Detection thresholds for specific conditions
DETECTION_THRESHOLDS = {
    "wheelspin_slip_ratio": 0.15,     # Slip ratio threshold for wheelspin detection
    "understeer_slip_angle": 0.05,    # Slip angle difference for understeer (radians)
    "oversteer_slip_angle": 0.05,     # Slip angle difference for oversteer (radians)
    "extreme_slip_ratio": 1.0,        # Threshold for extreme slip ratios
    "extreme_slip_angle": 0.5         # Threshold for extreme slip angles (radians)
}

# Slip calculation parameters
SLIP_CALCULATION_CONFIG = {
    "longitudinal_normalization": 0.3,  # Typical racing slip ratio range for normalization
    "lateral_normalization": 0.2,       # Typical racing slip angle range (radians) for normalization  
    "minimum_confidence": 0.1,          # Minimum confidence level for assessments
    "speed_confidence_threshold": 10.0   # Speed below which confidence is reduced (km/h)
}
"""
Configuration settings for the Hand Mimic System.
"""

# MediaPipe configuration
MEDIAPIPE_CONFIG = {
    'static_image_mode': False,
    'max_num_hands': 1,  # Only detect one hand
    'min_detection_confidence': 0.7,
    'min_tracking_confidence': 0.5
}

# Serial communication settings
DEFAULT_SERIAL_PORT = '/dev/ttyUSB0'
DEFAULT_BAUDRATE = 115200
SERIAL_TIMEOUT = 1

# Finger angle settings
# Default threshold values (modify with calibration)
FINGER_ANGLE_RANGES = {
    'thumb_mcp': (154.0, 180.0),
    'thumb_ip': (122.4, 180.0),
    'index': (11.5, 180.0),
    'middle': (10.8, 180.0),
    'ring': (13.8, 177.6),
    'pinky': (24.9, 174.1),
}

# Smoothing and update settings
SMOOTH_FACTOR = 0.7  # Higher value = smoother movement, more lag
UPDATE_INTERVAL = 2  # Update every N frames
ANGLE_UPDATE_THRESHOLD = 5  # Minimum angle change to trigger an update
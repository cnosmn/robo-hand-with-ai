"""
Finger angle calculation module.
"""
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

class AngleCalculator:
    """
    Class for calculating finger angles from hand landmarks.
    """
    def __init__(self, angle_ranges: Dict[str, Tuple[float, float]], smooth_factor: float = 0.7):
        """
        Initialize the angle calculator.
        
        Args:
            angle_ranges: Dictionary of min/max angles for each finger
            smooth_factor: Smoothing factor for angle transitions
        """
        self.angle_ranges = angle_ranges
        self.smooth_factor = smooth_factor
        self.prev_angles = None
    
    def calculate_raw_angles(self, landmarks) -> Dict[str, float]:
        """
        Calculate raw angles for each finger joint (for calibration).
        
        Args:
            landmarks: Hand landmarks from MediaPipe
            
        Returns:
            Dictionary of raw angles for each finger
        """
        # Thumb angles
        thumb_mcp_angle = self._calculate_angle(landmarks[1], landmarks[2], landmarks[3])
        thumb_ip_angle = self._calculate_angle(landmarks[2], landmarks[3], landmarks[4])
        
        # Other finger angles
        index_angle = self._calculate_angle(landmarks[5], landmarks[6], landmarks[8])
        middle_angle = self._calculate_angle(landmarks[9], landmarks[10], landmarks[12])
        ring_angle = self._calculate_angle(landmarks[13], landmarks[14], landmarks[16])
        pinky_angle = self._calculate_angle(landmarks[17], landmarks[18], landmarks[20])
        
        return {
            'thumb_mcp': thumb_mcp_angle,
            'thumb_ip': thumb_ip_angle, 
            'index': index_angle,
            'middle': middle_angle,
            'ring': ring_angle,
            'pinky': pinky_angle
        }
    
    def calculate_servo_angles(self, landmarks) -> Dict[str, int]:
        """
        Calculate servo angles for each finger.
        
        Args:
            landmarks: Hand landmarks from MediaPipe
            
        Returns:
            Dictionary of servo angles for each finger
        """
        # Calculate raw angles
        raw_angles = self.calculate_raw_angles(landmarks)
        
        # Convert angles to servo range (0-180 degrees)
        servo_angles = {}
        for finger, angle in raw_angles.items():
            if finger.startswith('thumb'):
                # Başparmak için ters haritalama (180-0 yerine 0-180)
                servo_angles[finger] = self._map_to_servo_angle_thumb(angle, finger)
            else:
                # Diğer parmaklar için normal haritalama
                servo_angles[finger] = self._map_to_servo_angle(angle, finger)
        
        # Apply smoothing if previous angles exist
        if self.prev_angles is not None:
            for key in servo_angles:
                servo_angles[key] = int(
                    self.smooth_factor * self.prev_angles[key] + 
                    (1 - self.smooth_factor) * servo_angles[key]
                )
        
        # Store current angles for next calculation
        self.prev_angles = servo_angles.copy()
        return servo_angles
    
    def _calculate_angle(self, a, b, c) -> float:
        """
        Calculate angle between three points.
        
        Args:
            a, b, c: Three points (MediaPipe landmarks)
            
        Returns:
            Angle in degrees
        """
        a = np.array([a.x, a.y])
        b = np.array([b.x, b.y])
        c = np.array([c.x, c.y])
        
        # Calculate vectors
        ba = a - b
        bc = c - b
        
        # Calculate angle (radians)
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        
        # Convert radians to degrees
        return np.degrees(angle)
    
    def _map_to_servo_angle(self, angle: float, finger_type: str) -> int:
        """
        Map calculated angle to servo motor angle for regular fingers.
        
        Args:
            angle: Raw angle in degrees
            finger_type: Type of finger
            
        Returns:
            Mapped angle (0-180 degrees)
        """
        # Get threshold values for the specified finger
        min_angle, max_angle = self.angle_ranges.get(finger_type, (120, 170))
        
        # Map angle to 0-180 range (180 = fully open, 0 = closed)
        # Note: Normally angle increases as finger closes, so we invert the mapping
        mapped_angle = int(np.interp(angle, [min_angle, max_angle], [180, 0]))
        
        # Constrain to valid range
        return max(0, min(mapped_angle, 180))
    
    def _map_to_servo_angle_thumb(self, angle: float, finger_type: str) -> int:
        """
        Map calculated angle to servo motor angle for thumb.
        Reverses the mapping direction compared to other fingers.
        
        Args:
            angle: Raw angle in degrees
            finger_type: Type of finger ('thumb_mcp' or 'thumb_ip')
            
        Returns:
            Mapped angle (0-180 degrees)
        """
        # Get threshold values for the specified finger
        min_angle, max_angle = self.angle_ranges.get(finger_type, (120, 170))
        
        # Map angle to 0-180 range but with REVERSED mapping (0 = fully open, 180 = closed)
        # This is the opposite of other fingers
        mapped_angle = int(np.interp(angle, [min_angle, max_angle], [0, 180]))
        
        # Constrain to valid range
        return max(0, min(mapped_angle, 180))
"""
Visualization module for hand tracking.
"""
import cv2
from typing import Dict, List, Optional, Tuple

class Renderer:
    """
    Class for visualization of hand tracking.
    """
    def __init__(self):
        """
        Initialize the renderer.
        """
        self.window_name = 'Real-Time Hand Tracking'
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
    
    def render_frame(self, frame, finger_angles: Optional[Dict[str, int]] = None, hand_detected: bool = True):
        """
        Render a frame with angle information.
        
        Args:
            frame: Camera frame
            finger_angles: Dictionary of finger angles
            hand_detected: Flag indicating if hand was detected
            
        Returns:
            Processed frame
        """
        # If hand not detected, show warning
        if not hand_detected:
            cv2.putText(
                frame, 
                "Hand not detected", 
                (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                (0, 0, 255), 
                2
            )
            return frame
        
        # Display finger angles if available
        if finger_angles:
            y_pos = 30
            for finger, angle in finger_angles.items():
                cv2.putText(
                    frame, 
                    f"{finger}: {angle}", 
                    (10, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, 
                    (0, 255, 0), 
                    1
                )
                y_pos += 25
        
        return frame
    
    def display_frame(self, frame):
        """
        Display a frame in the window.
        
        Args:
            frame: Camera frame
        """
        cv2.imshow(self.window_name, frame)
    
    def get_key(self) -> int:
        """
        Get a keypress.
        
        Returns:
            Key code
        """
        return cv2.waitKey(1) & 0xFF
    
    def close(self):
        """
        Close all windows.
        """
        cv2.destroyAllWindows()
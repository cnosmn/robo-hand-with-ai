"""
Hand detection module using MediaPipe.
"""
import cv2
import mediapipe as mp
from typing import Tuple, Dict, Optional, List

class HandDetector:
    """
    Class for detecting hands and landmarks using MediaPipe.
    """
    def __init__(self, config: Dict):
        """
        Initialize the MediaPipe hand detection module.
        
        Args:
            config (Dict): Configuration parameters for MediaPipe Hands
        """
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=config['static_image_mode'],
            max_num_hands=config['max_num_hands'],
            min_detection_confidence=config['min_detection_confidence'],
            min_tracking_confidence=config['min_tracking_confidence']
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
    
    def detect_hands(self, frame):
        """
        Detect hands in the frame.
        
        Args:
            frame: Camera frame in BGR format
            
        Returns:
            Detection results from MediaPipe
        """
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame for hand detection
        return self.hands.process(frame_rgb)
    
    def draw_landmarks(self, frame, multi_hand_landmarks):
        """
        Draw hand landmarks on the frame.
        
        Args:
            frame: Camera frame
            multi_hand_landmarks: Hand landmarks from MediaPipe
            
        Returns:
            Frame with landmarks drawn
        """
        for hand_landmarks in multi_hand_landmarks:
            self.mp_drawing.draw_landmarks(
                frame, 
                hand_landmarks, 
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_drawing_styles.get_default_hand_landmarks_style(),
                self.mp_drawing_styles.get_default_hand_connections_style()
            )
        return frame
    
    def close(self):
        """
        Release resources.
        """
        self.hands.close()
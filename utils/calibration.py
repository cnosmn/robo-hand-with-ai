"""
Calibration module for hand tracking system.
"""
import cv2
import time
from typing import Dict, Tuple

class CalibrationSystem:
    """
    System for calibrating finger angle ranges.
    """
    def __init__(self, hand_detector, angle_calculator):
        """
        Initialize calibration system.
        
        Args:
            hand_detector: HandDetector instance
            angle_calculator: AngleCalculator instance
        """
        self.hand_detector = hand_detector
        self.angle_calculator = angle_calculator
        self.window_name = 'Calibration Mode'
        
        # Min/max angles for each finger
        self.min_angles = {
            'thumb_mcp': 180, 'thumb_ip': 180, 'index': 180, 
            'middle': 180, 'ring': 180, 'pinky': 180
        }
        self.max_angles = {
            'thumb_mcp': 0, 'thumb_ip': 0, 'index': 0, 
            'middle': 0, 'ring': 0, 'pinky': 0
        }
    
    def run(self):
        """
        Run calibration mode.
        """
        print("\n=== CALIBRATION MODE ===")
        print("Open and close each finger fully to calibrate angle ranges")
        print("Press SPACE to start/pause, press S to save, press Q to quit")
        
        # Start camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Could not open camera!")
            return
            
        calibrating = False
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Cannot capture frame!")
                break
            
            # Detect hands
            results = self.hand_detector.detect_hands(frame)
            
            # Check if calibration is active
            status_text = "ACTIVE" if calibrating else "PAUSED - Press SPACE to start"
            cv2.putText(
                frame, 
                f"Calibration: {status_text}", 
                (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                (0, 0, 255), 
                2
            )
            
            # If hands detected and calibration active
            if calibrating and results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw landmarks
                    self.hand_detector.draw_landmarks(frame, [hand_landmarks])
                    
                    # Calculate raw angles (without mapping)
                    landmarks = hand_landmarks.landmark
                    raw_angles = self.angle_calculator.calculate_raw_angles(landmarks)
                    
                    # Update min and max values
                    for key, value in raw_angles.items():
                        if value < self.min_angles[key]:
                            self.min_angles[key] = value
                        if value > self.max_angles[key]:
                            self.max_angles[key] = value
                    
                    # Display angles on frame
                    y_pos = 60
                    for finger, angle in raw_angles.items():
                        cv2.putText(
                            frame, 
                            f"{finger}: {angle:.1f} | Min: {self.min_angles[finger]:.1f}, Max: {self.max_angles[finger]:.1f}", 
                            (10, y_pos), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.5, 
                            (0, 255, 0), 
                            1
                        )
                        y_pos += 25
            
            # Show frame
            cv2.imshow(self.window_name, frame)
            
            # Key controls
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' '):  # Space key
                calibrating = not calibrating
                if calibrating:
                    print("Calibration started - fully open and close your hand")
                else:
                    print("Calibration paused")
            elif key == ord('s'):  # Save
                self._save_calibration_results()
        
        # Release resources
        cap.release()
        cv2.destroyAllWindows()
        
        return self.min_angles, self.max_angles
    
    def _save_calibration_results(self):
        """
        Print calibration results.
        """
        print("\nCALIBRATION RESULTS:")
        for finger in self.min_angles.keys():
            print(f"{finger}: Min={self.min_angles[finger]:.1f}, Max={self.max_angles[finger]:.1f}")
        
        print("\nCopy these values to the settings.py file in the FINGER_ANGLE_RANGES dictionary")
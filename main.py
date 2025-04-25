#!/usr/bin/env python3
"""
Real-Time Hand Mimicking System

This program detects hand movements using a webcam and replicates them with
a robotic hand connected to an Arduino.
"""
import argparse
import cv2
import time
from typing import Dict, Optional, Tuple

# Import project modules
from config.settings import (
    MEDIAPIPE_CONFIG, 
    DEFAULT_SERIAL_PORT, 
    DEFAULT_BAUDRATE, 
    SERIAL_TIMEOUT,
    FINGER_ANGLE_RANGES, 
    SMOOTH_FACTOR, 
    UPDATE_INTERVAL, 
    ANGLE_UPDATE_THRESHOLD
)
from hand_tracking import HandDetector, AngleCalculator
from serial_comm import ArduinoInterface
from utils import CalibrationSystem
from visualization import Renderer

class RealTimeHandMimicSystem:
    """
    Main class for the hand mimicking system.
    """
    def __init__(self, port: str = DEFAULT_SERIAL_PORT, baudrate: int = DEFAULT_BAUDRATE):
        """
        Initialize the hand mimicking system.
        
        Args:
            port: Serial port for Arduino
            baudrate: Baud rate for serial communication
        """
        # Initialize hand tracking components
        self.hand_detector = HandDetector(MEDIAPIPE_CONFIG)
        self.angle_calculator = AngleCalculator(FINGER_ANGLE_RANGES, SMOOTH_FACTOR)
        
        # Initialize Arduino communication
        self.arduino = ArduinoInterface(port, baudrate, SERIAL_TIMEOUT)
        
        # Initialize visualization
        self.renderer = Renderer()
        
        # Initialize frame counter
        self.frame_counter = 0
    
    def process_frame(self, frame):
        """
        Process a camera frame.
        
        Args:
            frame: Camera frame
            
        Returns:
            Processed frame
        """
        # Detect hands
        results = self.hand_detector.detect_hands(frame)
        
        # Check if hand was detected
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks on frame
                self.hand_detector.draw_landmarks(frame, [hand_landmarks])
                
                # Calculate finger angles
                landmarks = hand_landmarks.landmark
                finger_angles = self.angle_calculator.calculate_servo_angles(landmarks)
                
                # Send angles to Arduino
                self.arduino.send_finger_angles(
                    finger_angles, 
                    UPDATE_INTERVAL, 
                    ANGLE_UPDATE_THRESHOLD
                )
                
                # Render angles on frame
                frame = self.renderer.render_frame(frame, finger_angles, True)
                
                # Only process the first hand
                break
        else:
            # No hand detected
            frame = self.renderer.render_frame(frame, None, False)
        
        return frame
    
    def run_calibration_mode(self):
        """
        Run calibration mode.
        """
        calibration_system = CalibrationSystem(self.hand_detector, self.angle_calculator)
        min_angles, max_angles = calibration_system.run()
        
        # Print results
        print("\nCalibration complete. Update the settings.py file with these values:")
        print("FINGER_ANGLE_RANGES = {")
        for finger in min_angles.keys():
            print(f"    '{finger}': ({min_angles[finger]:.1f}, {max_angles[finger]:.1f}),")
        print("}")
    
    def run(self):
        """
        Run the hand mimicking system.
        """
        print("\n=== REAL-TIME HAND MIMICKING SYSTEM ===")
        print("Press Q to quit")
        
        # Start camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Could not open camera!")
            return
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Cannot capture frame!")
                break
            
            # Process frame
            processed_frame = self.process_frame(frame)
            
            # Display frame
            self.renderer.display_frame(processed_frame)
            
            # Check for exit key
            if self.renderer.get_key() == ord('q'):
                break
        
        # Release resources
        cap.release()
        self.close()
    
    def close(self):
        """
        Clean up resources.
        """
        self.hand_detector.close()
        self.arduino.close()
        self.renderer.close()
        print("System closed.")

def main():
    """
    Main entry point for the application.
    """
    # Add execution timing for performance monitoring
    start_time = time.time()
    # Parse arguments
    parser = argparse.ArgumentParser(description="Real-Time Hand Mimicking System")
    parser.add_argument('--port', type=str, default=DEFAULT_SERIAL_PORT, 
                       help='Arduino serial port')
    parser.add_argument('--baudrate', type=int, default=DEFAULT_BAUDRATE, 
                       help='Serial port baudrate (bit/s)')
    parser.add_argument('--calibrate', action='store_true', 
                       help='Start calibration mode')
    args = parser.parse_args()
    
    # Create system
    mimic_system = RealTimeHandMimicSystem(port=args.port, baudrate=args.baudrate)
    
    try:
        # Choose calibration or normal mode
        if args.calibrate:
            mimic_system.run_calibration_mode()
        else:
            mimic_system.run()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    except Exception as e:
        print(f"\nError occurred: {e}")
    finally:
        mimic_system.close()
        end_time = time.time()
        print(f"Program terminated. Total execution time: {end_time - start_time:.2f} seconds.")
        
        
if __name__ == "__main__":
    main()
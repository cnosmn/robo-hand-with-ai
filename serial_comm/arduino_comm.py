"""
Arduino communication module.
"""
import serial
import time
from typing import Dict, Optional

class ArduinoInterface:
    """
    Class for communicating with Arduino.
    """
    def __init__(self, port: str, baudrate: int, timeout: int = 1):
        """
        Initialize the Arduino communication.
        
        Args:
            port: Serial port for Arduino
            baudrate: Baud rate for serial communication
            timeout: Serial timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.last_angles = {}
        self.connect()
    
    def connect(self) -> bool:
        """
        Connect to Arduino.
        
        Returns:
            Success status
        """
        try:
            print(f"Arduino'ya {self.port} portundan bağlanılıyor...")
            # Uncomment this for debugging without Arduino
            # print("DEBUG MODU: Arduino bağlantısı simüle ediliyor")
            # self.ser = None
            # return False
            
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            print(f"Arduino'ya {self.port} portunda bağlandı")
            time.sleep(2)  # Wait for Arduino to reset
            self.ser.write(b"start\n")  # Start program
            time.sleep(0.5)
            
            # Read Arduino response
            response = ""
            while self.ser.in_waiting:
                response += self.ser.readline().decode('utf-8').strip()
            print(f"Arduino yanıtı: {response}")
            return True
        except Exception as e:
            print(f"Arduino bağlantı hatası: {e}")
            self.ser = None
            return False
    def send_finger_angles(self, angles: Dict[str, int], update_interval: int, angle_threshold: int) -> bool:
        """
        Send finger angles to Arduino.
        
        Args:
            angles: Dictionary of finger angles
            update_interval: Frame interval for updates
            angle_threshold: Minimum angle change to trigger update
            
        Returns:
            Success status
        """
        if self.ser is None:
            print("No Arduino connection!")
            return False
        
        # Check if update is needed
        should_update = self._should_update_angles(angles, update_interval, angle_threshold)
        
        if should_update:
            # Create unified command
            unified_cmd = (
                f"movefingers:{angles['thumb_mcp']}:{angles['thumb_ip']}:"
                f"{angles['index']}:{angles['middle']}:{angles['ring']}:{angles['pinky']}\n"
            )
            
            print(f"Sending command to Arduino: {unified_cmd.strip()}")
            self.ser.write(unified_cmd.encode())
            
            # Try to get response
            time.sleep(0.1)
            if self.ser.in_waiting:
                response = self.ser.readline().decode('utf-8').strip()
                print(f"Arduino response: {response}")
            
            # Update last angles
            self.last_angles = angles.copy()
            self.frame_counter = 0
            return True
        
        self.frame_counter += 1
        return False
    
    def _should_update_angles(self, angles: Dict[str, int], update_interval: int, angle_threshold: int) -> bool:
        """
        Decide if angles should be updated.
        
        Args:
            angles: Dictionary of finger angles
            update_interval: Frame interval for updates
            angle_threshold: Minimum angle change to trigger update
            
        Returns:
            True if update should happen
        """
        # If last_angles is empty (first run), update immediately
        if not self.last_angles:
            self.frame_counter = 0
            return True
        
        # Update at regular intervals
        if getattr(self, 'frame_counter', 0) >= update_interval:
            return True
        
        # Update if any finger angle changed significantly
        for key, value in angles.items():
            if key in self.last_angles and abs(value - self.last_angles[key]) > angle_threshold:
                self.frame_counter = 0
                return True
        
        # No update needed
        return False
    
    def close(self):
        """
        Close Arduino connection.
        """
        if self.ser is not None:
            self.ser.write(b"stop\n")
            time.sleep(0.5)
            self.ser.close()
            print("Arduino connection closed.")
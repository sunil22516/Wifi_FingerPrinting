"""
Sensor Fusion Module - Pedestrian Dead Reckoning (PDR)
=======================================================
Combines WiFi localization with IMU (accelerometer/gyroscope) data
to provide smooth position tracking between WiFi scans.

Author: Aviral (Integration/Sensor Fusion)

The WiFi scan happens every 2-4 seconds, but the user moves continuously.
PDR fills the gap by:
1. Detecting steps from accelerometer data
2. Estimating step length
3. Determining heading from gyroscope
4. Projecting position forward between WiFi fixes

This module also implements a simple Kalman-like filter to fuse
WiFi position estimates with PDR estimates.
"""

import math
import time
from typing import Dict, List, Optional, Tuple
from collections import deque


class PedestrianDeadReckoning:
    """
    PDR (Pedestrian Dead Reckoning) using phone IMU sensors.
    Estimates position changes between WiFi localization updates.
    """

    def __init__(self):
        self.step_length = 0.7  # Average step length in meters
        self.heading = 0.0  # Current heading in radians (0 = North/up)
        self.position = {"x": 0.0, "y": 0.0}
        self.step_count = 0
        
        # Step detection parameters
        self.accel_threshold = 1.2  # m/s² threshold for step detection
        self.min_step_interval = 0.3  # Minimum time between steps (seconds)
        self.last_step_time = 0
        
        # Accelerometer history for step detection
        self.accel_history = deque(maxlen=50)
        self.last_peak = False

    def update_heading(self, gyro_z: float, dt: float):
        """
        Update heading from gyroscope Z-axis reading.
        
        Parameters:
            gyro_z: Gyroscope Z-axis angular velocity (rad/s)
            dt: Time delta since last reading (seconds)
        """
        self.heading += gyro_z * dt
        # Normalize to [0, 2π]
        self.heading = self.heading % (2 * math.pi)

    def detect_step(self, accel_magnitude: float, timestamp: float) -> bool:
        """
        Detect a step from accelerometer magnitude.
        Uses peak detection on acceleration signal.
        
        Parameters:
            accel_magnitude: Magnitude of acceleration vector (m/s²)
            timestamp: Current time in seconds
            
        Returns:
            True if a step was detected
        """
        self.accel_history.append(accel_magnitude)
        
        # Need enough history
        if len(self.accel_history) < 5:
            return False
        
        # Check if current reading is a peak above threshold
        is_peak = (accel_magnitude > self.accel_threshold and
                   accel_magnitude > self.accel_history[-2] and
                   accel_magnitude > self.accel_history[-3])
        
        # Debounce: minimum time between steps
        time_since_last = timestamp - self.last_step_time
        
        if is_peak and not self.last_peak and time_since_last > self.min_step_interval:
            self.last_step_time = timestamp
            self.step_count += 1
            self.last_peak = True
            return True
        
        if not is_peak:
            self.last_peak = False
        
        return False

    def step_forward(self) -> Dict:
        """
        Project position forward by one step in current heading direction.
        
        Returns:
            New position {x, y}
        """
        # In our coordinate system: x increases right, y increases down
        # heading 0 = North (up = negative y)
        dx = self.step_length * math.sin(self.heading)
        dy = -self.step_length * math.cos(self.heading)
        
        self.position["x"] += dx
        self.position["y"] += dy
        
        return {"x": self.position["x"], "y": self.position["y"]}

    def set_position(self, x: float, y: float):
        """Set/reset position (called when WiFi fix is received)."""
        self.position = {"x": x, "y": y}

    def set_heading_degrees(self, degrees: float):
        """Set heading in degrees (0=North, 90=East, 180=South, 270=West)."""
        self.heading = math.radians(degrees)


class SensorFusion:
    """
    Fuses WiFi localization and PDR estimates using a weighted average.
    
    When a WiFi fix arrives → high trust in WiFi position
    Between WiFi fixes → use PDR to estimate movement
    Result: smooth continuous position that doesn't jump wildly
    """

    def __init__(self):
        self.pdr = PedestrianDeadReckoning()
        self.wifi_position = None  # Last WiFi-based position
        self.fused_position = None  # Current best estimate
        self.wifi_confidence = 0.0
        self.last_wifi_time = 0
        
        # Fusion parameters
        self.wifi_weight_initial = 0.8  # How much to trust WiFi when fresh
        self.wifi_decay_rate = 0.1  # WiFi trust decays over time
        self.max_wifi_age = 5.0  # Seconds before WiFi fix is "stale"
        
        # Position history for smoothing
        self.position_history = deque(maxlen=20)

    def update_wifi(self, x: float, y: float, confidence: float, timestamp: float = None):
        """
        Called when a new WiFi localization result is available.
        
        Parameters:
            x, y: WiFi-estimated position
            confidence: Localization confidence (0-1)
            timestamp: Time of measurement (defaults to now)
        """
        if timestamp is None:
            timestamp = time.time()
        
        self.wifi_position = {"x": x, "y": y}
        self.wifi_confidence = confidence
        self.last_wifi_time = timestamp
        
        # Reset PDR position to WiFi fix
        self.pdr.set_position(x, y)
        
        # Update fused position
        self.fused_position = {"x": x, "y": y}
        self.position_history.append({"x": x, "y": y, "t": timestamp})

    def update_imu(self, accel_x: float, accel_y: float, accel_z: float,
                   gyro_z: float, dt: float, timestamp: float = None):
        """
        Called with each IMU reading (accelerometer + gyroscope).
        
        Parameters:
            accel_x, accel_y, accel_z: Accelerometer readings (m/s²)
            gyro_z: Gyroscope Z-axis (rad/s)
            dt: Time since last IMU reading (seconds)
            timestamp: Current time
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Update heading from gyroscope
        self.pdr.update_heading(gyro_z, dt)
        
        # Detect step from accelerometer
        accel_mag = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2)
        # Subtract gravity (≈9.81 m/s²) to get movement acceleration
        accel_movement = abs(accel_mag - 9.81)
        
        if self.pdr.detect_step(accel_movement, timestamp):
            # Step detected → project position forward
            pdr_pos = self.pdr.step_forward()
            
            # Fuse with WiFi if available
            self.fused_position = self._fuse_positions(pdr_pos, timestamp)
            self.position_history.append({
                "x": self.fused_position["x"],
                "y": self.fused_position["y"],
                "t": timestamp
            })

    def _fuse_positions(self, pdr_position: Dict, current_time: float) -> Dict:
        """
        Fuse PDR position with last WiFi position using time-decayed weighting.
        """
        if self.wifi_position is None:
            return pdr_position
        
        # WiFi trust decays over time
        wifi_age = current_time - self.last_wifi_time
        if wifi_age > self.max_wifi_age:
            # WiFi is too old, trust PDR fully
            return pdr_position
        
        # Compute WiFi weight (decays with time)
        wifi_weight = self.wifi_weight_initial * (1.0 - wifi_age / self.max_wifi_age)
        wifi_weight *= self.wifi_confidence
        pdr_weight = 1.0 - wifi_weight
        
        # Weighted average
        fused_x = wifi_weight * self.wifi_position["x"] + pdr_weight * pdr_position["x"]
        fused_y = wifi_weight * self.wifi_position["y"] + pdr_weight * pdr_position["y"]
        
        return {"x": round(fused_x, 2), "y": round(fused_y, 2)}

    def get_position(self) -> Optional[Dict]:
        """Get current best position estimate."""
        if self.fused_position is None:
            return self.wifi_position
        return self.fused_position

    def get_heading_degrees(self) -> float:
        """Get current heading in degrees."""
        return math.degrees(self.pdr.heading) % 360

    def get_step_count(self) -> int:
        """Get total steps counted."""
        return self.pdr.step_count

    def get_status(self) -> Dict:
        """Get full sensor fusion status."""
        pos = self.get_position()
        return {
            "position": pos,
            "heading": self.get_heading_degrees(),
            "step_count": self.pdr.step_count,
            "wifi_age": time.time() - self.last_wifi_time if self.last_wifi_time > 0 else None,
            "wifi_confidence": self.wifi_confidence,
            "history_length": len(self.position_history)
        }

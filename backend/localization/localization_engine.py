"""
Localization Engine
====================
Main localization module that loads the radio map and provides 
position estimation using WiFi fingerprinting + KNN.

Author: Tikam (Localization)

Usage:
    from localization_engine import LocalizationEngine
    engine = LocalizationEngine("path/to/radio_map.json")
    position = engine.localize({"AA:BB:CC:11:22:01": -45, "AA:BB:CC:11:22:02": -60})
"""

import json
import os
from typing import Dict, List, Optional

try:
    from .knn import knn_localize, filter_common_aps
except ImportError:
    from knn import knn_localize, filter_common_aps


class LocalizationEngine:
    """
    WiFi Fingerprint-based Indoor Localization Engine.
    Uses KNN algorithm to match live WiFi scans against a pre-recorded radio map.
    """

    def __init__(self, radio_map_path: str = None):
        """
        Initialize with radio map data.
        
        Parameters:
            radio_map_path: Path to radio_map.json file
        """
        if radio_map_path is None:
            # Default path: look in data_collection/sample_data/
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            radio_map_path = os.path.join(base_dir, "data_collection", "sample_data", "radio_map.json")

        with open(radio_map_path, "r") as f:
            data = json.load(f)

        self.radio_map = data["fingerprints"]
        self.metadata = data.get("metadata", {})
        self.k = 3  # Default K for KNN
        self.weighted = True  # Use weighted KNN
        self.last_position = None  # Track last known position

    def localize(self, wifi_readings: Dict[str, int]) -> Dict:
        """
        Estimate current position from WiFi readings.
        
        Parameters:
            wifi_readings: Dictionary of {bssid: rssi} from live WiFi scan
            
        Returns:
            Dictionary with x, y, confidence, neighbors
        """
        # Filter to only known APs for better accuracy
        filtered = filter_common_aps(wifi_readings, self.radio_map)
        
        # Run KNN localization
        result = knn_localize(filtered, self.radio_map, k=self.k, weighted=self.weighted)
        
        # Store for tracking
        self.last_position = {"x": result["x"], "y": result["y"]}
        
        return result

    def localize_with_history(self, wifi_readings: Dict[str, int], 
                              alpha: float = 0.3) -> Dict:
        """
        Localize with exponential moving average smoothing.
        Reduces jumping between positions by blending with previous position.
        
        Parameters:
            wifi_readings: Current WiFi scan
            alpha: Smoothing factor (0-1). Lower = smoother but slower response.
            
        Returns:
            Smoothed position estimate
        """
        raw_result = self.localize(wifi_readings)
        
        if self.last_position is None:
            self.last_position = {"x": raw_result["x"], "y": raw_result["y"]}
            return raw_result
        
        # Exponential moving average
        smoothed_x = alpha * raw_result["x"] + (1 - alpha) * self.last_position["x"]
        smoothed_y = alpha * raw_result["y"] + (1 - alpha) * self.last_position["y"]
        
        self.last_position = {"x": smoothed_x, "y": smoothed_y}
        
        raw_result["x"] = round(smoothed_x, 2)
        raw_result["y"] = round(smoothed_y, 2)
        raw_result["smoothed"] = True
        
        return raw_result

    def set_k(self, k: int):
        """Set the K parameter for KNN."""
        if k < 1:
            raise ValueError("K must be at least 1")
        self.k = k

    def get_radio_map_info(self) -> Dict:
        """Return info about loaded radio map."""
        return {
            "num_fingerprints": len(self.radio_map),
            "metadata": self.metadata,
            "bssids": list(self._get_all_bssids()),
            "coverage_area": self._get_coverage_area()
        }

    def _get_all_bssids(self) -> set:
        """Get all BSSIDs in the radio map."""
        bssids = set()
        for fp in self.radio_map:
            bssids.update(fp["wifi_readings"].keys())
        return bssids

    def _get_coverage_area(self) -> Dict:
        """Get the bounding box of the radio map coverage."""
        if not self.radio_map:
            return {"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0}
        
        xs = [fp["x"] for fp in self.radio_map]
        ys = [fp["y"] for fp in self.radio_map]
        
        return {
            "min_x": min(xs),
            "max_x": max(xs),
            "min_y": min(ys),
            "max_y": max(ys)
        }

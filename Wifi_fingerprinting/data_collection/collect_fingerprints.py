"""
WiFi Fingerprint Data Collection Tool
=======================================
Collects WiFi RSSI fingerprints at known locations on the 4th floor.
Records the data into a CSV/JSON radio map for the localization engine.



Usage:
    python collect_fingerprints.py

Workflow:
    1. Stand at a known grid point on the 4th floor
    2. Enter the X,Y coordinates when prompted
    3. The tool scans WiFi multiple times and records averaged RSSI
    4. Move to next grid point and repeat
    5. Data is saved to radio_map.csv and radio_map.json
"""

import csv
import json
import os
import re
import time
from datetime import datetime
from typing import List, Dict

from wifi_scanner import scan_wifi_multiple, scan_wifi


# Configuration
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data")
CSV_FILE = os.path.join(OUTPUT_DIR, "radio_map.csv")
JSON_FILE = os.path.join(OUTPUT_DIR, "radio_map.json")
SCANS_PER_POINT = 5  # Number of WiFi scans to average at each point


def parse_coordinates(coords_input: str) -> tuple[float, float]:
    """Parse coordinates entered as either 'X,Y' or 'X Y'."""
    parts = [part for part in re.split(r"[,\s]+", coords_input.strip()) if part]
    if len(parts) != 2:
        raise ValueError("Coordinates must contain exactly two numbers")
    return float(parts[0]), float(parts[1])


def normalize_fingerprint(fp: Dict) -> Dict:
    """Backfill fields that may be missing from older radio map entries."""
    fp.setdefault("label", "")
    fp.setdefault("timestamp", "")
    fp.setdefault("wifi_readings", {})
    return fp


def collect_single_point(x: float, y: float, location_label: str = "") -> Dict:
    """
    Collect WiFi fingerprint at a single grid point.
    
    Parameters:
        x, y: Coordinates of the collection point (meters)
        location_label: Human-readable label for this point
        
    Returns:
        Dictionary with coordinates and WiFi readings
    """
    print(f"\n  Scanning WiFi at ({x}, {y})... ({SCANS_PER_POINT} scans)")
    networks = scan_wifi_multiple(num_scans=SCANS_PER_POINT)
    
    fingerprint = {
        "x": x,
        "y": y,
        "label": location_label,
        "timestamp": datetime.now().isoformat(),
        "wifi_readings": {}
    }
    
    for net in networks:
        fingerprint["wifi_readings"][net["bssid"]] = {
            "ssid": net["ssid"],
            "rssi": net["rssi"],
            "num_readings": net.get("num_readings", 1)
        }
    
    print(f"  Captured {len(networks)} access points")
    return fingerprint


def save_to_csv(fingerprints: List[Dict], filepath: str):
    """
    Save fingerprints to CSV format.
    Format: x, y, label, bssid1_rssi, bssid2_rssi, ...
    Missing APs get value -100 (no signal)
    """
    # Collect all unique BSSIDs
    all_bssids = set()
    for fp in fingerprints:
        fp = normalize_fingerprint(fp)
        all_bssids.update(fp["wifi_readings"].keys())
    all_bssids = sorted(all_bssids)
    
    # Write CSV
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        # Header
        header = ["x", "y", "label", "timestamp"] + all_bssids
        writer.writerow(header)
        
        # Data rows
        for fp in fingerprints:
            fp = normalize_fingerprint(fp)
            row = [
                fp.get("x", ""),
                fp.get("y", ""),
                fp.get("label", ""),
                fp.get("timestamp", "")
            ]
            for bssid in all_bssids:
                if bssid in fp["wifi_readings"]:
                    reading = fp["wifi_readings"][bssid]
                    row.append(reading.get("rssi", -100) if isinstance(reading, dict) else reading)
                else:
                    row.append(-100)  # No signal
            writer.writerow(row)
    
    print(f"\n  Saved to CSV: {filepath}")


def save_to_json(fingerprints: List[Dict], filepath: str):
    """Save fingerprints to JSON format."""
    data = {
        "metadata": {
            "collected_at": datetime.now().isoformat(),
            "floor": "4th Floor, R&D Building",
            "num_points": len(fingerprints),
            "scans_per_point": SCANS_PER_POINT,
            "coordinate_system": "meters from top-left corner"
        },
        "fingerprints": fingerprints
    }
    
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"  Saved to JSON: {filepath}")


def load_existing_data(filepath: str) -> List[Dict]:
    """Load existing fingerprint data to append to."""
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            data = json.load(f)
            return [normalize_fingerprint(fp) for fp in data.get("fingerprints", [])]
    return []


def interactive_collection():
    """
    Interactive mode: prompts user for coordinates and collects data.
    """
    print("=" * 60)
    print("WiFi Fingerprint Collection Tool")
    print("=" * 60)
    print("\nThis tool collects WiFi signal data at known locations.")
    print("Walk to each grid point, enter coordinates, and wait for scan.")
    print("Type 'done' to finish and save.\n")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load existing data if any
    fingerprints = load_existing_data(JSON_FILE)
    if fingerprints:
        print(f"Loaded {len(fingerprints)} existing fingerprints.")
    
    point_count = len(fingerprints)
    
    while True:
        print(f"\n--- Point #{point_count + 1} ---")
        
        # Get coordinates
        coords_input = input("Enter X,Y coordinates (or 'done' to finish): ").strip()
        
        if coords_input.lower() == "done":
            break
        
        try:
            x, y = parse_coordinates(coords_input)
        except ValueError:
            print("  Invalid format. Use: X,Y or X Y (e.g., 25.0,8.0 or 25.0 8.0)")
            continue
        
        label = input("  Location label (optional, press Enter to skip): ").strip()
        
        # Collect fingerprint
        fp = collect_single_point(x, y, label)
        fingerprints.append(fp)
        point_count += 1
        
        # Auto-save after each point
        save_to_json(fingerprints, JSON_FILE)
        save_to_csv(fingerprints, CSV_FILE)
        print(f"  Total points collected: {point_count}")
    
    # Final save
    if fingerprints:
        save_to_json(fingerprints, JSON_FILE)
        save_to_csv(fingerprints, CSV_FILE)
        print(f"\n{'=' * 60}")
        print(f"Collection complete! {point_count} points saved.")
        print(f"  CSV: {CSV_FILE}")
        print(f"  JSON: {JSON_FILE}")
        print(f"{'=' * 60}")
    else:
        print("\nNo data collected.")


def batch_collection(grid_points: List[Dict]):
    """
    Automated batch collection at predefined grid points.
    
    Parameters:
        grid_points: List of {"x": float, "y": float, "label": str}
    """
    print(f"Batch collection: {len(grid_points)} points")
    fingerprints = []
    
    for i, point in enumerate(grid_points):
        print(f"\nPoint {i+1}/{len(grid_points)}: ({point['x']}, {point['y']}) - {point.get('label', '')}")
        input("  Press Enter when you're at this location...")
        
        fp = collect_single_point(point["x"], point["y"], point.get("label", ""))
        fingerprints.append(fp)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    save_to_json(fingerprints, JSON_FILE)
    save_to_csv(fingerprints, CSV_FILE)
    return fingerprints


if __name__ == "__main__":
    interactive_collection()

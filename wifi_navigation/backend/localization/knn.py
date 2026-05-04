"""
KNN (K-Nearest Neighbors) WiFi Localization Algorithm
======================================================
Compares live WiFi RSSI readings against the radio map (fingerprint database)
to determine the user's X,Y position.

Author: Tikam (Localization)

Algorithm:
1. Take live WiFi scan (list of BSSIDs and their RSSI values)
2. Compare against every stored fingerprint in radio map
3. Compute "signal distance" between live scan and each stored fingerprint
4. Pick K closest matches (lowest distance)
5. Average their X,Y coordinates → that's the estimated position
"""

import math
from typing import List, Dict, Tuple, Optional


def signal_distance(live_readings: Dict[str, int], stored_readings: Dict[str, int],
                    missing_penalty: int = -100) -> float:
    """
    Compute the Euclidean distance in signal space between a live scan
    and a stored fingerprint.

    Strategy: use only BSSIDs that appear in BOTH scans (intersection).
    If the intersection is very small (<3), fall back to the full union
    with a missing_penalty for robustness.

    Parameters:
        live_readings: {bssid: rssi} from current WiFi scan (BSSIDs lowercase)
        stored_readings: {bssid: rssi} from radio map (BSSIDs lowercase)
        missing_penalty: fallback RSSI when AP is missing (-100 = no signal)

    Returns:
        Euclidean distance in signal space (lower = more similar)
    """
    common = set(live_readings.keys()) & set(stored_readings.keys())

    if len(common) >= 2:
        # Compare only shared APs – avoids noise from unrelated APs
        sum_sq = sum((live_readings[b] - stored_readings[b]) ** 2 for b in common)
        return math.sqrt(sum_sq)

    # Fallback: full union with penalty (less reliable but still works)
    all_bssids = set(live_readings.keys()) | set(stored_readings.keys())
    sum_sq = 0.0
    for bssid in all_bssids:
        live_rssi = live_readings.get(bssid, missing_penalty)
        stored_rssi = stored_readings.get(bssid, missing_penalty)
        diff = live_rssi - stored_rssi
        sum_sq += diff * diff
    return math.sqrt(sum_sq)


def knn_localize(live_readings: Dict[str, int], radio_map: List[Dict],
                 k: int = 3, weighted: bool = True) -> Dict:
    """
    KNN-based localization.
    
    Parameters:
        live_readings: Current WiFi scan {bssid: rssi_value}  (BSSIDs already lowercase)
        radio_map: List of fingerprints [{x, y, wifi_readings: {bssid: rssi_int}}]
                   (BSSIDs already lowercase, normalised by LocalizationEngine.__init__)
        k: Number of nearest neighbors to consider
        weighted: If True, weight neighbors by inverse distance (WKNN)
    
    Returns:
        Dictionary with:
            - x, y: Estimated coordinates
            - confidence: Quality score (0-1, higher = more confident)
            - neighbors: The K nearest reference points used
    """
    if not radio_map:
        raise ValueError("Radio map is empty")
    if not live_readings:
        raise ValueError("No WiFi readings provided")

    # Lowercase live BSSIDs for consistent comparison
    live_lower = {b.lower(): r for b, r in live_readings.items()}

    # Compute distance from live scan to every fingerprint in radio map
    distances = []
    for fp in radio_map:
        # fp["wifi_readings"] is already {bssid_lower: rssi_int} from LocalizationEngine
        stored_rssi = fp["wifi_readings"]
        dist = signal_distance(live_lower, stored_rssi)
        distances.append((dist, fp))

    # Sort by distance (closest first)
    distances.sort(key=lambda x: x[0])

    # Take K nearest neighbors
    k = min(k, len(distances))
    nearest = distances[:k]

    if weighted and nearest[0][0] > 0:
        total_weight = 0.0
        weighted_x = 0.0
        weighted_y = 0.0
        for dist, fp in nearest:
            weight = 1.0 / (dist + 0.001)
            weighted_x += fp["x"] * weight
            weighted_y += fp["y"] * weight
            total_weight += weight
        est_x = weighted_x / total_weight
        est_y = weighted_y / total_weight
    else:
        est_x = sum(fp["x"] for _, fp in nearest) / k
        est_y = sum(fp["y"] for _, fp in nearest) / k

    min_dist = nearest[0][0]
    max_reasonable_dist = 60.0  # empirical threshold for this building
    confidence = max(0.0, 1.0 - (min_dist / max_reasonable_dist))

    return {
        "x": round(est_x, 2),
        "y": round(est_y, 2),
        "confidence": round(confidence, 3),
        "neighbors": [
            {
                "x": fp["x"],
                "y": fp["y"],
                "label": fp.get("label", ""),
                "location_id": fp.get("location_id", ""),
                "distance": round(dist, 2)
            }
            for dist, fp in nearest
        ]
    }


def filter_common_aps(live_readings: Dict[str, int], radio_map: List[Dict],
                      min_aps: int = 3) -> Dict[str, int]:
    """
    Filter live readings to only include APs that appear in the radio map.
    This improves accuracy by ignoring transient/unknown APs.
    
    Parameters:
        live_readings: Current scan {bssid: rssi}
        radio_map: Fingerprint database
        min_aps: Minimum number of common APs required
    
    Returns:
        Filtered readings dict
    """
    # Collect all BSSIDs in radio map
    map_bssids = set()
    for fp in radio_map:
        map_bssids.update(fp["wifi_readings"].keys())
    
    # Keep only APs that appear in radio map
    filtered = {bssid: rssi for bssid, rssi in live_readings.items() if bssid in map_bssids}
    
    if len(filtered) < min_aps:
        # If too few common APs, return all readings
        return live_readings
    
    return filtered

"""
Comprehensive Test Suite
=========================
Tests for all components: Localization, Navigation, Sensor Fusion.
Run with: python -m pytest tests/ -v
Or simply: python tests/test_all.py
"""

import sys
import os
import math

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "navigation"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "localization"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "sensor_fusion"))


# ============================================================
# Navigation Tests
# ============================================================
def test_navigation_graph_load():
    """Test graph loads with correct number of nodes and edges."""
    from navigation_engine import NavigationEngine
    engine = NavigationEngine()
    assert len(engine.nodes) >= 20, f"Expected >=20 nodes, got {len(engine.nodes)}"
    assert len(engine.edges) >= 20, f"Expected >=20 edges, got {len(engine.edges)}"
    print("✓ Navigation: graph loads correctly")


def test_navigation_astar_elevator_to_412():
    """Test A* finds path from elevator to B-412."""
    from navigation_engine import NavigationEngine
    engine = NavigationEngine()
    result = engine.navigate(25.0, 2.0, "B-412")
    assert result["success"]
    assert result["path"][0] == "ELEVATOR"
    assert result["path"][-1] == "ROOM_412_DOOR"
    assert result["total_distance"] > 0
    print(f"✓ Navigation: Elevator→B-412 = {result['total_distance']}m via {len(result['path'])} nodes")


def test_navigation_all_destinations_reachable():
    """Test every destination is reachable from elevator."""
    from navigation_engine import NavigationEngine
    engine = NavigationEngine()
    failures = []
    for dest in engine.get_available_destinations():
        result = engine.navigate(25.0, 2.0, dest)
        if not result["success"]:
            failures.append(dest)
    assert len(failures) == 0, f"Unreachable: {failures}"
    print(f"✓ Navigation: all {len(engine.destinations)} destinations reachable")


def test_navigation_directions_generated():
    """Test turn-by-turn directions are generated."""
    from navigation_engine import NavigationEngine
    engine = NavigationEngine()
    result = engine.navigate(25.0, 2.0, "408")
    assert result["success"]
    assert len(result["directions"]) >= 2
    assert result["directions"][0]["action"] == "start"
    assert result["directions"][-1]["action"] == "arrived"
    print(f"✓ Navigation: {len(result['directions'])} direction steps generated")


def test_navigation_invalid_destination():
    """Test graceful handling of invalid destination."""
    from navigation_engine import NavigationEngine
    engine = NavigationEngine()
    result = engine.navigate(25.0, 2.0, "Room XYZ")
    assert not result["success"]
    assert "error" in result
    print("✓ Navigation: invalid destination handled")


def test_navigation_reroute():
    """Test dynamic re-routing from new position."""
    from navigation_engine import NavigationEngine
    engine = NavigationEngine()
    result1 = engine.navigate(25.0, 2.0, "B-412")
    result2 = engine.navigate(25.0, 8.0, "B-412")  # Moved to lobby
    assert result1["success"] and result2["success"]
    assert result2["total_distance"] <= result1["total_distance"]
    print("✓ Navigation: re-routing gives shorter path")


# ============================================================
# Localization Tests
# ============================================================
def test_localization_knn_basic():
    """Test KNN localizes to correct area with matching fingerprint."""
    from knn import knn_localize
    import json
    
    # Load radio map
    radio_map_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "data_collection", "sample_data", "radio_map.json")
    with open(radio_map_path) as f:
        data = json.load(f)
    radio_map = data["fingerprints"]
    
    # Use exact readings from elevator point
    live_readings = {
        "AA:BB:CC:11:22:01": -35,
        "AA:BB:CC:11:22:02": -62,
        "AA:BB:CC:11:22:03": -78,
        "AA:BB:CC:11:22:04": -80,
        "AA:BB:CC:11:22:05": -85
    }
    
    result = knn_localize(live_readings, radio_map, k=3)
    # Should be near elevator (25, 2)
    assert abs(result["x"] - 25.0) < 5.0, f"X={result['x']}, expected ~25"
    assert abs(result["y"] - 2.0) < 5.0, f"Y={result['y']}, expected ~2"
    print(f"✓ Localization: KNN estimated ({result['x']}, {result['y']}), expected ~(25, 2)")


def test_localization_knn_different_locations():
    """Test KNN distinguishes between different locations."""
    from knn import knn_localize
    import json
    
    radio_map_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "data_collection", "sample_data", "radio_map.json")
    with open(radio_map_path) as f:
        data = json.load(f)
    radio_map = data["fingerprints"]
    
    # Readings similar to East Junction (45, 8)
    east_readings = {
        "AA:BB:CC:11:22:01": -70,
        "AA:BB:CC:11:22:02": -70,
        "AA:BB:CC:11:22:03": -33,
        "AA:BB:CC:11:22:04": -45,
        "AA:BB:CC:11:22:05": -60
    }
    
    # Readings similar to SW Junction (5, 30)
    sw_readings = {
        "AA:BB:CC:11:22:01": -85,
        "AA:BB:CC:11:22:02": -52,
        "AA:BB:CC:11:22:03": -72,
        "AA:BB:CC:11:22:04": -45,
        "AA:BB:CC:11:22:05": -38
    }
    
    east_result = knn_localize(east_readings, radio_map, k=3)
    sw_result = knn_localize(sw_readings, radio_map, k=3)
    
    # They should be in different locations
    dist = math.sqrt((east_result["x"] - sw_result["x"])**2 + (east_result["y"] - sw_result["y"])**2)
    assert dist > 10, f"Locations too close: {dist}m apart"
    print(f"✓ Localization: distinguishes East ({east_result['x']},{east_result['y']}) from SW ({sw_result['x']},{sw_result['y']})")


def test_localization_confidence():
    """Test confidence score is reasonable."""
    from knn import knn_localize
    import json
    
    radio_map_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "data_collection", "sample_data", "radio_map.json")
    with open(radio_map_path) as f:
        data = json.load(f)
    radio_map = data["fingerprints"]
    
    # Exact match should have high confidence
    exact_readings = {
        "AA:BB:CC:11:22:01": -35,
        "AA:BB:CC:11:22:02": -62,
        "AA:BB:CC:11:22:03": -78,
        "AA:BB:CC:11:22:04": -80,
        "AA:BB:CC:11:22:05": -85
    }
    result = knn_localize(exact_readings, radio_map, k=3)
    assert result["confidence"] > 0.5, f"Confidence too low: {result['confidence']}"
    print(f"✓ Localization: confidence = {result['confidence']}")


def test_localization_engine():
    """Test LocalizationEngine class."""
    from localization_engine import LocalizationEngine
    
    radio_map_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "data_collection", "sample_data", "radio_map.json")
    engine = LocalizationEngine(radio_map_path)
    
    result = engine.localize({
        "AA:BB:CC:11:22:01": -45,
        "AA:BB:CC:11:22:02": -42,
        "AA:BB:CC:11:22:03": -65,
        "AA:BB:CC:11:22:04": -70,
        "AA:BB:CC:11:22:05": -78
    })
    assert "x" in result and "y" in result
    assert result["confidence"] > 0
    print(f"✓ Localization Engine: position ({result['x']}, {result['y']}), confidence {result['confidence']}")


# ============================================================
# Sensor Fusion Tests
# ============================================================
def test_sensor_fusion_wifi_update():
    """Test sensor fusion with WiFi update."""
    from fusion import SensorFusion
    
    sf = SensorFusion()
    sf.update_wifi(25.0, 8.0, 0.9, timestamp=100.0)
    pos = sf.get_position()
    assert pos is not None
    assert abs(pos["x"] - 25.0) < 0.01
    assert abs(pos["y"] - 8.0) < 0.01
    print("✓ Sensor Fusion: WiFi update works")


def test_sensor_fusion_step_detection():
    """Test PDR step detection."""
    from fusion import PedestrianDeadReckoning
    
    pdr = PedestrianDeadReckoning()
    pdr.set_position(25.0, 8.0)
    pdr.set_heading_degrees(180)  # Facing south
    
    # Build up history with low readings first (need 5 readings in history)
    pdr.detect_step(0.5, 0.1)
    pdr.detect_step(0.5, 0.2)
    pdr.detect_step(0.5, 0.3)
    pdr.detect_step(0.5, 0.4)
    pdr.detect_step(0.8, 0.5)  # Rising
    
    # Now simulate a peak (above threshold, higher than previous 2)
    detected = pdr.detect_step(2.0, 1.0)
    assert detected, "Step should be detected"
    
    # Take the step
    new_pos = pdr.step_forward()
    assert new_pos["y"] > 8.0, "Should move south (y increases)"
    print(f"✓ Sensor Fusion: step detected, moved to ({new_pos['x']:.2f}, {new_pos['y']:.2f})")


def test_sensor_fusion_combined():
    """Test full fusion: WiFi + simulated IMU steps."""
    from fusion import SensorFusion
    import time
    
    sf = SensorFusion()
    
    # Initial WiFi fix
    t = 100.0
    sf.update_wifi(25.0, 8.0, 0.9, timestamp=t)
    
    # Simulate walking south with IMU
    sf.pdr.set_heading_degrees(180)
    for i in range(5):
        t += 0.5
        sf.update_imu(0, 0, 11.5, 0, 0.02, timestamp=t)  # Step-like acceleration
        t += 0.3
        sf.update_imu(0, 0, 9.0, 0, 0.02, timestamp=t)   # Normal
    
    pos = sf.get_position()
    assert pos is not None
    print(f"✓ Sensor Fusion: after 5 IMU updates, position = ({pos['x']:.1f}, {pos['y']:.1f})")


# ============================================================
# Integration Tests
# ============================================================
def test_full_pipeline():
    """Test complete pipeline: Localize → Navigate → Directions."""
    from localization_engine import LocalizationEngine
    from navigation_engine import NavigationEngine
    
    radio_map_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "data_collection", "sample_data", "radio_map.json")
    
    loc_engine = LocalizationEngine(radio_map_path)
    nav_engine = NavigationEngine()
    
    # Step 1: Localize (simulate being at elevator)
    loc_result = loc_engine.localize({
        "AA:BB:CC:11:22:01": -35,
        "AA:BB:CC:11:22:02": -62,
        "AA:BB:CC:11:22:03": -78,
        "AA:BB:CC:11:22:04": -80,
        "AA:BB:CC:11:22:05": -85
    })
    
    # Step 2: Navigate to B-412
    nav_result = nav_engine.navigate(loc_result["x"], loc_result["y"], "B-412")
    
    assert nav_result["success"]
    assert nav_result["total_distance"] > 0
    assert len(nav_result["directions"]) > 0
    
    print(f"✓ Full Pipeline: Localized at ({loc_result['x']}, {loc_result['y']})")
    print(f"  → Navigate to B-412: {nav_result['total_distance']}m, {len(nav_result['directions'])} steps")
    print(f"  → Path: {' → '.join(nav_result['path'][:4])}...")


# ============================================================
# Run All Tests
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("WIFI INDOOR NAVIGATION - Full Test Suite")
    print("=" * 60)
    print()

    tests = [
        # Navigation
        test_navigation_graph_load,
        test_navigation_astar_elevator_to_412,
        test_navigation_all_destinations_reachable,
        test_navigation_directions_generated,
        test_navigation_invalid_destination,
        test_navigation_reroute,
        # Localization
        test_localization_knn_basic,
        test_localization_knn_different_locations,
        test_localization_confidence,
        test_localization_engine,
        # Sensor Fusion
        test_sensor_fusion_wifi_update,
        test_sensor_fusion_step_detection,
        test_sensor_fusion_combined,
        # Integration
        test_full_pipeline,
    ]

    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    if failed == 0:
        print("ALL TESTS PASSED ✓")
    print("=" * 60)

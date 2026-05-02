"""
Test Suite for Navigation Engine
=================================
Run with: python test_navigation.py
Or with pytest: pytest test_navigation.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from astar import astar, build_adjacency_list, find_nearest_node, euclidean_distance
from directions import generate_directions, get_total_distance, compute_bearing, get_turn_direction
from navigation_engine import NavigationEngine


def test_graph_loading():
    """Test that graph loads correctly."""
    engine = NavigationEngine()
    assert len(engine.nodes) > 0, "No nodes loaded"
    assert len(engine.edges) > 0, "No edges loaded"
    assert len(engine.destinations) > 0, "No destinations loaded"
    print("✓ Graph loading works")


def test_adjacency_list():
    """Test adjacency list construction."""
    engine = NavigationEngine()
    adj = engine.adjacency
    # Elevator should connect to Lobby
    elevator_neighbors = [n for n, w in adj.get("ELEVATOR", [])]
    assert "LOBBY" in elevator_neighbors, "ELEVATOR should connect to LOBBY"
    print("✓ Adjacency list construction works")


def test_euclidean_distance():
    """Test distance calculation."""
    a = {"x": 0, "y": 0}
    b = {"x": 3, "y": 4}
    assert abs(euclidean_distance(a, b) - 5.0) < 0.001
    print("✓ Euclidean distance works")


def test_astar_basic():
    """Test A* finds a path from elevator to room B-412."""
    engine = NavigationEngine()
    result = astar(engine.nodes, engine.adjacency, "ELEVATOR", "ROOM_412_DOOR")
    assert result is not None, "A* should find a path"
    assert result["path"][0] == "ELEVATOR", "Path should start at ELEVATOR"
    assert result["path"][-1] == "ROOM_412_DOOR", "Path should end at ROOM_412_DOOR"
    assert result["total_distance"] > 0, "Distance should be positive"
    print(f"✓ A* basic: ELEVATOR → B-412 = {result['total_distance']}m, path: {' → '.join(result['path'])}")


def test_astar_same_node():
    """Test A* when start == goal."""
    engine = NavigationEngine()
    result = astar(engine.nodes, engine.adjacency, "ELEVATOR", "ELEVATOR")
    assert result is not None
    assert result["path"] == ["ELEVATOR"]
    assert result["total_distance"] == 0
    print("✓ A* same node (trivial path) works")


def test_astar_all_destinations():
    """Test A* can find path from elevator to ALL destinations."""
    engine = NavigationEngine()
    failures = []
    for dest_name, dest_node in engine.destinations.items():
        result = astar(engine.nodes, engine.adjacency, "ELEVATOR", dest_node)
        if result is None:
            failures.append(dest_name)

    assert len(failures) == 0, f"No path found for: {failures}"
    print(f"✓ A* reaches all {len(engine.destinations)} destinations from elevator")


def test_find_nearest_node():
    """Test snapping coordinates to nearest node."""
    engine = NavigationEngine()
    # Point very close to elevator (25, 2)
    nearest = find_nearest_node(engine.nodes, 25.1, 2.1)
    assert nearest == "ELEVATOR", f"Expected ELEVATOR, got {nearest}"

    # Point close to lobby (25, 8)
    nearest = find_nearest_node(engine.nodes, 24.5, 7.5)
    assert nearest == "LOBBY", f"Expected LOBBY, got {nearest}"
    print("✓ Nearest node snapping works")


def test_destination_resolution():
    """Test that various destination formats resolve correctly."""
    engine = NavigationEngine()

    assert engine.resolve_destination("B-412") == "ROOM_412_DOOR"
    assert engine.resolve_destination("412") == "ROOM_412_DOOR"
    assert engine.resolve_destination("401") == "ROOM_401_DOOR"
    assert engine.resolve_destination("Meeting Room") == "ROOM_408_DOOR"
    assert engine.resolve_destination("Pantry") == "PANTRY"
    assert engine.resolve_destination("nonexistent") is None
    print("✓ Destination resolution works")


def test_navigate_full():
    """Test full navigation pipeline."""
    engine = NavigationEngine()
    result = engine.navigate(25.0, 2.0, "B-412")

    assert result["success"] is True
    assert len(result["path"]) > 0
    assert len(result["waypoints"]) > 0
    assert len(result["directions"]) > 0
    assert result["total_distance"] > 0
    assert result["directions_text"] != ""
    print(f"✓ Full navigation: Elevator → B-412")
    print(f"  Distance: {result['total_distance']}m")
    print(f"  Steps: {len(result['directions'])}")


def test_navigate_invalid_destination():
    """Test navigation with invalid destination."""
    engine = NavigationEngine()
    result = engine.navigate(25.0, 2.0, "Room XYZ")
    assert result["success"] is False
    assert "error" in result
    print("✓ Invalid destination handled gracefully")


def test_directions_generation():
    """Test turn-by-turn directions."""
    engine = NavigationEngine()
    result = engine.navigate(25.0, 2.0, "408")

    assert result["success"]
    directions = result["directions"]
    assert len(directions) >= 2  # At least start + arrival
    assert directions[0]["action"] == "start"
    assert directions[-1]["action"] == "arrived"
    print(f"✓ Directions generated: {len(directions)} steps")
    for d in directions:
        print(f"  → {d['instruction']}")


def test_bearing_computation():
    """Test compass bearing computation."""
    # Moving right (East)
    bearing = compute_bearing({"x": 0, "y": 0}, {"x": 10, "y": 0})
    assert 85 < bearing < 95, f"Expected ~90°, got {bearing}°"

    # Moving down (South)
    bearing = compute_bearing({"x": 0, "y": 0}, {"x": 0, "y": 10})
    assert 175 < bearing < 185, f"Expected ~180°, got {bearing}°"
    print("✓ Bearing computation works")


def test_turn_direction():
    """Test turn direction logic."""
    assert get_turn_direction(0, 90) == "right"
    assert get_turn_direction(0, 270) == "left"
    assert get_turn_direction(0, 10) == "straight"
    assert get_turn_direction(90, 90) == "straight"
    print("✓ Turn direction logic works")


def test_recalculate():
    """Test dynamic re-routing."""
    engine = NavigationEngine()
    # First navigate from elevator
    result1 = engine.navigate(25.0, 2.0, "B-412")
    assert result1["success"]

    # Simulate user has moved to lobby, recalculate
    result2 = engine.recalculate(25.0, 8.0, "B-412")
    assert result2["success"]
    # New path should be shorter
    assert result2["total_distance"] <= result1["total_distance"]
    print("✓ Dynamic re-routing works")


if __name__ == "__main__":
    print("=" * 60)
    print("NAVIGATION ENGINE - Test Suite")
    print("=" * 60)
    print()

    tests = [
        test_graph_loading,
        test_adjacency_list,
        test_euclidean_distance,
        test_astar_basic,
        test_astar_same_node,
        test_astar_all_destinations,
        test_find_nearest_node,
        test_destination_resolution,
        test_navigate_full,
        test_navigate_invalid_destination,
        test_directions_generation,
        test_bearing_computation,
        test_turn_direction,
        test_recalculate,
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
    print("=" * 60)

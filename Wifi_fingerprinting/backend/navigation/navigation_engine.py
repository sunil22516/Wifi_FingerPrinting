"""
Navigation Engine - Main Module
================================
Ties together the graph, A* algorithm, and direction generator.
Provides a clean interface for the frontend (Tripti) and localization (Tikam).

Usage:
    from navigation_engine import NavigationEngine
    engine = NavigationEngine()
    result = engine.navigate(start_x=25, start_y=2, destination="B-412")
"""

import json
import os
from typing import Optional

try:
    from .astar import astar, build_adjacency_list, find_nearest_node
    from .directions import generate_directions, get_total_distance, format_directions_text
except ImportError:
    from astar import astar, build_adjacency_list, find_nearest_node
    from directions import generate_directions, get_total_distance, format_directions_text


class NavigationEngine:
    """
    Main navigation engine class.
    Loads the floor graph and provides pathfinding + directions.
    """

    def __init__(self, graph_path: str = None):
        """
        Initialize the navigation engine by loading the floor graph.

        Parameters:
            graph_path: Path to graph.json file. Defaults to same directory.
        """
        if graph_path is None:
            graph_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph.json")

        with open(graph_path, "r", encoding="utf-8-sig") as f:
            self.graph_data = json.load(f)

        self.nodes = self.graph_data["nodes"]
        self.edges = self.graph_data["edges"]
        self.destinations = self.graph_data["destinations"]
        self.adjacency = build_adjacency_list(self.edges)

    def get_available_destinations(self) -> list:
        """Return list of all navigable destination names."""
        return sorted(self.destinations.keys())

    def resolve_destination(self, destination: str) -> Optional[str]:
        """
        Resolve a user-friendly destination name to a node ID.
        Handles room numbers like '412', 'B-412', 'Meeting Room', etc.
        """
        # Direct lookup
        if destination in self.destinations:
            return self.destinations[destination]

        # Case-insensitive lookup
        dest_lower = destination.lower().strip()
        for key, node_id in self.destinations.items():
            if key.lower() == dest_lower:
                return node_id

        # Partial match (e.g., "412" matches "B-412")
        for key, node_id in self.destinations.items():
            if dest_lower in key.lower() or key.lower() in dest_lower:
                return node_id

        return None

    def navigate(self, start_x: float, start_y: float, destination: str) -> dict:
        """
        Main navigation function — called by frontend/localization.

        Parameters:
            start_x: Current X coordinate from localization engine
            start_y: Current Y coordinate from localization engine
            destination: Destination name or room number (e.g., "B-412", "408", "Pantry")

        Returns:
            Dictionary with:
                - 'success': bool
                - 'path': list of node IDs
                - 'waypoints': list of {id, x, y, label} for drawing on map
                - 'directions': list of turn-by-turn instructions
                - 'directions_text': formatted text instructions
                - 'total_distance': total path distance in meters
                - 'start_node': resolved start node ID
                - 'end_node': resolved destination node ID
                - 'error': error message if success is False
        """
        # Resolve destination to node ID
        dest_node = self.resolve_destination(destination)
        if dest_node is None:
            return {
                "success": False,
                "error": f"Unknown destination: '{destination}'. Available: {', '.join(self.get_available_destinations())}",
                "path": [],
                "waypoints": [],
                "directions": [],
                "directions_text": "",
                "total_distance": 0
            }

        # Snap current position to nearest graph node
        start_node = find_nearest_node(self.nodes, start_x, start_y)

        # Run A* pathfinding
        result = astar(self.nodes, self.adjacency, start_node, dest_node)

        if result is None:
            return {
                "success": False,
                "error": f"No path found from {start_node} to {dest_node}. The destination may be unreachable.",
                "path": [],
                "waypoints": [],
                "directions": [],
                "directions_text": "",
                "total_distance": 0,
                "start_node": start_node,
                "end_node": dest_node
            }

        # Generate turn-by-turn directions
        directions = generate_directions(result["waypoints"])
        directions_text = format_directions_text(directions)

        return {
            "success": True,
            "path": result["path"],
            "waypoints": result["waypoints"],
            "directions": directions,
            "directions_text": directions_text,
            "total_distance": result["total_distance"],
            "start_node": start_node,
            "end_node": dest_node,
            "error": None
        }

    def navigate_by_nodes(self, start_node: str, end_node: str) -> dict:
        """
        Navigate between two known node IDs directly.
        Useful when start/end are already resolved (e.g., from dropdown selection).
        """
        if start_node not in self.nodes:
            return {"success": False, "error": f"Start node '{start_node}' not found in graph"}
        if end_node not in self.nodes:
            return {"success": False, "error": f"End node '{end_node}' not found in graph"}

        result = astar(self.nodes, self.adjacency, start_node, end_node)

        if result is None:
            return {
                "success": False,
                "error": f"No path found from {start_node} to {end_node}",
                "path": [],
                "waypoints": [],
                "directions": [],
                "directions_text": "",
                "total_distance": 0
            }

        directions = generate_directions(result["waypoints"])
        directions_text = format_directions_text(directions)

        return {
            "success": True,
            "path": result["path"],
            "waypoints": result["waypoints"],
            "directions": directions,
            "directions_text": directions_text,
            "total_distance": result["total_distance"],
            "start_node": start_node,
            "end_node": end_node,
            "error": None
        }

    def recalculate(self, current_x: float, current_y: float, destination: str) -> dict:
        """
        Recalculate route from new position (for dynamic re-routing).
        Called when localization detects user has deviated from path.
        """
        return self.navigate(current_x, current_y, destination)


# === Convenience function for direct use ===
def get_navigation(start_x: float, start_y: float, destination: str) -> dict:
    """
    Standalone function for quick navigation queries.
    Creates engine instance and returns navigation result.
    """
    engine = NavigationEngine()
    return engine.navigate(start_x, start_y, destination)


if __name__ == "__main__":
    # Quick demo/test
    engine = NavigationEngine()

    print("=" * 60)
    print("NAVIGATION ENGINE - Demo")
    print("=" * 60)
    print(f"\nAvailable destinations: {engine.get_available_destinations()}")

    # Simulate: User is at elevator (x=25, y=2), wants to go to B-412
    print("\n--- Navigating from Elevator to Room B-412 ---")
    result = engine.navigate(start_x=25.0, start_y=2.0, destination="B-412")

    if result["success"]:
        print(f"\nPath: {' → '.join(result['path'])}")
        print(f"Total distance: {result['total_distance']} meters")
        print(f"\nDirections:")
        print(result["directions_text"])
    else:
        print(f"Error: {result['error']}")

    # Another test: Elevator to Meeting Room
    print("\n--- Navigating from Elevator to Meeting Room (408) ---")
    result = engine.navigate(start_x=25.0, start_y=2.0, destination="Meeting Room")

    if result["success"]:
        print(f"\nPath: {' → '.join(result['path'])}")
        print(f"Total distance: {result['total_distance']} meters")
        print(f"\nDirections:")
        print(result["directions_text"])
    else:
        print(f"Error: {result['error']}")

"""
A* (A-Star) Pathfinding Algorithm Implementation
=================================================
Navigation Engine for WiFi Indoor Localization Project
Author: Sunil (Navigation Module)

This module implements the A* pathfinding algorithm on a graph
representing the 4th floor of the R&D building.

Algorithm Overview:
- f(n) = g(n) + h(n)
  - g(n): actual cost from start to current node (sum of edge weights)
  - h(n): heuristic estimate (Euclidean distance) from current node to goal
- Explores nodes with lowest f(n) first
- Guarantees shortest path when heuristic is admissible (never overestimates)
"""

import heapq
import math
from typing import Optional


def euclidean_distance(node_a: dict, node_b: dict) -> float:
    """
    Compute Euclidean distance between two nodes.
    Used as the heuristic h(n) for A*.
    This is admissible because straight-line distance never overestimates
    the actual walking distance.
    """
    dx = node_a["x"] - node_b["x"]
    dy = node_a["y"] - node_b["y"]
    return math.sqrt(dx * dx + dy * dy)


def build_adjacency_list(edges: list) -> dict:
    """
    Convert edge list to adjacency list representation.
    Returns: {node_id: [(neighbor_id, weight), ...]}
    """
    adj = {}
    for edge in edges:
        from_node = edge["from"]
        to_node = edge["to"]
        weight = edge["weight"]

        if from_node not in adj:
            adj[from_node] = []
        adj[from_node].append((to_node, weight))

        # Add reverse edge if bidirectional
        if edge.get("bidirectional", True):
            if to_node not in adj:
                adj[to_node] = []
            adj[to_node].append((from_node, weight))

    return adj


def astar(nodes: dict, adjacency: dict, start_id: str, goal_id: str) -> Optional[dict]:
    """
    A* pathfinding algorithm.

    Parameters:
        nodes: Dictionary of node_id -> {x, y, label, type, ...}
        adjacency: Adjacency list {node_id: [(neighbor_id, weight), ...]}
        start_id: Starting node ID
        goal_id: Destination node ID

    Returns:
        Dictionary with:
            - 'path': ordered list of node IDs from start to goal
            - 'total_distance': total path distance in meters
            - 'waypoints': list of {id, x, y, label} for each node in path
        Or None if no path exists.
    """
    if start_id not in nodes:
        raise ValueError(f"Start node '{start_id}' not found in graph")
    if goal_id not in nodes:
        raise ValueError(f"Goal node '{goal_id}' not found in graph")

    # If start == goal, return trivial path
    if start_id == goal_id:
        node = nodes[start_id]
        return {
            "path": [start_id],
            "total_distance": 0.0,
            "waypoints": [{"id": start_id, "x": node["x"], "y": node["y"], "label": node.get("label", start_id)}]
        }

    goal_node = nodes[goal_id]

    # Priority queue: (f_score, counter, node_id)
    # counter is used to break ties in heap ordering
    open_set = []
    counter = 0
    heapq.heappush(open_set, (0, counter, start_id))

    # Track the best path to each node
    came_from = {}  # node_id -> previous node_id

    # g_score: actual cost from start to node
    g_score = {start_id: 0.0}

    # f_score: g_score + heuristic
    f_score = {start_id: euclidean_distance(nodes[start_id], goal_node)}

    # Set of nodes already evaluated
    closed_set = set()

    while open_set:
        current_f, _, current = heapq.heappop(open_set)

        # Skip if already processed (duplicate in heap)
        if current in closed_set:
            continue

        # Goal reached — reconstruct path
        if current == goal_id:
            path = _reconstruct_path(came_from, current)
            total_dist = g_score[current]
            waypoints = []
            for node_id in path:
                n = nodes[node_id]
                waypoints.append({
                    "id": node_id,
                    "x": n["x"],
                    "y": n["y"],
                    "label": n.get("label", node_id)
                })
            return {
                "path": path,
                "total_distance": round(total_dist, 2),
                "waypoints": waypoints
            }

        closed_set.add(current)

        # Explore neighbors
        for neighbor, edge_weight in adjacency.get(current, []):
            if neighbor in closed_set:
                continue

            tentative_g = g_score[current] + edge_weight

            # If this path to neighbor is better than any previous one
            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + euclidean_distance(nodes[neighbor], goal_node)
                f_score[neighbor] = f
                counter += 1
                heapq.heappush(open_set, (f, counter, neighbor))

    # No path found
    return None


def _reconstruct_path(came_from: dict, current: str) -> list:
    """Backtrack from goal to start using came_from map."""
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def find_nearest_node(nodes: dict, x: float, y: float) -> str:
    """
    Given an X,Y coordinate (from localization), find the nearest node in the graph.
    This is used to 'snap' the localized position to the graph for navigation.

    Parameters:
        nodes: Dictionary of node_id -> {x, y, ...}
        x, y: Current position coordinates from localization engine

    Returns:
        Node ID of the closest node
    """
    min_dist = float('inf')
    nearest = None
    for node_id, node_data in nodes.items():
        dist = math.sqrt((node_data["x"] - x) ** 2 + (node_data["y"] - y) ** 2)
        if dist < min_dist:
            min_dist = dist
            nearest = node_id
    return nearest

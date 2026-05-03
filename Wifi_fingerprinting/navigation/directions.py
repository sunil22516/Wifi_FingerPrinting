"""
Turn-by-Turn Direction Generator
=================================
Converts a path (list of waypoints) into human-readable navigation instructions.

Uses vector math to determine turn directions (left/right/straight)
by computing the angle between consecutive path segments.
"""

import math
from typing import List


def compute_bearing(from_point: dict, to_point: dict) -> float:
    """
    Compute the bearing (angle in degrees) from one point to another.
    0° = North (up), 90° = East (right), 180° = South, 270° = West.
    """
    dx = to_point["x"] - from_point["x"]
    dy = to_point["y"] - from_point["y"]
    # Note: In our coordinate system, Y increases downward
    # atan2 gives angle from positive X axis, we convert to compass bearing
    angle = math.atan2(dx, -dy)  # negative dy because Y increases downward
    bearing = math.degrees(angle) % 360
    return bearing


def get_turn_direction(bearing_before: float, bearing_after: float) -> str:
    """
    Determine the turn direction based on change in bearing.

    Returns one of: 'straight', 'slight left', 'left', 'sharp left',
                    'slight right', 'right', 'sharp right', 'u-turn'
    """
    # Calculate the angle difference (how much we turn)
    diff = (bearing_after - bearing_before + 360) % 360

    if diff <= 20 or diff >= 340:
        return "straight"
    elif 20 < diff <= 60:
        return "slight right"
    elif 60 < diff <= 120:
        return "right"
    elif 120 < diff <= 160:
        return "sharp right"
    elif 160 < diff <= 200:
        return "u-turn"
    elif 200 < diff <= 240:
        return "sharp left"
    elif 240 < diff <= 300:
        return "left"
    elif 300 < diff < 340:
        return "slight left"
    else:
        return "straight"


def compute_distance(point_a: dict, point_b: dict) -> float:
    """Compute distance between two waypoints in meters."""
    dx = point_a["x"] - point_b["x"]
    dy = point_a["y"] - point_b["y"]
    return math.sqrt(dx * dx + dy * dy)


def generate_directions(waypoints: List[dict]) -> List[dict]:
    """
    Generate turn-by-turn navigation instructions from a list of waypoints.

    Parameters:
        waypoints: Ordered list of {id, x, y, label} from A* output

    Returns:
        List of direction steps, each containing:
            - 'instruction': Human-readable text (e.g., "Turn left and walk 8 meters")
            - 'distance': Distance for this segment in meters
            - 'action': The action type ('start', 'straight', 'left', 'right', etc.)
            - 'waypoint': The target waypoint for this step
    """
    if not waypoints or len(waypoints) < 2:
        return [{"instruction": "You are already at your destination.", "distance": 0, "action": "arrived", "waypoint": waypoints[0] if waypoints else None}]

    directions = []

    # First instruction: Start
    dist_first = compute_distance(waypoints[0], waypoints[1])
    directions.append({
        "instruction": f"Start at {waypoints[0]['label']}. Walk towards {waypoints[1]['label']} ({dist_first:.0f}m).",
        "distance": round(dist_first, 1),
        "action": "start",
        "waypoint": waypoints[0]
    })

    # Middle instructions: Turns and straight segments
    for i in range(1, len(waypoints) - 1):
        prev = waypoints[i - 1]
        curr = waypoints[i]
        next_wp = waypoints[i + 1]

        bearing_in = compute_bearing(prev, curr)
        bearing_out = compute_bearing(curr, next_wp)
        turn = get_turn_direction(bearing_in, bearing_out)
        dist = compute_distance(curr, next_wp)

        # Build instruction text
        if turn == "straight":
            instruction = f"Continue straight past {curr['label']} towards {next_wp['label']} ({dist:.0f}m)."
        elif turn == "u-turn":
            instruction = f"At {curr['label']}, make a U-turn towards {next_wp['label']} ({dist:.0f}m)."
        else:
            instruction = f"At {curr['label']}, turn {turn} towards {next_wp['label']} ({dist:.0f}m)."

        directions.append({
            "instruction": instruction,
            "distance": round(dist, 1),
            "action": turn,
            "waypoint": curr
        })

    # Final instruction: Arrival
    final = waypoints[-1]
    directions.append({
        "instruction": f"You have arrived at {final['label']}. It will be on your {'left' if final.get('x', 0) < waypoints[-2].get('x', 0) else 'right'} side.",
        "distance": 0,
        "action": "arrived",
        "waypoint": final
    })

    return directions


def get_total_distance(waypoints: List[dict]) -> float:
    """Calculate total walking distance along the path."""
    total = 0.0
    for i in range(len(waypoints) - 1):
        total += compute_distance(waypoints[i], waypoints[i + 1])
    return round(total, 1)


def format_directions_text(directions: List[dict]) -> str:
    """Format directions as a simple numbered text list for display."""
    lines = []
    for i, step in enumerate(directions, 1):
        lines.append(f"{i}. {step['instruction']}")
    return "\n".join(lines)

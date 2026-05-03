

"""
Build radio_map.json from real fingerprints.csv data.
Run once to generate the fingerprint database used by the localization engine.
"""
import json
import os
from collections import defaultdict

# -----------------------------------------------------------------------
# Coordinate assignment for each fingerprinted location
# (x=east direction, y=south direction, origin=top-left corner)
# Layout: B-wing rooms on north side (left), lift + open areas mid,
#         A-wing rooms on north side (right), labs on south side.
# -----------------------------------------------------------------------
BUILDING_WIDTH_M = 120.0
BUILDING_DEPTH_M = 25.0

CORRIDOR_Y = 8.0
NORTH_Y = 3.0
SOUTH_Y = 13.0
DISCUSS_Y = 19.0
LIFT_Y = 5.0


def normalize_location_key(raw: str) -> str:
    key = raw.strip().lower()
    key = key.replace("-", "_")
    key = key.replace(" ", "_")
    return key


LOCATION_COORDS = {}

# B-wing rooms (B401-B412) on north side
B_ROOM_X_START = 6.0
B_ROOM_STEP = 4.0
for idx, room_num in enumerate(range(401, 413)):
    x = B_ROOM_X_START + idx * B_ROOM_STEP
    key = f"b{room_num}"
    LOCATION_COORDS[key] = {
        "x": x,
        "y": NORTH_Y,
        "label": f"Room B-{room_num}",
        "type": "room",
        "room_number": f"B-{room_num}"
    }

# A-wing rooms (A401-A412, no A411)
A_ROOM_NUMS = [401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 412]
A_ROOM_X_START = 72.0
A_ROOM_STEP = 4.0
for idx, room_num in enumerate(A_ROOM_NUMS):
    x = A_ROOM_X_START + idx * A_ROOM_STEP
    key = f"a{room_num}"
    LOCATION_COORDS[key] = {
        "x": x,
        "y": NORTH_Y,
        "label": f"Room A-{room_num}",
        "type": "room",
        "room_number": f"A-{room_num}"
    }

# Common / landmarks and labs
LOCATION_COORDS.update({
    "lift_area":     {"x": 62.0, "y": LIFT_Y,   "label": "Lift / Elevator Area", "type": "landmark"},
    "open_area":     {"x": 60.0, "y": CORRIDOR_Y, "label": "Open Area (Center)",  "type": "corridor"},
    "open_area_1b":  {"x": 54.0, "y": CORRIDOR_Y, "label": "Open Area 1 (B-Wing)", "type": "corridor"},
    "open_area_2b":  {"x": 68.0, "y": CORRIDOR_Y, "label": "Open Area 2 (Near Lift)", "type": "corridor"},
    "washroom":      {"x": 70.0, "y": SOUTH_Y, "label": "Washroom",              "type": "landmark"},

    "design_studio": {"x": 10.0, "y": SOUTH_Y, "label": "Design Studio",         "type": "room", "room_number": "Design-Studio"},
    "aid_lab":       {"x": 22.0, "y": SOUTH_Y, "label": "AID Lab",               "type": "room", "room_number": "AID-Lab"},
    "ci_lab":        {"x": 30.0, "y": SOUTH_Y, "label": "CI Lab",                "type": "room", "room_number": "CI-Lab"},
    "dcl_lab":       {"x": 42.0, "y": SOUTH_Y, "label": "DCL Lab",               "type": "room", "room_number": "DCL-Lab"},
    "midas_lab":     {"x": 84.0, "y": SOUTH_Y, "label": "MIDAS Lab",             "type": "room", "room_number": "MIDAS-Lab"},
    "iras_lab":      {"x": 96.0, "y": SOUTH_Y, "label": "IRAS Lab",              "type": "room", "room_number": "IRAS-Lab"},
    "hmi_lab":       {"x": 108.0, "y": SOUTH_Y, "label": "HMI Lab",              "type": "room", "room_number": "HMI-Lab"},

    "discussion_room_1a": {"x": 22.0, "y": DISCUSS_Y, "label": "Discussion Room 1", "type": "room", "room_number": "Disc-Room-1"},
    "discussion_room_2a": {"x": 34.0, "y": DISCUSS_Y, "label": "Discussion Room 2", "type": "room", "room_number": "Disc-Room-2"},
})

def build_radio_map(csv_path: str, out_path: str):
    # Parse CSV - format: date,location,bssid1:rssi1,bssid2:rssi2,...
    agg = defaultdict(lambda: defaultdict(list))

    unknown_locations = set()
    with open(csv_path, newline="", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 3:
                continue
            location_raw = parts[1].strip()
            location = normalize_location_key(location_raw)
            if location not in LOCATION_COORDS:
                unknown_locations.add(location_raw)
                continue  # skip unknown / placeholder rows
            for field in parts[2:]:
                field = field.strip()
                if not field:
                    continue
                # bssid is always 17 chars (AA:BB:CC:DD:EE:FF) so rssi starts at index 18
                idx = field.rfind(":")
                if idx == -1:
                    continue
                bssid = field[:idx]
                rssi_str = field[idx + 1:]
                try:
                    rssi = int(rssi_str)
                    agg[location][bssid].append(rssi)
                except ValueError:
                    continue

    # Build fingerprints – one averaged entry per unique location
    merged = {}  # location_id -> {x, y, label, type, bssid_map}
    for location, bssid_map in agg.items():
        coords = LOCATION_COORDS[location]
        if location not in merged:
            merged[location] = {
                "x": coords["x"],
                "y": coords["y"],
                "label": coords["label"],
                "location_id": location,
                "bssid_map": defaultdict(list)
            }
        for bssid, rssi_list in bssid_map.items():
            merged[location]["bssid_map"][bssid].extend(rssi_list)

    fingerprints = []
    for key, data in merged.items():
        wifi_readings = {}
        for bssid, rssi_list in data["bssid_map"].items():
            avg = round(sum(rssi_list) / len(rssi_list))
            wifi_readings[bssid] = {"rssi": avg, "num_samples": len(rssi_list)}
        fp = {
            "x": data["x"],
            "y": data["y"],
            "label": data["label"],
            "location_id": data["location_id"],
            "wifi_readings": wifi_readings
        }
        fingerprints.append(fp)
        print(f"  {data['label']:35s} ({data['x']:5.1f}, {data['y']:5.1f})  –  {len(wifi_readings)} APs")

    radio_map = {
        "metadata": {
            "floor": "4th Floor, R&D Building, IIIT Delhi",
            "wing": "A + B Wing",
            "coordinate_system": "meters from top-left corner of floor plan",
            "building_width_m": BUILDING_WIDTH_M,
            "building_depth_m": BUILDING_DEPTH_M,
            "note": "Built from real fingerprints collected on 2026-04-09",
            "num_locations": len(fingerprints)
        },
        "fingerprints": fingerprints
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(radio_map, f, indent=2)
    if unknown_locations:
        print("\nSkipped unknown locations:")
        for loc in sorted(unknown_locations):
            print(f"  - {loc}")

    print(f"\nWrote {len(fingerprints)} fingerprints → {out_path}")


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    full_csv = os.path.normpath(os.path.join(base, "..", "fingerprints.csv"))
    legacy_csv = os.path.join(base, "fingerprints_Awing.csv")
    csv_path = full_csv if os.path.exists(full_csv) else legacy_csv

    build_radio_map(
        csv_path=csv_path,
        out_path=os.path.join(base, "data_collection", "sample_data", "radio_map.json")
    )

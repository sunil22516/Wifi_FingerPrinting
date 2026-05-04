"""
Build radio_map.json from fingerprintsnew.csv
=============================================
Updated to cover the full 4th floor:
  - B-Wing: B-wing faculty rooms, labs (DCL, IRAS), discussion rooms, open areas
  - Central Junction: Open Meeting area, Lift area
  - A-Wing: A-wing faculty rooms, named labs (Design Studio, AID, CI, MIDAS, HMI)

Coordinate system: x=east, y=south, origin=top-left corner
  B-wing: x=0-58, Junction: x=58-68, A-wing: x=68-125

Run:
    python build_radio_map.py
"""

import json
import os
from collections import defaultdict

# -----------------------------------------------------------------------
# All fingerprinted locations → (x, y) real-world coordinates in metres
# Matches the full 4th-floor layout in graph_new.json
# -----------------------------------------------------------------------
LOCATION_COORDS = {
    # ── B-Wing North Faculty Rooms ───────────────────────────────────────
    "B412":            {"x":  2.0, "y":  3.0, "label": "Room B-412",       "type": "room"},
    "B411":            {"x":  6.0, "y":  3.0, "label": "Room B-411",       "type": "room"},
    "B410":            {"x": 10.0, "y":  3.0, "label": "Room B-410",       "type": "room"},
    "B409":            {"x": 18.0, "y":  3.0, "label": "Room B-409",       "type": "room"},
    "B408":            {"x": 22.0, "y":  3.0, "label": "Room B-408",       "type": "room"},
    "B407":            {"x": 26.0, "y":  3.0, "label": "Room B-407",       "type": "room"},
    "B406":            {"x": 30.0, "y":  3.0, "label": "Room B-406",       "type": "room"},
    "B405":            {"x": 34.0, "y":  3.0, "label": "Room B-405",       "type": "room"},
    "B404":            {"x": 43.0, "y":  3.0, "label": "Room B-404",       "type": "room"},
    "B403":            {"x": 47.0, "y":  3.0, "label": "Room B-403",       "type": "room"},
    "B402":            {"x": 51.0, "y":  3.0, "label": "Room B-402",       "type": "room"},
    "B401":            {"x": 55.0, "y":  3.0, "label": "Room B-401",       "type": "room"},

    # ── B-Wing Corridor Open Areas ────────────────────────────────────────
    "Open_Area_1B":    {"x": 14.0, "y":  8.0, "label": "Open Area 1B",     "type": "corridor"},
    "Open_Area_2B":    {"x": 38.0, "y":  8.0, "label": "Open Area 2B",     "type": "corridor"},

    # ── B-Wing South Labs ────────────────────────────────────────────────
    "dcl_lab":         {"x":  6.0, "y": 16.0, "label": "DCL Lab",          "type": "room"},
    "iras_lab":        {"x": 44.0, "y": 16.0, "label": "IRAS Lab",         "type": "room"},

    # ── Central Junction / Lift ──────────────────────────────────────────
    "lift_area":       {"x": 64.0, "y":  5.0, "label": "Lift / Elevator",  "type": "landmark"},
    "open-area":       {"x": 64.0, "y":  8.0, "label": "Open Area (Lift)", "type": "corridor"},

    # ── A-Wing North Faculty Rooms ───────────────────────────────────────
    "A401":            {"x": 70.0, "y":  3.0, "label": "Room A-401",       "type": "room"},
    "A402":            {"x": 74.0, "y":  3.0, "label": "Room A-402",       "type": "room"},
    "A403":            {"x": 78.0, "y":  3.0, "label": "Room A-403",       "type": "room"},
    "A404":            {"x": 86.0, "y":  3.0, "label": "Room A-404",       "type": "room"},
    "A405":            {"x": 90.0, "y":  3.0, "label": "Room A-405",       "type": "room"},
    "A407":            {"x": 98.0, "y":  3.0, "label": "Room A-407",       "type": "room"},
    "A408":            {"x":102.0, "y":  3.0, "label": "Room A-408",       "type": "room"},
    "A409":            {"x":106.0, "y":  3.0, "label": "Room A-409",       "type": "room"},
    "A410":            {"x":110.0, "y":  3.0, "label": "Room A-410",       "type": "room"},
    "A412":            {"x":118.0, "y":  3.0, "label": "Room A-412",       "type": "room"},

    # ── A-Wing Named Labs (south side) ────────────────────────────────────
    "design_studio":   {"x": 71.0, "y": 16.0, "label": "Design Studio",   "type": "room"},
    "design-studio":   {"x": 71.0, "y": 16.0, "label": "Design Studio",   "type": "room"},
    "aid_lab":         {"x": 78.0, "y": 16.0, "label": "AID Lab",         "type": "room"},
    "ci_lab":          {"x": 90.0, "y": 16.0, "label": "CI Lab",          "type": "room"},
    "midas_lab":       {"x":100.0, "y": 16.0, "label": "MIDAS Lab",       "type": "room"},
    "hmi_lab":         {"x":110.0, "y": 16.0, "label": "HMI Lab",         "type": "room"},

    # ── A-Wing Discussion Rooms ──────────────────────────────────────────
    "Discussion_Room_1A": {"x": 78.0, "y": 20.0, "label": "Discussion Room 1A", "type": "room"},
    "Discussion_room_2A": {"x": 96.0, "y": 20.0, "label": "Discussion Room 2A", "type": "room"},
}


def build_radio_map(csv_path: str, out_path: str):
    """
    Parse the CSV fingerprint file and produce a radio_map.json.

    CSV format (per row):
        timestamp, location_label, mac1:rssi1, mac2:rssi2, mac3:rssi3, ...

    The MAC+RSSI are encoded as a single token like '72:7f:f0:12:cf:83:-70'
    where the 7th colon-separated field is the RSSI integer.
    """
    agg = defaultdict(lambda: defaultdict(list))   # location → {bssid: [rssi, ...]}
    skipped_locations = set()

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f):
            parts = line.strip().split(",")
            if len(parts) < 3:
                continue
            location = parts[1].strip()
            if location not in LOCATION_COORDS:
                skipped_locations.add(location)
                continue
            for field in parts[2:]:
                field = field.strip()
                if not field:
                    continue
                # Format: "AA:BB:CC:DD:EE:FF:-70"  → last colon separates MAC from RSSI
                idx = field.rfind(":")
                if idx == -1:
                    continue
                bssid = field[:idx].lower()
                rssi_str = field[idx + 1:]
                try:
                    rssi = int(rssi_str)
                    agg[location][bssid].append(rssi)
                except ValueError:
                    continue

    if skipped_locations:
        print(f"  [warn] Skipped unknown locations: {sorted(skipped_locations)}")

    # Merge entries that share the same label (e.g., design_studio + design-studio)
    merged = {}   # canonical_label → entry
    for location, bssid_map in agg.items():
        coords = LOCATION_COORDS[location]
        key = coords["label"]
        if key not in merged:
            merged[key] = {
                "x": coords["x"],
                "y": coords["y"],
                "label": coords["label"],
                "location_id": location,
                "bssid_map": defaultdict(list)
            }
        for bssid, rssi_list in bssid_map.items():
            merged[key]["bssid_map"][bssid].extend(rssi_list)

    # Average RSSI per BSSID per location
    fingerprints = []
    for key, data in sorted(merged.items(), key=lambda kv: (kv[1]["x"], kv[1]["y"])):
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
        print(f"  {data['label']:35s}  ({data['x']:6.1f}, {data['y']:5.1f})  – {len(wifi_readings)} APs")

    radio_map = {
        "metadata": {
            "floor": "4th Floor, R&D Building, IIIT Delhi",
            "wings": "B-Wing + Junction + A-Wing",
            "coordinate_system": "meters from top-left corner",
            "building_width_m": 125,
            "building_depth_m": 22,
            "source_csv": os.path.basename(csv_path),
            "num_locations": len(fingerprints)
        },
        "fingerprints": fingerprints
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(radio_map, f, indent=2)
    print(f"\n✓ Wrote {len(fingerprints)} fingerprints → {out_path}")


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    build_radio_map(
        csv_path=os.path.join(base, "fingerprintsnew.csv"),
        out_path=os.path.join(base, "data_collection", "sample_data", "radio_map.json")
    )

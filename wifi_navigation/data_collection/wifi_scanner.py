"""
WiFi Scanner Module
====================
Scans nearby WiFi access points and returns RSSI (signal strength) values.
Works on Windows, Linux, and macOS.

Author: Mayank (Data Collection)

Usage:
    from wifi_scanner import scan_wifi
    results = scan_wifi()
    # Returns: [{"bssid": "AA:BB:CC:DD:EE:FF", "ssid": "NetworkName", "rssi": -45}, ...]
"""

import subprocess
import platform
import re
from typing import List, Dict

# Try to import pywifi for accurate dBm readings on Windows/Linux
try:
    import pywifi
    _PYWIFI_AVAILABLE = True
except ImportError:
    _PYWIFI_AVAILABLE = False


def scan_wifi() -> List[Dict]:
    """
    Scan for available WiFi networks and return their signal strengths.

    Returns:
        List of dictionaries with keys: bssid, ssid, rssi
        RSSI is in dBm (negative values, closer to 0 = stronger signal)

    Priority:
        1. pywifi library  – gives actual dBm, works on Windows/Linux
        2. OS-native tools – fallback (netsh / nmcli / airport)
    """
    # Preferred: pywifi gives real dBm values matching the training data
    if _PYWIFI_AVAILABLE:
        try:
            return _scan_pywifi()
        except Exception:
            pass  # fall through to OS-native

    system = platform.system()
    if system == "Windows":
        return _scan_windows()
    elif system == "Linux":
        return _scan_linux()
    elif system == "Darwin":
        return _scan_macos()
    else:
        raise OSError(f"Unsupported OS: {system}")


def _scan_pywifi() -> List[Dict]:
    """
    Scan using pywifi library – returns actual RSSI dBm values.
    Install with: pip install pywifi comtypes (Windows) or pip install pywifi (Linux)
    """
    wifi = pywifi.PyWiFi()
    iface = wifi.interfaces()[0]
    iface.scan()
    import time
    time.sleep(2)  # wait for scan to complete
    results = iface.scan_results()
    networks = []
    for profile in results:
        bssid = profile.bssid.lower().strip()
        ssid = profile.ssid or ""
        rssi = int(profile.signal)  # already in dBm
        networks.append({"bssid": bssid, "ssid": ssid, "rssi": rssi})
    return networks


def _scan_windows() -> List[Dict]:
    """Scan WiFi on Windows using netsh."""
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout
        
        networks = []
        current_network = {}
        
        for line in output.split("\n"):
            line = line.strip()
            
            if line.startswith("SSID") and "BSSID" not in line:
                if current_network.get("bssid"):
                    networks.append(current_network)
                ssid = line.split(":", 1)[1].strip() if ":" in line else ""
                current_network = {"ssid": ssid, "bssid": "", "rssi": -100}
                
            elif "BSSID" in line:
                bssid = line.split(":", 1)[1].strip()
                current_network["bssid"] = bssid
                
            elif "Signal" in line:
                # Windows reports signal as quality percentage (0-100%)
                match = re.search(r"(\d+)%", line)
                if match:
                    percentage = int(match.group(1))
                    # Standard conversion: quality = 2*(rssi+100) → rssi = quality/2 - 100
                    # Clamped to realistic indoor range [-30, -90]
                    rssi = max(-90, min(-30, int(percentage / 2) - 100))
                    current_network["rssi"] = rssi
        
        # Don't forget the last network
        if current_network.get("bssid"):
            networks.append(current_network)
        
        return networks
        
    except subprocess.TimeoutExpired:
        print("WiFi scan timed out")
        return []
    except Exception as e:
        print(f"WiFi scan error: {e}")
        return []


def _scan_linux() -> List[Dict]:
    """Scan WiFi on Linux using iwlist or nmcli."""
    try:
        # Try nmcli first (more modern)
        result = subprocess.run(
            ["nmcli", "-t", "-f", "BSSID,SSID,SIGNAL", "dev", "wifi", "list", "--rescan", "yes"],
            capture_output=True, text=True, timeout=15
        )
        
        networks = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split(":")
            if len(parts) >= 8:  # BSSID has colons
                # Reconstruct BSSID (first 6 colon-separated parts)
                bssid = ":".join(parts[:6]).lower()
                ssid = parts[6] if len(parts) > 6 else ""
                signal_str = parts[-1].strip() if parts[-1].strip().lstrip("-").isdigit() else "0"
                signal_val = int(signal_str)
                # nmcli -f SIGNAL returns percentage (0-100); convert to dBm
                if signal_val > 0:  # percentage
                    rssi = max(-90, min(-30, int(signal_val / 2) - 100))
                else:  # already dBm (negative)
                    rssi = signal_val
                networks.append({"bssid": bssid, "ssid": ssid, "rssi": rssi})
        
        return networks
        
    except FileNotFoundError:
        # Fallback to iwlist
        try:
            result = subprocess.run(
                ["sudo", "iwlist", "wlan0", "scan"],
                capture_output=True, text=True, timeout=15
            )
            return _parse_iwlist(result.stdout)
        except Exception:
            return []
    except Exception as e:
        print(f"WiFi scan error: {e}")
        return []


def _parse_iwlist(output: str) -> List[Dict]:
    """Parse iwlist scan output."""
    networks = []
    current = {}
    
    for line in output.split("\n"):
        line = line.strip()
        if "Cell" in line and "Address:" in line:
            if current.get("bssid"):
                networks.append(current)
            bssid = line.split("Address:")[1].strip()
            current = {"bssid": bssid, "ssid": "", "rssi": -100}
        elif "ESSID:" in line:
            ssid = line.split("ESSID:")[1].strip().strip('"')
            current["ssid"] = ssid
        elif "Signal level=" in line:
            match = re.search(r"Signal level[=:](-?\d+)", line)
            if match:
                current["rssi"] = int(match.group(1))
    
    if current.get("bssid"):
        networks.append(current)
    
    return networks


def _scan_macos() -> List[Dict]:
    """Scan WiFi on macOS using airport utility."""
    try:
        airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        result = subprocess.run(
            [airport_path, "-s"],
            capture_output=True, text=True, timeout=10
        )
        
        networks = []
        lines = result.stdout.strip().split("\n")
        
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 3:
                ssid = parts[0]
                # Find BSSID (MAC address pattern)
                bssid_match = re.search(r"([0-9a-fA-F:]{17})", line)
                rssi_match = re.search(r"(-\d+)", line)
                
                if bssid_match and rssi_match:
                    networks.append({
                        "bssid": bssid_match.group(1),
                        "ssid": ssid,
                        "rssi": int(rssi_match.group(1))
                    })
        
        return networks
        
    except Exception as e:
        print(f"WiFi scan error: {e}")
        return []


def scan_wifi_multiple(num_scans: int = 5) -> List[Dict]:
    """
    Perform multiple WiFi scans and average the RSSI values.
    This reduces noise in signal strength measurements.
    
    Parameters:
        num_scans: Number of scans to average
        
    Returns:
        List of networks with averaged RSSI values
    """
    import time
    
    all_readings = {}  # bssid -> list of rssi values
    
    for i in range(num_scans):
        networks = scan_wifi()
        for net in networks:
            bssid = net["bssid"]
            if bssid not in all_readings:
                all_readings[bssid] = {"ssid": net["ssid"], "rssi_values": []}
            all_readings[bssid]["rssi_values"].append(net["rssi"])
        
        if i < num_scans - 1:
            time.sleep(0.5)  # Small delay between scans
    
    # Average the readings
    averaged = []
    for bssid, data in all_readings.items():
        avg_rssi = sum(data["rssi_values"]) / len(data["rssi_values"])
        averaged.append({
            "bssid": bssid,
            "ssid": data["ssid"],
            "rssi": round(avg_rssi),
            "num_readings": len(data["rssi_values"])
        })
    
    return averaged


if __name__ == "__main__":
    print("Scanning WiFi networks...")
    networks = scan_wifi()
    print(f"\nFound {len(networks)} networks:\n")
    print(f"{'BSSID':<20} {'SSID':<25} {'RSSI (dBm)':<10}")
    print("-" * 55)
    for net in sorted(networks, key=lambda x: x["rssi"], reverse=True):
        print(f"{net['bssid']:<20} {net['ssid']:<25} {net['rssi']}")

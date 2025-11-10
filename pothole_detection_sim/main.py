#!/usr/bin/env python3
"""
generate_live_route.py

Reads a KML (supports <coordinates> and <gx:coord>), picks random potholes on the real route,
and writes an interactive HTML (Leaflet) that animates a car moving at 6 m/s and shows warnings.

Usage:
    python generate_live_route.py --kml "route.kml" --potholes 10 --warning 80

Output:
    live_route.html (open in browser)
"""

import re
import math
import random
import json
import argparse
from pathlib import Path

# ---------- CONFIG DEFAULTS ----------
DEFAULT_KML = "Directions from Wagheshwar Temple, Nagar Road, Wagholi, Pune, Maharashtra to MIT ADT UNIVERSITY, Loni Kalbhor, Maharashtra.kml"
OUTPUT_HTML = "live_route.html"
CAR_SPEED_MPS = 6.0          # car speed in meters / second
DEFAULT_NUM_POTHOLES = 10
WARNING_DISTANCE_M = 80      # show warning when within this many meters
# -------------------------------------


def extract_coords_from_kml_text(text):
    """
    Tries to extract coordinates from KML text.
    Returns list of (lat, lon) tuples in order.
    Handles:
      - <coordinates>lon,lat[,alt] ...</coordinates>
      - <gx:coord>lon lat [alt]</gx:coord>
    """
    coords = []

    # 1) try <gx:coord>
    gx = re.findall(r"<gx:coord>(.*?)</gx:coord>", text, re.S)
    if gx:
        for g in gx:
            parts = g.strip().split()
            if len(parts) >= 2:
                try:
                    lon = float(parts[0]); lat = float(parts[1])
                    coords.append((lat, lon))
                except:
                    continue

    # 2) try <coordinates> blocks (space or newline separated)
    if not coords:
        matches = re.findall(r"<coordinates>(.*?)</coordinates>", text, re.S)
        for m in matches:
            # coordinates blocks may have many "lon,lat,alt" tokens separated by whitespace
            tokens = m.strip().replace("\n", " ").split()
            for t in tokens:
                parts = t.split(",")
                if len(parts) >= 2:
                    try:
                        lon = float(parts[0]); lat = float(parts[1])
                        coords.append((lat, lon))
                    except:
                        continue

    return coords


def haversine_m(a, b):
    """Return meters between two (lat, lon) points."""
    lat1, lon1 = a; lat2, lon2 = b
    R = 6371000.0
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1); dlambda = math.radians(lon2 - lon1)
    aa = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(aa), math.sqrt(1-aa))


def resample_route_to_reasonable_points(route, max_segment_m=8.0):
    """
    The KML may have long gaps; for smooth animation we resample so each segment < max_segment_m.
    route: list of (lat, lon)
    Returns new list of (lat, lon)
    """
    new = []
    for i in range(len(route)-1):
        a = route[i]; b = route[i+1]
        d = haversine_m(a, b)
        steps = max(1, int(math.ceil(d / max_segment_m)))
        for s in range(steps):
            t = s / steps
            lat = a[0] * (1 - t) + b[0] * t
            lon = a[1] * (1 - t) + b[1] * t
            new.append((lat, lon))
    new.append(route[-1])
    return new


def build_html(route_latlon, potholes_latlon, segment_durations, output_path,
               warning_distance_m=80, car_icon_url=None):
    """
    route_latlon: list of (lat, lon)
    potholes_latlon: list of (lat, lon)
    segment_durations: list of seconds per segment (len = len(route)-1)
    """
    # prepare JS arrays
    # route as [[lat,lon],[lat,lon], ...]
    route_js = json.dumps([[float(lat), float(lon)] for (lat, lon) in route_latlon])
    potholes_js = json.dumps([[float(lat), float(lon)] for (lat, lon) in potholes_latlon])
    seg_dur_js = json.dumps([float(x) for x in segment_durations])

    if not car_icon_url:
        car_icon_url = "https://cdn-icons-png.flaticon.com/512/744/744465.png"

    # HTML template
    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>Live Route Simulation</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
  html,body,#map {{ height:100%; margin:0; padding:0; }}
  .warning-box {{
      position: absolute;
      left: 12px;
      top: 12px;
      z-index: 9999;
      background: rgba(220,40,40,0.9);
      color: white;
      padding: 10px 16px;
      border-radius: 8px;
      font-family: Arial, sans-serif;
      font-weight: 600;
      display: none;
      box-shadow: 0 2px 10px rgba(0,0,0,0.35);
  }}
  .hud {{
      position: absolute;
      right: 12px;
      top: 12px;
      z-index: 9998;
      background: rgba(255,255,255,0.9);
      padding: 8px 12px;
      border-radius: 8px;
      font-family: Arial, sans-serif;
      color: #111;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  }}
</style>
</head>
<body>
<div id="map"></div>
<div class="warning-box" id="warnBox">⚠️ Pothole ahead: <span id="warnDist">--</span> m</div>
<div class="hud" id="hudBox">
  <div>Speed: {CAR_SPEED_MPS:.1f} m/s</div>
  <div>Next pothole: <span id="hudPDist">--</span> m</div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>

// --- data injected from Python ---
const route = {route_js};            // array of [lat, lon]
const potholes = {potholes_js};      // array of [lat, lon]
const segDurations = {seg_dur_js};   // seconds per segment
const warningDistance = {warning_distance_m};

// small helper: haversine in meters (lat,lon)
function haversine_m(a, b) {{
  const R = 6371000;
  const toRad = Math.PI/180;
  const lat1 = a[0]*toRad, lon1 = a[1]*toRad;
  const lat2 = b[0]*toRad, lon2 = b[1]*toRad;
  const dlat = lat2-lat1, dlon = lon2-lon1;
  const sinDlat = Math.sin(dlat/2), sinDlon = Math.sin(dlon/2);
  const aa = sinDlat*sinDlat + Math.cos(lat1)*Math.cos(lat2)*sinDlon*sinDlon;
  return 2*R*Math.atan2(Math.sqrt(aa), Math.sqrt(1-aa));
}}

// set up map
const map = L.map('map').setView(route[0], 14);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    maxZoom: 19,
}}).addTo(map);


// draw route
const poly = L.polyline(route, {{color: 'blue', weight: 4, opacity:0.85}}).addTo(map);
map.fitBounds(poly.getBounds().pad(0.15));

// draw potholes as simple red dots (no popup)
const potholeMarkers = [];
for (let i=0;i<potholes.length;i++) {{
  const p = potholes[i];
  const m = L.circleMarker(p, {{radius:4, color:'red', fillColor:'red', fillOpacity:1}});
  m.addTo(map);
  potholeMarkers.push(m);
}}

// car icon
const carIcon = L.icon({{
  iconUrl: '{car_icon_url}',
  iconSize: [36,36],
  iconAnchor: [18,18]
}});

// place car
let carMarker = L.marker(route[0], {{icon: carIcon}}).addTo(map);

// animation state
let segmentIndex = 0;           // current segment start index (route[i] -> route[i+1])
let t0 = null;                  // time when current segment started (ms)
let paused = false;

// compute total route length for info
let totalDist = 0;
for (let i=1;i<route.length;i++) {{
  totalDist += haversine_m(route[i-1], route[i]);
}}

// animation loop: we use requestAnimationFrame to interpolate along segments using segDurations
function step(ts) {{
  if (paused) {{ requestAnimationFrame(step); return; }}
  if (t0 === null) t0 = ts;

  // if we finished all segments, stop at last point
  if (segmentIndex >= segDurations.length) {{
    carMarker.setLatLng(route[route.length-1]);
    updateWarnings(route.length-1);
    return;
  }}

  const segDur = segDurations[segmentIndex] * 1000.0; // ms
  const segStartTime = t0;
  const elapsed = ts - segStartTime;
  let frac = elapsed / segDur;
  if (frac >= 1.0) {{
    // move to next segment
    segmentIndex++;
    t0 = ts;
    if (segmentIndex >= segDurations.length) {{
      carMarker.setLatLng(route[route.length-1]);
      updateWarnings(route.length-1);
      return;
    }} else {{
      // recursive step to handle long frames
      step(ts);
      return;
    }}
  }} else {{
    // interpolate between route[segmentIndex] -> route[segmentIndex+1]
    const a = route[segmentIndex];
    const b = route[segmentIndex+1];
    const lat = a[0] + (b[0]-a[0])*frac;
    const lon = a[1] + (b[1]-a[1])*frac;
    carMarker.setLatLng([lat, lon]);
    updateWarningsPosition([lat, lon]);
    requestAnimationFrame(step);
  }}
}}

// warning UI update based on current car position (lat,lon)
function updateWarningsPosition(carPos) {{
  // find nearest pothole (straight-line)
  let minD = Infinity;
  let minIdx = -1;
  for (let i=0;i<potholes.length;i++) {{
    const d = haversine_m(carPos, potholes[i]);
    if (d < minD) {{ minD = d; minIdx = i; }}
  }}
  const hudP = document.getElementById('hudPDist');
  hudP.textContent = Math.round(minD);

  const warnBox = document.getElementById('warnBox');
  const warnDistSpan = document.getElementById('warnDist');
  if (minD <= warningDistance) {{
    warnDistSpan.textContent = Math.round(minD);
    warnBox.style.display = 'block';
    // highlight the pothole marker (make it bigger) to draw attention
    potholeMarkers.forEach((m, idx) => {{
      if (idx === minIdx) {{
        m.setStyle({{radius:7}});
      }} else {{
        m.setStyle({{radius:4}});
      }}
    }});
  }} else {{
    warnBox.style.display = 'none';
    // reset sizes
    potholeMarkers.forEach((m) => m.setStyle({{radius:4}}));
  }}
}}

// also update warnings at final points
function updateWarnings(lastIndex) {{
  const pos = route[lastIndex];
  updateWarningsPosition(pos);
}}

// start animation
requestAnimationFrame(step);

</script>
</body>
</html>
"""
    Path(output_path).write_text(html, encoding="utf-8")
    print(f"✅ Wrote animation to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate live_route.html from KML route.")
    parser.add_argument("--kml", type=str, default=DEFAULT_KML, help="Path to KML file")
    parser.add_argument("--out", type=str, default=OUTPUT_HTML, help="Output HTML file")
    parser.add_argument("--potholes", type=int, default=DEFAULT_NUM_POTHOLES, help="Number of potholes")
    parser.add_argument("--warning", type=float, default=WARNING_DISTANCE_M, help="Warning distance (m)")
    args = parser.parse_args()

    kml_path = Path(args.kml)
    if not kml_path.exists():
        print("ERROR: KML file not found:", kml_path)
        return

    text = kml_path.read_text(encoding="utf-8")
    coords = extract_coords_from_kml_text(text)
    if not coords:
        print("ERROR: No coordinates found in KML. Are you sure the file contains a route?")
        return

    # coords is list of (lat, lon) (we normalized earlier)
    # Resample to ensure smooth animation: keep segments reasonably small (~<=8 m)
    route = resample_route_to_reasonable_points(coords, max_segment_m=6.0)

    # compute per-segment durations using CAR_SPEED_MPS (seconds)
    seg_durations = []
    for i in range(len(route)-1):
        d = haversine_m(route[i], route[i+1])
        duration = d / CAR_SPEED_MPS
        seg_durations.append(max(0.01, duration))  # avoid zero

    # choose potholes randomly (indices)
    n_potholes = max(1, min(args.potholes, len(route)//4))
    pothole_indices = random.sample(range(5, max(6,len(route)-6)), n_potholes)
    potholes = [route[i] for i in pothole_indices]

    # Build HTML
    build_html(route, potholes, seg_durations, args.out, warning_distance_m=args.warning)

if __name__ == "__main__":
    main()

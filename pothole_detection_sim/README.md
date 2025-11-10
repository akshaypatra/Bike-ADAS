## 📘 Pothole Detection Simulation


<h1 align="center">🚗 <strong>Overview<strong> </h1>

**This module simulates a bike/car ride along a real route (from a .kml file) while dynamically warning the rider about upcoming potholes.
It’s designed as a component for the Bike-ADAS project to demonstrate route awareness and hazard prediction.**

---

## 🗺️ Features

✅ Parse a real route from .kml (Google Maps export)

✅ Place random potholes along the actual road path

✅ Animate a moving car at a configurable speed (default 6 m/s)

✅ Show live pothole warnings with distance updates

✅ Interactive map output (interactive_route.html) using Leaflet.js

✅ Works offline — no external APIs needed

---

## 🧩 Prerequisites

-Make sure you have the following libraries installed:

```bash
pip install fastkml simplekml geopy folium
```

-(Optional) for extended parsing:

```bash
pip install lxml
```
---

## ⚙️ Usage

-Place your route .kml file in the module folder (e.g. route.kml).

-Run the main simulation:
```bash
python main.py --kml "route.kml" --speed 6
```

-After completion, open the generated file:
```
interactive_route.html
```
in any browser.

---

## ⚡ Command-Line Options
Flag	Description	Default

--kml	Path to your KML file	Directions.kml

--speed	Vehicle speed in m/s	6

--potholes	Number of random potholes	12

--warning	Warning distance in meters	80

--out	Output HTML file name	interactive_route.html

---

##Example:
```
python main.py --kml my_route.kml --potholes 15 --warning 100
```
---

## 🧠 Internals

**The KML path is parsed using fastkml and converted to coordinate points.**

**Potholes are placed randomly along the route’s geodesic path using geopy.distance.**

**The vehicle is animated via JavaScript on a Leaflet map.**

**A console warning system triggers alerts when approaching a pothole within the specified distance.**

---

## 📂 Project Structure
```
pothole_detection_sim/
│
├── main.py
├── sample_route.kml
├── interactive_route.html
└── README.md
```
**NOTE: You don't need to create an interactive_route.html file explicitly , after running the main.py it will be added automatically in your project folder.

---

## 🧑‍💻 Contributors

@Mo8Faiz

@akshaypatra

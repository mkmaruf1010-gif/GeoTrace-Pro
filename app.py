import json
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Page Config
st.set_page_config(
    page_title="GeoTrace Pro - Field Survey Tracker",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("GeoTrace Pro: Real-Time Mobile GPS Road Tracker")
st.markdown(
    "A professional web-based GIS tool to record live field tracks, map roads, and export spatial vector data directly from mobile browsers."
)

# Sidebar Options
st.sidebar.header("Survey Configuration")
road_name = st.sidebar.text_input("Road / Project Name", "Road_Survey_01")
surveyor = st.sidebar.text_input("Surveyor Name", "Field Officer")
min_accuracy = st.sidebar.slider(
    "Max Allowed GPS Jitter / Accuracy (meters)", 5, 50, 25
)

st.sidebar.markdown("---")
st.sidebar.subheader("Field Instructions:")
st.sidebar.markdown(
    """
1. Allow Location Permission when prompted by your mobile browser.
2. Tap 'Locate Me' to verify your current position on the map.
3. Tap 'Start Tracking' right before walking or driving along the road.
4. The app will automatically render a blue vector polyline as you move.
5. Tap 'Stop Tracking' and click 'Export GeoJSON' to save your spatial vector file.
"""
)

# Custom HTML/JS Field Tracking Component (Using standard string formatting instead of complex f-string blocks to avoid syntax errors)
html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        #map {{ height: 480px; width: 100%; border-radius: 12px; }}
    </style>
</head>
<body class="bg-slate-900 text-white p-2">
    <div class="flex flex-wrap gap-2 mb-3">
        <button onclick="locateMe()" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded shadow flex items-center gap-1">
            Locate Me
        </button>
        <button id="startBtn" onclick="startTracking()" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 px-4 rounded shadow">
            Start Tracking
        </button>
        <button id="stopBtn" onclick="stopTracking()" class="bg-rose-600 hover:bg-rose-700 text-white font-bold py-2 px-4 rounded shadow hidden">
            Stop Tracking
        </button>
        <button onclick="clearTrack()" class="bg-amber-600 hover:bg-amber-700 text-white font-bold py-2 px-4 rounded shadow">
            Clear Map
        </button>
        <button onclick="exportGeoJSON()" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded shadow">
            Export GeoJSON
        </button>
    </div>

    <!-- Live Status Bar -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3 text-xs bg-slate-800 p-3 rounded-lg border border-slate-700">
        <div>Status: <span id="status" class="font-bold text-amber-400">Idle</span></div>
        <div>Recorded Points: <span id="pointCount" class="font-bold text-blue-400">0</span></div>
        <div>Accuracy: <span id="accuracy" class="font-bold text-emerald-400">-- m</span></div>
        <div>Speed: <span id="speed" class="font-bold text-purple-400">0 km/h</span></div>
    </div>

    <div id="map"></div>

    <script>
        let map, polyline, currentMarker, locateMarker, watchId = null;
        let trackPoints = [];
        const MAX_ACCURACY = {min_accuracy};

        // Initialize Leaflet Map
        function initMap() {{
            map = L.map('map').setView([23.8103, 90.4125], 14);
            
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '&copy; OpenStreetMap Contributors'
            }}).addTo(map);

            polyline = L.polyline([], {{ color: '#3b82f6', weight: 6, opacity: 0.9 }}).addTo(map);
        }}

        initMap();

        function locateMe() {{
            if (!navigator.geolocation) {{
                alert("Geolocation is not supported by your browser!");
                return;
            }}

            document.getElementById('status').innerText = "Fetching Location...";
            
            navigator.geolocation.getCurrentPosition(
                (position) => {{
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    const acc = position.coords.accuracy;
                    const point = [lat, lng];

                    document.getElementById('accuracy').innerText = Math.round(acc) + " m";
                    document.getElementById('status').innerText = "Location Found";
                    document.getElementById('status').className = "font-bold text-indigo-400";

                    map.setView(point, 17);

                    if (!locateMarker) {{
                        locateMarker = L.circleMarker(point, {{
                            radius: 10,
                            fillColor: "#3b82f6",
                            color: "#ffffff",
                            weight: 3,
                            fillOpacity: 0.9
                        }}).addTo(map).bindPopup("<b>You are here!</b>").openPopup();
                    }} else {{
                        locateMarker.setLatLng(point).bindPopup("<b>You are here!</b>").openPopup();
                    }}
                }},
                (err) => {{
                    console.error(err);
                    alert("GPS Error: " + err.message);
                    document.getElementById('status').innerText = "GPS Failed";
                }},
                {{
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }}
            );
        }}

        function startTracking() {{
            if (!navigator.geolocation) {{
                alert("Geolocation is not supported by your browser!");
                return;
            }}

            document.getElementById('startBtn').classList.add('hidden');
            document.getElementById('stopBtn').classList.remove('hidden');
            document.getElementById('status').innerText = "Tracking Live...";
            document.getElementById('status').className = "font-bold text-emerald-400 animate-pulse";

            watchId = navigator.geolocation.watchPosition(
                (position) => {{
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    const acc = position.coords.accuracy;
                    const alt = position.coords.altitude || 0;
                    const speed = position.coords.speed ? (position.coords.speed * 3.6).toFixed(1) : 0;

                    document.getElementById('accuracy').innerText = Math.round(acc) + " m";
                    document.getElementById('speed').innerText = speed + " km/h";

                    if (acc > MAX_ACCURACY) return;

                    const point = [lat, lng];
                    trackPoints.push({{
                        lat: lat,
                        lng: lng,
                        alt: alt,
                        acc: acc,
                        timestamp: new Date().toISOString()
                    }});

                    document.getElementById('pointCount').innerText = trackPoints.length;

                    polyline.addLatLng(point);

                    if (!currentMarker) {{
                        currentMarker = L.circleMarker(point, {{
                            radius: 8,
                            fillColor: "#ef4444",
                            color: "#ffffff",
                            weight: 2,
                            fillOpacity: 1
                        }}).addTo(map);
                    }} else {{
                        currentMarker.setLatLng(point);
                    }}

                    map.setView(point, 18);
                }},
                (err) => {{
                    console.error(err);
                }},
                {{
                    enableHighAccuracy: true,
                    maximumAge: 0,
                    timeout: 10000
                }}
            );
        }}

        function stopTracking() {{
            if (watchId !== null) {{
                navigator.geolocation.clearWatch(watchId);
                watchId = null;
            }}
            document.getElementById('startBtn').classList.remove('hidden');
            document.getElementById('stopBtn').classList.add('hidden');
            document.getElementById('status').innerText = "Paused / Stopped";
            document.getElementById('status').className = "font-bold text-rose-400";
        }}

        function clearTrack() {{
            stopTracking();
            trackPoints = [];
            polyline.setLatLngs([]);
            if (currentMarker) map.removeLayer(currentMarker);
            if (locateMarker) map.removeLayer(locateMarker);
            document.getElementById('pointCount').innerText = "0";
            document.getElementById('accuracy').innerText = "-- m";
            document.getElementById('speed').innerText = "0 km/h";
            document.getElementById('status').innerText = "Idle";
            document.getElementById('status').className = "font-bold text-amber-400";
        }}

        function exportGeoJSON() {{
            if (trackPoints.length === 0) {{
                alert("No GPS data points recorded yet!");
                return;
            }}

            const geojson = {{
                "type": "FeatureCollection",
                "features": [
                    {{
                        "type": "Feature",
                        "geometry": {{
                            "type": "LineString",
                            "coordinates": trackPoints.map(p => [p.lng, p.lat, p.alt])
                        }},
                        "properties": {{
                            "road_name": "{road_name}",
                            "surveyor": "{surveyor}",
                            "recorded_points": trackPoints.length,
                            "start_time": trackPoints[0].timestamp,
                            "end_time": trackPoints[trackPoints.length - 1].timestamp
                        }}
                    }}
                ]
            }};

            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(geojson, null, 2));
            const downloadAnchor = document.createElement('a');
            downloadAnchor.setAttribute("href", dataStr);
            downloadAnchor.setAttribute("download", "{road_name}_track_" + Date.now() + ".geojson");
            document.body.appendChild(downloadAnchor);
            downloadAnchor.click();
            downloadAnchor.remove();
        }}
    </script>
</body>
</html>
"""

# Render HTML Component in Streamlit
components.html(html_code, height=620, scrolling=False)

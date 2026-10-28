import json
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Page Config
st.set_page_config(
    page_title="Field Survey Road Tracker",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🛰️ Streamlit Real-Time Mobile GPS Road Tracker")
st.markdown(
    "মোবাইল জিপিএস ব্যবহার করে ফিল্ডে রাস্তার ভেক্টর লাইন (PolyLine) অটোমেটিক ড্র করার প্রফেশনাল টুল।"
)

# Sidebar Options
st.sidebar.header("📋 Survey Details")
road_name = st.sidebar.text_input("Road / Project Name", "Dhaka_Sector_3_Road")
surveyor = st.sidebar.text_input("Surveyor Name", "Md. Mehedi Khan Maruf")
min_accuracy = st.sidebar.slider(
    "Max Allowed GPS Jitter/Accuracy (meters)", 5, 50, 25
)

st.sidebar.markdown("---")
st.sidebar.subheader("💡 নির্দেশনা:")
st.sidebar.markdown(
    """
1. মোবাইল ব্রাউজারে **Location Permission** এলাউ করুন।
2. ফিল্ড সার্ভে শুরুর মুহূর্তে **Start Tracking** চাপুন।
3. হাঁটা বা গাড়ি ড্রাইভ করার সাথে সাথে মানচিত্রে নীল ভেক্টর লাইন অটো ড্র হবে।
4. শেষে **Stop Tracking** চেপে **Export GeoJSON** বাটনে ক্লিক করুন।
"""
)

# Embed Custom HTML/JS Field Tracking Component into Streamlit
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
        <button id="startBtn" onclick="startTracking()" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 px-4 rounded shadow">
            ▶️ Start Tracking
        </button>
        <button id="stopBtn" onclick="stopTracking()" class="bg-rose-600 hover:bg-rose-700 text-white font-bold py-2 px-4 rounded shadow hidden">
            ⏹️ Stop Tracking
        </button>
        <button onclick="clearTrack()" class="bg-amber-600 hover:bg-amber-700 text-white font-bold py-2 px-4 rounded shadow">
            🗑️ Clear Map
        </button>
        <button onclick="exportGeoJSON()" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded shadow">
            💾 Export GeoJSON Vector
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
        let map, polyline, currentMarker, watchId = null;
        let trackPoints = [];
        const MAX_ACCURACY = {min_accuracy};

        // Initialize Leaflet Map
        function initMap() {{
            map = L.map('map').setView([23.8103, 90.4125], 13);
            
            // OpenStreetMap Layer
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '© OpenStreetMap'
            }}).addTo(map);

            polyline = L.polyline([], {{ color: '#3b82f6', weight: 6, opacity: 0.9 }}).addTo(map);
        }}

        initMap();

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

                    // Accuracy Filter: Ignore weak GPS signals
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

                    // Update Vector Polyline
                    polyline.addLatLng(point);

                    // Update Live Marker
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
                    alert("GPS Error: " + err.message);
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
            document.getElementById('pointCount').innerText = "0";
            document.getElementById('accuracy').innerText = "-- m";
            document.getElementById('speed').innerText = "0 km/h";
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
            downloadAnchor.setAttribute("download", `{road_name}_track_${{Date.now()}}.geojson`);
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

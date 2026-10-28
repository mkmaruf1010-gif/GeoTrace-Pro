import json
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Page Config
st.set_page_config(
    page_title="GeoTrace Pro - Field Survey Tracker",
    page_icon="",
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
1. Allow **Location Permission** when prompted by your mobile browser.
2. Tap **"Locate Me"** to verify your current position on the map.
3. Tap **"Start Tracking"** right before walking or driving along the road.
4. The app will automatically render a blue vector polyline as you move.
5. Tap **"Stop Tracking"** and click **"Export GeoJSON"** to save your spatial vector file.
"""
)

# Embed Custom HTML/JS Field Tracking Component in English
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

        // Initialize Leaflet Map (Default center: Dhaka, shifts to user location on locate)
        function initMap() {{
            map = L.map('map').setView([23.8103, 90.4125], 14);
            
            // OpenStreetMap Tile Layer
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '&copy; OpenStreetMap Contributors'
            }}).addTo(map);

            polyline = L.polyline([], {{ color: '#3b82f6', weight: 6, opacity: 0.9 }}).addTo(map);

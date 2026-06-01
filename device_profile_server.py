"""
Wireless Device Profile Server - Listens for and collects device profiles from remote devices.
"""

from flask import Flask, render_template, request, jsonify
from pathlib import Path
import json
import threading
import socket
from datetime import datetime
from typing import Dict, Any, Optional
import uuid
import webbrowser


class DeviceProfileServer:
    """Flask-based server for receiving device profiles from remote devices."""
    
    def __init__(self, port: int = 5000):
        """
        Initialize the profile server.
        
        Args:
            port: Port to run the server on
        """
        self.port = port
        self.app = Flask(__name__)
        self.received_profiles: Dict[str, Dict[str, Any]] = {}
        self.profiles_dir = Path("reports/remote_profiles")
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.server_session_id = str(uuid.uuid4())[:8]
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Serve the device profile collection page."""
            return self._get_collection_html()
        
        @self.app.route('/dashboard')
        def dashboard():
            """Serve the live location dashboard."""
            return self._get_dashboard_html()
        
        @self.app.route('/api/submit-profile', methods=['POST'])
        def submit_profile():
            """Receive device profile data from remote device."""
            try:
                data = request.get_json()
                
                # Generate profile ID
                profile_id = str(uuid.uuid4())[:8]
                device_id = data.get('device_id', 'unknown')
                
                # Add metadata
                profile = {
                    'profile_id': profile_id,
                    'device_id': device_id,
                    'timestamp': datetime.now().isoformat(),
                    'remote_ip': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', 'Unknown'),
                    **data
                }
                
                # Store profile
                self.received_profiles[profile_id] = profile
                
                # Save to file
                filename = f"remote_profile_{profile_id}_{device_id}.json"
                filepath = self.profiles_dir / filename
                with open(filepath, 'w') as f:
                    json.dump(profile, f, indent=2)
                
                return jsonify({
                    'status': 'success',
                    'profile_id': profile_id,
                    'message': 'Profile received successfully'
                }), 200
                
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 400
        
        @self.app.route('/api/profiles', methods=['GET'])
        def get_profiles():
            """Get all received profiles."""
            return jsonify({
                'profiles': self.received_profiles,
                'count': len(self.received_profiles)
            }), 200
        
        @self.app.route('/api/profile/<profile_id>', methods=['GET'])
        def get_profile(profile_id):
            """Get specific profile."""
            if profile_id in self.received_profiles:
                return jsonify(self.received_profiles[profile_id]), 200
            return jsonify({'error': 'Profile not found'}), 404
    
    def _get_dashboard_html(self) -> str:
        """
        Generate live location dashboard with map.
        
        Returns:
            HTML page as string
        """
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>LEX Live Device Dashboard</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #0f0f1e;
                    color: #e0e0e0;
                }
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px;
                    text-align: center;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
                }
                .header h1 {
                    color: #fff;
                    font-size: 24px;
                }
                .header p {
                    color: #ddd;
                    font-size: 12px;
                    margin-top: 5px;
                }
                .container {
                    display: flex;
                    height: calc(100vh - 70px);
                }
                #map {
                    flex: 1;
                    z-index: 1;
                }
                .sidebar {
                    width: 350px;
                    background: #1a1e27;
                    border-right: 1px solid #333;
                    overflow-y: auto;
                    padding: 20px;
                    box-shadow: -2px 0 10px rgba(0, 0, 0, 0.3);
                }
                .device-list {
                    list-style: none;
                }
                .device-item {
                    background: #2a2e37;
                    padding: 15px;
                    margin-bottom: 15px;
                    border-radius: 8px;
                    border-left: 3px solid #667eea;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                .device-item:hover {
                    background: #323844;
                    border-left-color: #764ba2;
                    transform: translateX(5px);
                }
                .device-name {
                    color: #00ff00;
                    font-weight: bold;
                    font-size: 14px;
                }
                .device-info {
                    color: #888;
                    font-size: 12px;
                    margin-top: 8px;
                }
                .device-coords {
                    color: #00ccff;
                    font-size: 11px;
                    margin-top: 5px;
                    font-family: monospace;
                }
                .stats {
                    background: #2a2e37;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    border-left: 3px solid #00ff00;
                }
                .stat-item {
                    display: flex;
                    justify-content: space-between;
                    margin: 5px 0;
                    font-size: 13px;
                }
                .stat-label {
                    color: #888;
                }
                .stat-value {
                    color: #00ff00;
                    font-weight: bold;
                }
                .refresh-info {
                    color: #888;
                    font-size: 11px;
                    text-align: center;
                    margin-top: 20px;
                }
                .badge {
                    display: inline-block;
                    background: #667eea;
                    color: #fff;
                    padding: 2px 8px;
                    border-radius: 3px;
                    font-size: 10px;
                    margin-left: 5px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🗺️ LEX Live Device Dashboard</h1>
                <p>Real-time Device Location Tracking</p>
            </div>
            
            <div class="container">
                <div id="map"></div>
                
                <div class="sidebar">
                    <div class="stats">
                        <div class="stat-item">
                            <span class="stat-label">Connected Devices:</span>
                            <span class="stat-value" id="deviceCount">0</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Last Update:</span>
                            <span class="stat-value" id="lastUpdate">-</span>
                        </div>
                    </div>
                    
                    <h3 style="color: #00ff00; margin-bottom: 15px; font-size: 14px;">📍 DEVICES</h3>
                    <ul class="device-list" id="deviceList"></ul>
                    
                    <div class="refresh-info">
                        Auto-refreshing every 2 seconds
                    </div>
                </div>
            </div>
            
            <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
            <script>
                // Initialize map
                const map = L.map('map').setView([0, 0], 2);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; OpenStreetMap contributors',
                    maxZoom: 19
                }).addTo(map);
                
                const markers = {};
                let lastProfileCount = 0;
                
                async function updateDashboard() {
                    try {
                        const response = await fetch('/api/profiles');
                        const data = await response.json();
                        const profiles = data.profiles || {};
                        
                        // Update device count
                        document.getElementById('deviceCount').textContent = Object.keys(profiles).length;
                        document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
                        
                        // Update map and sidebar
                        const deviceList = document.getElementById('deviceList');
                        
                        // Remove devices no longer present
                        Object.keys(markers).forEach(profileId => {
                            if (!profiles[profileId]) {
                                map.removeLayer(markers[profileId].marker);
                                delete markers[profileId];
                            }
                        });
                        
                        // Add new devices or update existing ones
                        Object.entries(profiles).forEach(([profileId, profile]) => {
                            const location = profile.location || {};
                            const hasCoords = location.latitude && location.longitude;
                            
                            if (hasCoords) {
                                const lat = location.latitude;
                                const lon = location.longitude;
                                const accuracy = Math.round(location.accuracy || 0);
                                const deviceId = profile.device_id || 'Unknown';
                                
                                // Create or update marker
                                if (!markers[profileId]) {
                                    const marker = L.circleMarker([lat, lon], {
                                        radius: 10,
                                        fillColor: '#667eea',
                                        color: '#764ba2',
                                        weight: 2,
                                        opacity: 1,
                                        fillOpacity: 0.8
                                    }).addTo(map);
                                    
                                    marker.bindPopup(`
                                        <div style="background: #1a1e27; color: #e0e0e0; padding: 10px; border-radius: 5px;">
                                            <strong style="color: #00ff00;">${deviceId}</strong><br>
                                            <small style="color: #888;">Lat: ${lat.toFixed(6)}</small><br>
                                            <small style="color: #888;">Lon: ${lon.toFixed(6)}</small><br>
                                            <small style="color: #888;">Accuracy: ±${accuracy}m</small><br>
                                            <small style="color: #888;">Time: ${new Date(profile.timestamp).toLocaleString()}</small>
                                        </div>
                                    `);
                                    
                                    markers[profileId] = { marker, lat, lon };
                                }
                            }
                        });
                        
                        // Update sidebar list
                        deviceList.innerHTML = '';
                        Object.entries(profiles).forEach(([profileId, profile]) => {
                            const location = profile.location || {};
                            const hasCoords = location.latitude && location.longitude;
                            const deviceId = profile.device_id || 'Unknown';
                            
                            const li = document.createElement('li');
                            li.className = 'device-item';
                            
                            if (hasCoords) {
                                li.style.cursor = 'pointer';
                                li.onclick = () => {
                                    map.setView([location.latitude, location.longitude], 15);
                                    markers[profileId].marker.openPopup();
                                };
                            }
                            
                            li.innerHTML = `
                                <div class="device-name">${deviceId} ${hasCoords ? '<span class="badge">📍</span>' : '<span class="badge" style="background: #666;">No GPS</span>'}</div>
                                <div class="device-info">
                                    Platform: ${profile.platform || 'Unknown'}
                                </div>
                                ${hasCoords ? `
                                    <div class="device-coords">
                                        ${location.latitude.toFixed(6)}, ${location.longitude.toFixed(6)}<br>
                                        ±${Math.round(location.accuracy || 0)}m accuracy
                                    </div>
                                ` : '<div class="device-coords" style="color: #ff6666;">GPS not available</div>'}
                                <div class="device-info">
                                    ${new Date(profile.timestamp).toLocaleString()}
                                </div>
                            `;
                            
                            deviceList.appendChild(li);
                        });
                        
                        // Auto-fit map if we have markers
                        const markerArray = Object.values(markers).map(m => [m.lat, m.lon]);
                        if (markerArray.length > 0) {
                            const bounds = L.latLngBounds(markerArray);
                            map.fitBounds(bounds, { padding: [100, 100] });
                        }
                        
                    } catch (error) {
                        console.error('Error updating dashboard:', error);
                    }
                }
                
                // Update on load and then every 2 seconds
                updateDashboard();
                setInterval(updateDashboard, 2000);
            </script>
        </body>
        </html>
        """
        return html
    
    def _get_collection_html(self) -> str:
        """
        Generate HTML page that collects device profile.
        
        Returns:
            HTML page as string
        """
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>LEX Device Profile Collector</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    padding: 20px;
                }
                .container {
                    background: #1a1e27;
                    border-radius: 15px;
                    padding: 40px;
                    max-width: 600px;
                    width: 100%;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                    color: #e0e0e0;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .header h1 {
                    color: #00ff00;
                    font-size: 28px;
                    margin-bottom: 10px;
                }
                .header p {
                    color: #888;
                    font-size: 14px;
                }
                .status {
                    background: #2a2e37;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    border-left: 3px solid #00ffff;
                }
                .status-item {
                    display: flex;
                    justify-content: space-between;
                    margin: 8px 0;
                    font-size: 14px;
                }
                .status-label {
                    color: #888;
                }
                .status-value {
                    color: #00ff00;
                    font-weight: bold;
                }
                .spinner {
                    border: 4px solid #333;
                    border-top: 4px solid #00ff00;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                .button {
                    background: #00ff00;
                    color: #000;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 5px;
                    font-weight: bold;
                    cursor: pointer;
                    width: 100%;
                    margin-top: 20px;
                    font-size: 16px;
                    transition: all 0.3s;
                }
                .button:hover {
                    background: #00cc00;
                    transform: translateY(-2px);
                }
                .button:disabled {
                    background: #666;
                    cursor: not-allowed;
                    transform: none;
                }
                .success {
                    background: #1a3a1a;
                    border-left-color: #00ff00;
                    padding: 20px;
                    border-radius: 8px;
                    margin-top: 20px;
                    display: none;
                }
                .success.show {
                    display: block;
                }
                .success-text {
                    color: #00ff00;
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                .success-detail {
                    color: #aaa;
                    font-size: 12px;
                    margin: 5px 0;
                }
                .error {
                    background: #3a1a1a;
                    border-left-color: #ff0000;
                    padding: 20px;
                    border-radius: 8px;
                    margin-top: 20px;
                    display: none;
                    color: #ff6666;
                }
                .error.show {
                    display: block;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1> LEX Device Profile</h1>
                    <p>Automatic Device Information Collector</p>
                </div>
                
                <div class="status">
                    <div class="status-item">
                        <span class="status-label">Status:</span>
                        <span class="status-value" id="status">Initializing...</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Collection Progress:</span>
                        <span class="status-value" id="progress">0/8</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Device ID:</span>
                        <span class="status-value" id="deviceId">-</span>
                    </div>
                </div>
                
                <div class="spinner" id="spinner"></div>
                
                <button class="button" id="submitBtn" disabled>Collecting Device Data...</button>
                
                <div class="success" id="successBox">
                    <div class="success-text">✓ Profile Submitted Successfully!</div>
                    <div class="success-detail" id="profileId"></div>
                    <div class="success-detail">Your device information has been securely sent to LEX.</div>
                </div>
                
                <div class="error" id="errorBox">
                    <div id="errorMessage"></div>
                </div>
            </div>
            
            <script>
                let profileData = {};
                let collectionCount = 0;
                const totalSteps = 8;
                
                function updateProgress() {
                    collectionCount++;
                    document.getElementById('progress').textContent = collectionCount + '/' + totalSteps;
                }
                
                function updateStatus(msg) {
                    document.getElementById('status').textContent = msg;
                }
                
                async function collectDeviceProfile() {
                    try {
                        updateStatus('Collecting device information...');
                        
                        // 1. Basic Device Info
                        profileData.device_model = navigator.userAgent;
                        profileData.platform = navigator.platform;
                        profileData.language = navigator.language;
                        profileData.online = navigator.onLine;
                        updateProgress();
                        updateStatus('✓ Basic info collected...');
                        
                        // 2. Device ID (generate unique ID)
                        let deviceId = localStorage.getItem('lexDeviceId');
                        if (!deviceId) {
                            deviceId = 'device-' + Math.random().toString(36).substr(2, 9);
                            localStorage.setItem('lexDeviceId', deviceId);
                        }
                        profileData.device_id = deviceId;
                        document.getElementById('deviceId').textContent = deviceId;
                        updateProgress();
                        updateStatus('✓ Device ID generated...');
                        
                        // 3. Screen Resolution
                        profileData.screen_resolution = {
                            width: window.screen.width,
                            height: window.screen.height,
                            pixel_depth: window.screen.pixelDepth,
                            color_depth: window.screen.colorDepth
                        };
                        updateProgress();
                        updateStatus('✓ Screen resolution detected...');
                        
                        // 4. Memory Info (if available)
                        if (navigator.deviceMemory) {
                            profileData.device_memory_gb = navigator.deviceMemory;
                        }
                        updateProgress();
                        updateStatus('✓ Memory info collected...');
                        
                        // 5. Connection Info
                        if (navigator.connection) {
                            profileData.connection = {
                                effective_type: navigator.connection.effectiveType,
                                downlink: navigator.connection.downlink,
                                rtt: navigator.connection.rtt,
                                save_data: navigator.connection.saveData
                            };
                        }
                        updateProgress();
                        updateStatus('✓ Connection info detected...');
                        
                        // 6. Geolocation
                        await collectGeolocation();
                        updateProgress();
                        updateStatus('✓ Location data collected...');
                        
                        // 7. Browser Capabilities
                        profileData.capabilities = {
                            cookies_enabled: navigator.cookieEnabled,
                            touch_enabled: 'ontouchstart' in window,
                            webgl_enabled: !!document.createElement('canvas').getContext('webgl'),
                            service_worker: 'serviceWorker' in navigator,
                            notification: 'Notification' in window
                        };
                        updateProgress();
                        updateStatus('✓ Browser capabilities detected...');
                        
                        // 8. Hardware Info
                        profileData.hardware = {
                            vibration: 'vibrate' in navigator,
                            battery: 'getBattery' in navigator,
                            camera: navigator.mediaDevices ? true : false,
                            microphone: navigator.mediaDevices ? true : false
                        };
                        updateProgress();
                        updateStatus('✓ Hardware capabilities detected...');
                        
                        // Add timestamp
                        profileData.timestamp = new Date().toISOString();
                        profileData.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                        
                        return true;
                    } catch (error) {
                        console.error('Error collecting profile:', error);
                        return false;
                    }
                }
                
                async function collectGeolocation() {
                    return new Promise((resolve) => {
                        if ('geolocation' in navigator) {
                            navigator.geolocation.getCurrentPosition(
                                function(position) {
                                    profileData.location = {
                                        latitude: position.coords.latitude,
                                        longitude: position.coords.longitude,
                                        accuracy: position.coords.accuracy,
                                        altitude: position.coords.altitude,
                                        altitude_accuracy: position.coords.altitudeAccuracy,
                                        heading: position.coords.heading,
                                        speed: position.coords.speed
                                    };
                                    resolve();
                                },
                                function(error) {
                                    profileData.location = {
                                        error: error.message,
                                        code: error.code
                                    };
                                    resolve();
                                },
                                {
                                    enableHighAccuracy: true,
                                    timeout: 10000,
                                    maximumAge: 0
                                }
                            );
                        } else {
                            profileData.location = { error: 'Geolocation not available' };
                            resolve();
                        }
                    });
                }
                
                async function submitProfile() {
                    try {
                        const response = await fetch('/api/submit-profile', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(profileData)
                        });
                        
                        const result = await response.json();
                        
                        if (response.ok) {
                            updateStatus('✓ Profile submitted successfully!');
                            document.getElementById('submitBtn').disabled = true;
                            document.getElementById('submitBtn').textContent = '✓ Complete';
                            document.getElementById('profileId').textContent = 'Profile ID: ' + result.profile_id;
                            document.getElementById('spinner').style.display = 'none';
                            document.getElementById('successBox').classList.add('show');
                        } else {
                            throw new Error(result.message);
                        }
                    } catch (error) {
                        updateStatus('✗ Submission failed');
                        document.getElementById('errorMessage').textContent = 'Error: ' + error.message;
                        document.getElementById('errorBox').classList.add('show');
                        document.getElementById('submitBtn').disabled = false;
                        document.getElementById('submitBtn').textContent = 'Retry Submission';
                    }
                }
                
                // Start collection on page load
                window.addEventListener('load', async function() {
                    const success = await collectDeviceProfile();
                    if (success) {
                        updateStatus('✓ Collection complete! Ready to submit.');
                        document.getElementById('submitBtn').disabled = false;
                        document.getElementById('submitBtn').textContent = 'Submit Device Profile';
                    } else {
                        updateStatus('✗ Collection failed');
                    }
                });
                
                document.getElementById('submitBtn').addEventListener('click', submitProfile);
            </script>
        </body>
        </html>
        """
        return html
    
    def get_server_url(self, local_ip: str) -> str:
        """
        Get the server URL.
        
        Args:
            local_ip: Local IP address
            
        Returns:
            Full server URL
        """
        return f"http://{local_ip}:{self.port}"
    
    def start_server(self, debug: bool = False):
        """
        Start the Flask server.
        
        Args:
            debug: Enable debug mode
        """
        self.app.run(host='0.0.0.0', port=self.port, debug=debug, use_reloader=False)
    
    def start_server_thread(self) -> threading.Thread:
        """
        Start server in a background thread.
        
        Returns:
            Thread object
        """
        thread = threading.Thread(target=self.start_server, daemon=True)
        thread.start()
        return thread
    
    def get_local_ip(self) -> str:
        """
        Get local IP address.
        
        Returns:
            Local IP address
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    def display_profiles(self) -> None:
        """Display all received profiles."""
        if not self.received_profiles:
            print("No profiles received yet.\n")
            return
        
        print(f"\n{'='*60}")
        print(f"RECEIVED DEVICE PROFILES ({len(self.received_profiles)})")
        print(f"{'='*60}\n")
        
        for profile_id, profile in self.received_profiles.items():
            print(f"Profile ID: {profile_id}")
            print(f"Device ID: {profile.get('device_id', 'Unknown')}")
            print(f"Timestamp: {profile.get('timestamp', 'Unknown')}")
            print(f"Remote IP: {profile.get('remote_ip', 'Unknown')}")
            
            # Device info
            device_model = profile.get('device_model', 'Unknown')
            print(f"Device Model: {device_model[:60]}...")
            
            # Location
            if profile.get('location'):
                loc = profile['location']
                if 'latitude' in loc:
                    print(f"Location: {loc['latitude']}, {loc['longitude']}")
                    print(f"Accuracy: {loc.get('accuracy', 'N/A')} meters")
            
            # Screen
            if profile.get('screen_resolution'):
                screen = profile['screen_resolution']
                print(f"Screen: {screen['width']}x{screen['height']}")
            
            # Connection
            if profile.get('connection'):
                conn = profile['connection']
                print(f"Connection: {conn.get('effective_type', 'Unknown')}")
            
            print()

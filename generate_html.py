import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from the current directory
load_dotenv(dotenv_path=Path('.') / '.env')

# Get API key from environment - fallback to the correct key if not found
api_key = os.getenv('GOOGLE_MAPS_API_KEY')

if not api_key:
    print("Warning: GOOGLE_MAPS_API_KEY not found in environment variables, using provided key")
    api_key = "BRUH" # remove before pushing to github...
else:
    print(f"Loaded API key: {api_key[:10]}...")

# Ensure api_key is always a string
api_key = str(api_key)

def generate_visualization_html():
    """Generate the visualization HTML with the API key"""
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A* Path Visualization - Streetlight Optimized Route</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        
        .container {
            display: flex;
            height: calc(100vh - 120px);
        }
        
        .sidebar {
            width: 350px;
            background: white;
            padding: 20px;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
            overflow-y: auto;
        }
        
        .map-container {
            flex: 1;
            position: relative;
        }
        
        #map {
            height: 100%;
            width: 100%;
        }
        
        .info-panel {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .info-panel h3 {
            margin: 0 0 15px 0;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 8px;
        }
        
        .stat {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        
        .stat:last-child {
            border-bottom: none;
        }
        
        .stat-label {
            font-weight: 600;
            color: #555;
        }
        
        .stat-value {
            color: #667eea;
            font-weight: 500;
        }
        
        .controls {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .control-group {
            margin-bottom: 15px;
        }
        
        .control-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #555;
        }
        
        .control-group input {
            width: 100%;
            padding: 8px;
            border: 2px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        
        .control-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
            margin: 5px 0;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .btn-secondary:hover {
            box-shadow: 0 4px 12px rgba(240, 147, 251, 0.4);
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #666;
        }
        
        .loading.show {
            display: block;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error {
            background: #fee;
            color: #c33;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            border-left: 4px solid #c33;
        }
        
        .success {
            background: #efe;
            color: #363;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            border-left: 4px solid #363;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚶‍♂️ Safwalk Route Visualization</h1>
        <p>A* Pathfinding with Streetlight Visibility Optimization</p>
    </div>
    
    <div class="container">
        <div class="sidebar">
            <div class="info-panel">
                <h3>📊 Route Information</h3>
                <div id="routeInfo">
                    <div class="stat">
                        <span class="stat-label">Status:</span>
                        <span class="stat-value" id="status">Ready to load</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Total Nodes:</span>
                        <span class="stat-value" id="nodeCount">-</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Distance:</span>
                        <span class="stat-value" id="distance">-</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Processing Time:</span>
                        <span class="stat-value" id="processingTime">-</span>
                    </div>
                </div>
            </div>
            
            <div class="controls">
                <h3>🎨 Customization</h3>
                
                <div class="control-group">
                    <label for="pathColor">Path Color:</label>
                    <input type="color" id="pathColor" value="#00FF00">
                </div>
                
                <div class="control-group">
                    <label for="pathWeight">Path Weight:</label>
                    <input type="range" id="pathWeight" min="2" max="10" value="4">
                    <span id="weightValue">4</span>
                </div>
                
                <div class="control-group">
                    <label for="pathOpacity">Path Opacity:</label>
                    <input type="range" id="pathOpacity" min="0.1" max="1" step="0.1" value="1">
                    <span id="opacityValue">1.0</span>
                </div>
                
                <button class="btn" onclick="loadPathFromFile()">🗺️ Load Route</button>
                <button class="btn btn-secondary" onclick="clearPath()">🗑️ Clear Route</button>
                <button class="btn" onclick="fitBounds()">🎯 Fit to Route</button>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Loading route data...</p>
            </div>
            
            <div id="messages"></div>
        </div>
        
        <div class="map-container">
            <div id="map"></div>
        </div>
    </div>

    <script>
        let map;
        let currentPath;
        let markers = [];
        let pathCoordinates = [];

        function initMap() {
            // Initialize map centered on the route area
            map = new google.maps.Map(document.getElementById("map"), {
                center: { lat: 43.504894, lng: -80.518974 }, // Center of the route
                zoom: 13,
                mapTypeId: google.maps.MapTypeId.ROADMAP,
                styles: [
                    {
                        featureType: "poi",
                        elementType: "labels",
                        stylers: [{ visibility: "off" }]
                    }
                ]
            });
        }

        function addMarker(position, title, color = '#FF0000', iconType = 'default') {
            const marker = new google.maps.Marker({
                position: position,
                map: map,
                title: title,
                icon: iconType === 'default' ? null : {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 10,
                    fillColor: color,
                    fillOpacity: 1,
                    strokeColor: '#000000',
                    strokeWeight: 2
                }
            });
            markers.push(marker);
            return marker;
        }

        function clearMarkers() {
            markers.forEach(marker => marker.setMap(null));
            markers = [];
        }

        function clearPath() {
            if (currentPath) {
                currentPath.setMap(null);
                currentPath = null;
            }
            clearMarkers();
            updateStatus('Route cleared');
            updateRouteInfo({}, 'Route cleared');
        }

        function drawPath(coordinates, color = "#00FF00", weight = 4, opacity = 1.0) {
            // Clear existing path
            if (currentPath) {
                currentPath.setMap(null);
            }
            
            // Clear existing markers
            clearMarkers();
            
            if (!coordinates || coordinates.length === 0) {
                showMessage('No coordinates provided', 'error');
                return;
            }

            // Add start and end markers
            addMarker(coordinates[0], "Start Point", "#00FF00", 'custom');
            addMarker(coordinates[coordinates.length - 1], "End Point", "#FF0000", 'custom');

            // Create polyline
            currentPath = new google.maps.Polyline({
                path: coordinates,
                geodesic: true,
                strokeColor: color,
                strokeOpacity: opacity,
                strokeWeight: weight
            });

            currentPath.setMap(map);

            // Fit map to show entire path
            fitBounds();

            // Display path information
            displayPathInfo(coordinates);
            
            showMessage('Route loaded successfully!', 'success');
        }

        function displayPathInfo(coordinates) {
            const distance = calculateDistance(coordinates);
            const info = {
                nodeCount: coordinates.length,
                distance: distance.toFixed(2) + ' km',
                start: `(${coordinates[0].lat.toFixed(6)}, ${coordinates[0].lng.toFixed(6)})`,
                end: `(${coordinates[coordinates.length-1].lat.toFixed(6)}, ${coordinates[coordinates.length-1].lng.toFixed(6)})`
            };
            
            updateRouteInfo(info, 'Route loaded');
        }

        function updateRouteInfo(info, status) {
            document.getElementById('status').textContent = status;
            document.getElementById('nodeCount').textContent = info.nodeCount || '-';
            document.getElementById('distance').textContent = info.distance || '-';
            document.getElementById('processingTime').textContent = info.processingTime || '-';
        }

        function calculateDistance(coordinates) {
            let totalDistance = 0;
            for (let i = 1; i < coordinates.length; i++) {
                const prev = coordinates[i - 1];
                const curr = coordinates[i];
                totalDistance += google.maps.geometry.spherical.computeDistanceBetween(
                    new google.maps.LatLng(prev.lat, prev.lng),
                    new google.maps.LatLng(curr.lat, curr.lng)
                );
            }
            return totalDistance / 1000; // Convert to kilometers
        }

        function loadPathFromFile() {
            showLoading(true);
            updateStatus('Loading route data...');
            
            fetch('path_coordinates.json')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Failed to load path file');
                    }
                    return response.json();
                })
                .then(data => {
                    // Convert GeoJSON coordinates to Google Maps format
                    pathCoordinates = data.geometry.coordinates.map(coord => ({
                        lat: coord[1], // GeoJSON is [lng, lat], Google Maps expects {lat, lng}
                        lng: coord[0]
                    }));
                    
                    const color = document.getElementById('pathColor').value;
                    const weight = parseInt(document.getElementById('pathWeight').value);
                    const opacity = parseFloat(document.getElementById('pathOpacity').value);
                    
                    drawPath(pathCoordinates, color, weight, opacity);
                    showLoading(false);
                })
                .catch(error => {
                    console.error('Error loading path file:', error);
                    showMessage('Error loading path file. Make sure path_coordinates.json exists.', 'error');
                    showLoading(false);
                    updateStatus('Error loading route');
                });
        }

        function fitBounds() {
            if (pathCoordinates.length > 0) {
                const bounds = new google.maps.LatLngBounds();
                pathCoordinates.forEach(coord => bounds.extend(coord));
                map.fitBounds(bounds);
                
                // Add some padding
                const listener = google.maps.event.addListenerOnce(map, 'bounds_changed', function() {
                    map.setZoom(Math.min(map.getZoom(), 15));
                });
            }
        }

        function updateStatus(status) {
            document.getElementById('status').textContent = status;
        }

        function showLoading(show) {
            const loading = document.getElementById('loading');
            if (show) {
                loading.classList.add('show');
            } else {
                loading.classList.remove('show');
            }
        }

        function showMessage(message, type) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = type;
            messageDiv.textContent = message;
            messagesDiv.appendChild(messageDiv);
            
            // Remove message after 5 seconds
            setTimeout(() => {
                messageDiv.remove();
            }, 5000);
        }

        // Event listeners for controls
        document.getElementById('pathWeight').addEventListener('input', function() {
            document.getElementById('weightValue').textContent = this.value;
            if (currentPath) {
                currentPath.setOptions({ strokeWeight: parseInt(this.value) });
            }
        });

        document.getElementById('pathOpacity').addEventListener('input', function() {
            document.getElementById('opacityValue').textContent = parseFloat(this.value).toFixed(1);
            if (currentPath) {
                currentPath.setOptions({ strokeOpacity: parseFloat(this.value) });
            }
        });

        document.getElementById('pathColor').addEventListener('change', function() {
            if (currentPath) {
                currentPath.setOptions({ strokeColor: this.value });
            }
        });

        // Auto-load the route when page loads
        window.addEventListener('load', function() {
            setTimeout(loadPathFromFile, 1000); // Load after map initializes
        });
    </script>

    <!-- Load Google Maps API with geometry library -->
    <script async defer
        src="https://maps.googleapis.com/maps/api/js?key=''' + api_key + '''&libraries=geometry&callback=initMap">
    </script>
</body>
</html>'''
    
    with open('visualize_route.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Generated visualize_route.html with API key")

def generate_simple_html():
    """Generate the simple visualization HTML with the API key"""
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A* Path with Google Maps</title>
    <style>
        #map {
            height: 600px;
            width: 100%;
        }
        .controls {
            margin: 20px 0;
            padding: 15px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }
        .input-group {
            margin: 10px 0;
        }
        label {
            display: inline-block;
            width: 120px;
            font-weight: bold;
        }
        input[type="text"], input[type="number"] {
            padding: 5px;
            margin: 5px;
            border: 1px solid #ccc;
            border-radius: 3px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
        }
        button:hover {
            background-color: #45a049;
        }
        .path-info {
            margin: 10px 0;
            padding: 10px;
            background-color: #e8f5e8;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <h1>A* Pathfinding with Streetlight Visibility Optimization</h1>
    
    <div class="controls">
        <div class="input-group">
            <label for="startLat">Start Latitude:</label>
            <input type="number" id="startLat" value="43.65107" step="0.000001">
            <label for="startLng">Start Longitude:</label>
            <input type="number" id="startLng" value="-79.347016" step="0.000001">
        </div>
        
        <div class="input-group">
            <label for="endLat">End Latitude:</label>
            <input type="number" id="endLat" value="43.6532" step="0.000001">
            <label for="endLng">End Longitude:</label>
            <input type="number" id="endLng" value="-79.3832" step="0.000001">
        </div>
        
        <div class="input-group">
            <label for="pathColor">Path Color:</label>
            <input type="text" id="pathColor" value="#00FF00">
            <label for="pathWeight">Path Weight:</label>
            <input type="number" id="pathWeight" value="4" min="1" max="10">
        </div>
        
        <button onclick="loadPathFromServer()">Generate A* Path</button>
        <button onclick="loadPathFromFile()">Load from JSON File</button>
        <button onclick="clearPath()">Clear Path</button>
    </div>
    
    <div id="pathInfo" class="path-info" style="display: none;">
        <strong>Path Information:</strong>
        <div id="pathDetails"></div>
    </div>
    
    <div id="map"></div>

    <script>
        let map;
        let currentPath;
        let markers = [];

        function initMap() {
            // Initialize map centered on Toronto
            map = new google.maps.Map(document.getElementById("map"), {
                center: { lat: 43.65107, lng: -79.347016 },
                zoom: 12,
                mapTypeId: google.maps.MapTypeId.ROADMAP
            });
        }

        function addMarker(position, title, color = '#FF0000') {
            const marker = new google.maps.Marker({
                position: position,
                map: map,
                title: title,
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 10,
                    fillColor: color,
                    fillOpacity: 1,
                    strokeColor: '#000000',
                    strokeWeight: 2
                }
            });
            markers.push(marker);
            return marker;
        }

        function clearMarkers() {
            markers.forEach(marker => marker.setMap(null));
            markers = [];
        }

        function clearPath() {
            if (currentPath) {
                currentPath.setMap(null);
                currentPath = null;
            }
            clearMarkers();
            document.getElementById("pathInfo").style.display = "none";
        }

        function drawPath(coordinates, color = "#00FF00", weight = 4) {
            // Clear existing path
            if (currentPath) {
                currentPath.setMap(null);
            }
            
            // Clear existing markers
            clearMarkers();
            
            if (!coordinates || coordinates.length === 0) {
                alert("No coordinates provided");
                return;
            }

            // Add start and end markers
            addMarker(coordinates[0], "Start", "#00FF00");
            addMarker(coordinates[coordinates.length - 1], "End", "#FF0000");

            // Create polyline
            currentPath = new google.maps.Polyline({
                path: coordinates,
                geodesic: true,
                strokeColor: color,
                strokeOpacity: 1.0,
                strokeWeight: weight
            });

            currentPath.setMap(map);

            // Fit map to show entire path
            const bounds = new google.maps.LatLngBounds();
            coordinates.forEach(coord => bounds.extend(coord));
            map.fitBounds(bounds);

            // Display path information
            displayPathInfo(coordinates);
        }

        function displayPathInfo(coordinates) {
            const distance = calculateDistance(coordinates);
            const info = `
                <div>Total coordinates: ${coordinates.length}</div>
                <div>Approximate distance: ${distance.toFixed(2)} km</div>
                <div>Start: (${coordinates[0].lat.toFixed(6)}, ${coordinates[0].lng.toFixed(6)})</div>
                <div>End: (${coordinates[coordinates.length-1].lat.toFixed(6)}, ${coordinates[coordinates.length-1].lng.toFixed(6)})</div>
            `;
            
            document.getElementById("pathDetails").innerHTML = info;
            document.getElementById("pathInfo").style.display = "block";
        }

        function calculateDistance(coordinates) {
            let totalDistance = 0;
            for (let i = 1; i < coordinates.length; i++) {
                const prev = coordinates[i - 1];
                const curr = coordinates[i];
                totalDistance += google.maps.geometry.spherical.computeDistanceBetween(
                    new google.maps.LatLng(prev.lat, prev.lng),
                    new google.maps.LatLng(curr.lat, curr.lng)
                );
            }
            return totalDistance / 1000; // Convert to kilometers
        }

        function loadPathFromServer() {
            const startLat = parseFloat(document.getElementById("startLat").value);
            const startLng = parseFloat(document.getElementById("startLng").value);
            const endLat = parseFloat(document.getElementById("endLat").value);
            const endLng = parseFloat(document.getElementById("endLng").value);
            const color = document.getElementById("pathColor").value;
            const weight = parseInt(document.getElementById("pathWeight").value);

            // This would typically make an API call to your Python backend
            // For now, we'll simulate with sample coordinates
            alert("This would call your Python A* algorithm with the provided coordinates.\\n\\n" +
                  "You'll need to set up a web server (Flask/FastAPI) to handle this request.\\n\\n" +
                  "For now, try loading from the JSON file instead.");
        }

        function loadPathFromFile() {
            const color = document.getElementById("pathColor").value;
            const weight = parseInt(document.getElementById("pathWeight").value);

            // Load the JSON file generated by the Python script
            fetch('path_coordinates.json')
                .then(response => response.json())
                .then(data => {
                    // Convert GeoJSON coordinates to Google Maps format
                    const coordinates = data.geometry.coordinates.map(coord => ({
                        lat: coord[1], // GeoJSON is [lng, lat], Google Maps expects {lat, lng}
                        lng: coord[0]
                    }));
                    
                    drawPath(coordinates, color, weight);
                })
                .catch(error => {
                    console.error('Error loading path file:', error);
                    alert('Error loading path file. Make sure path_coordinates.json exists and was generated by running the Python script.');
                });
        }

        // Sample path data for demonstration (replace with actual A* results)
        function loadSamplePath() {
            const sampleCoordinates = [
                { lat: 43.65107, lng: -79.347016 },
                { lat: 43.6515, lng: -79.3480 },
                { lat: 43.6520, lng: -79.3490 },
                { lat: 43.6525, lng: -79.3500 },
                { lat: 43.6532, lng: -79.3832 }
            ];
            
            drawPath(sampleCoordinates);
        }
    </script>

    <!-- Load Google Maps API with geometry library -->
    <script async defer
        src="https://maps.googleapis.com/maps/api/js?key=''' + api_key + '''&libraries=geometry&callback=initMap">
    </script>

    <div style="margin-top: 20px;">
        <h3>Instructions:</h3>
        <ol>
            <li>Run the Python script (<code>python astar.py</code>) to generate the path coordinates</li>
            <li>Use "Load from JSON File" to display the A* path on the map</li>
            <li>Customize the path color and weight using the controls above</li>
        </ol>
        
        <h3>Features:</h3>
        <ul>
            <li>Displays A* path optimized for streetlight visibility</li>
            <li>Shows start (green) and end (red) markers</li>
            <li>Calculates approximate path distance</li>
            <li>Automatically fits map to show entire path</li>
            <li>Customizable path styling</li>
        </ul>
    </div>
</body>
</html>'''
    
    with open('simple_visualization.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Generated simple_visualization.html with API key")

if __name__ == "__main__":
    generate_visualization_html()
    generate_simple_html()
    print(f"Generated HTML files with API key: {api_key[:10]}...") 
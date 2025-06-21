from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import osmnx as ox
import json
import heapq
import time
from astar import a_star, path_to_polyline_coordinates, save_path_to_json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the graph and lighting data once at startup
print("Loading Toronto walking network...")
G = ox.graph_from_place("Toronto, Canada", network_type='walk')

print("Loading streetlight data...")
with open('kwtest1_geometry_only.json') as f:
    light_data = json.load(f)

# Add lighting scores to edges
print("Adding lighting scores to graph edges...")
for u, v, data in G.edges(data=True):
    edge_id = f"{u}_{v}"
    data['lighting_score'] = light_data.get(edge_id, 1.0)  
    data['custom_weight'] = data['length'] / data['lighting_score']

print("Graph loaded successfully!")

def heuristic(a, b):
    return ox.distance.euclidean_dist_vec(a[0], a[1], b[0], b[1])

def get_nearest_node_safe(G, coords):
    """Safely get nearest node with fallback for different OSMnx versions."""
    try:
        # Newer OSMnx versions use nearest_nodes with (lng, lat) order
        return ox.nearest_nodes(G, coords[1], coords[0])
    except AttributeError:
        # Fallback for older OSMnx versions
        return ox.get_nearest_node(G, coords)

@app.route('/')
def index():
    """Serve the main HTML page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>A* Pathfinding API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .form-group { margin: 15px 0; }
            label { display: inline-block; width: 120px; font-weight: bold; }
            input[type="number"] { padding: 5px; margin: 5px; width: 150px; }
            button { background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #45a049; }
            .result { margin-top: 20px; padding: 15px; background-color: #f5f5f5; border-radius: 5px; }
            .coordinates { font-family: monospace; background-color: #f0f0f0; padding: 10px; border-radius: 3px; overflow-x: auto; }
            .loading { display: none; color: #666; font-style: italic; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>A* Pathfinding API</h1>
            <p>This API finds optimal walking paths in Toronto that prioritize well-lit streets.</p>
            
            <form id="pathForm">
                <div class="form-group">
                    <label for="startLat">Start Latitude:</label>
                    <input type="number" id="startLat" name="start_lat" value="43.494751" step="0.000001" required>
                </div>
                
                <div class="form-group">
                    <label for="startLng">Start Longitude:</label>
                    <input type="number" id="startLng" name="start_lng" value="-80.524751" step="0.000001" required>
                </div>
                
                <div class="form-group">
                    <label for="endLat">End Latitude:</label>
                    <input type="number" id="endLat" name="end_lat" value="43.515037" step="0.000001" required>
                </div>
                
                <div class="form-group">
                    <label for="endLng">End Longitude:</label>
                    <input type="number" id="endLng" name="end_lng" value="-80.513197" step="0.000001" required>
                </div>
                
                <button type="submit">Find Path</button>
            </form>
            
            <div id="loading" class="loading">
                <p>Finding optimal path... This may take a few seconds.</p>
            </div>
            
            <div id="result" class="result" style="display: none;">
                <h3>Path Result:</h3>
                <div id="pathInfo"></div>
                <h4>Coordinates (Google Maps format):</h4>
                <div id="coordinates" class="coordinates"></div>
                <h4>GeoJSON:</h4>
                <div id="geojson" class="coordinates"></div>
            </div>
        </div>

        <script>
            document.getElementById('pathForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                // Show loading message
                document.getElementById('loading').style.display = 'block';
                document.getElementById('result').style.display = 'none';
                
                const formData = new FormData(this);
                const data = {
                    start_lat: parseFloat(formData.get('start_lat')),
                    start_lng: parseFloat(formData.get('start_lng')),
                    end_lat: parseFloat(formData.get('end_lat')),
                    end_lng: parseFloat(formData.get('end_lng'))
                };
                
                try {
                    const response = await fetch('/api/path', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    // Hide loading message
                    document.getElementById('loading').style.display = 'none';
                    
                    if (result.success) {
                        document.getElementById('pathInfo').innerHTML = `
                            <p><strong>Path found!</strong></p>
                            <p>Total nodes: ${result.path_info.node_count}</p>
                            <p>Total coordinates: ${result.path_info.coordinate_count}</p>
                            <p>Processing time: ${result.processing_time.toFixed(2)} seconds</p>
                            <p>Start: (${result.coordinates[0].lat.toFixed(6)}, ${result.coordinates[0].lng.toFixed(6)})</p>
                            <p>End: (${result.coordinates[result.coordinates.length-1].lat.toFixed(6)}, ${result.coordinates[result.coordinates.length-1].lng.toFixed(6)})</p>
                        `;
                        
                        document.getElementById('coordinates').textContent = JSON.stringify(result.coordinates, null, 2);
                        document.getElementById('geojson').textContent = JSON.stringify(result.geojson, null, 2);
                        document.getElementById('result').style.display = 'block';
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    console.error('Error:', error);
                    document.getElementById('loading').style.display = 'none';
                    alert('Error making request to API');
                }
            });
        </script>
    </body>
    </html>
    """
    return html_content

@app.route('/api/path', methods=['POST'])
def get_path():
    """API endpoint to find A* path between two points"""
    try:
        data = request.get_json()
        
        # Extract coordinates
        start_lat = data.get('start_lat')
        start_lng = data.get('start_lng')
        end_lat = data.get('end_lat')
        end_lng = data.get('end_lng')
        
        if None in [start_lat, start_lng, end_lat, end_lng]:
            return jsonify({'success': False, 'error': 'Missing coordinates'})
        
        start_time = time.time()
        
        # Get nearest nodes in the graph
        origin_node = get_nearest_node_safe(G, (start_lat, start_lng))
        destination_node = get_nearest_node_safe(G, (end_lat, end_lng))
        
        # Find path using A*
        path = a_star(G, origin_node, destination_node)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        if not path:
            return jsonify({'success': False, 'error': 'No path found between the specified points'})
        
        # Convert path to coordinates
        coordinates = path_to_polyline_coordinates(G, path)
        
        # Create GeoJSON format
        geojson = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[coord['lng'], coord['lat']] for coord in coordinates]  # GeoJSON format: [lng, lat]
            },
            "properties": {
                "description": "A* path optimized for streetlight visibility",
                "node_count": len(path),
                "coordinate_count": len(coordinates)
            }
        }
        
        # Save to file
        save_path_to_json(G, path, "path_coordinates.json")
        
        return jsonify({
            'success': True,
            'coordinates': coordinates,
            'geojson': geojson,
            'path_info': {
                'node_count': len(path),
                'coordinate_count': len(coordinates)
            },
            'processing_time': processing_time
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'A* Pathfinding API is running'})

if __name__ == '__main__':
    print("Starting Flask server...")
    print("API endpoints:")
    print("  GET  / - Main interface")
    print("  POST /api/path - Find A* path")
    print("  GET  /api/health - Health check")
    print("\nOpen http://localhost:5000 in your browser")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 
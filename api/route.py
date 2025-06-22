from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add parent directory and current directory to path to import your existing modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(__file__))

# Import your existing functions
try:
    from astar_optimized import find_path_optimized, path_to_polyline_coordinates
except ImportError:
    print("Warning: Could not import astar module")
    def find_path_optimized(*args, **kwargs):
        return None, None
    def path_to_polyline_coordinates(*args, **kwargs):
        return []

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check endpoint"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "status": "healthy",
            "service": "SafeBike API",
            "message": "Backend is running!"
        }
        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        """Handle route finding - same logic as your Flask app"""
        try:
            # CORS headers
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

            # Parse request body (same as your Flask app)
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            # Extract coordinates (same format as your Flask app expects)
            start_lat = float(data.get('start_lat'))
            start_lng = float(data.get('start_lng'))
            end_lat = float(data.get('end_lat'))
            end_lng = float(data.get('end_lng'))
            
            start_coords = (start_lat, start_lng)
            end_coords = (end_lat, end_lng)

            # Use your existing pathfinding function
            G, path = find_path_optimized(start_coords, end_coords, radius_km=5)

            if path:
                # Use your existing coordinate conversion
                coordinates = path_to_polyline_coordinates(G, path)
                
                # Format exactly like your Flask app
                formatted_coords = [
                    {"lat": coord[0], "lng": coord[1]} 
                    for coord in coordinates
                ]

                # Create GeoJSON (same as your Flask app)
                geojson = {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[coord[1], coord[0]] for coord in coordinates]
                    },
                    "properties": {
                        "description": "A* path optimized for streetlight visibility"
                    }
                }

                # Same response format as your Flask app
                response = {
                    "success": True,
                    "coordinates": formatted_coords,
                    "geojson": geojson,
                    "path_info": {
                        "node_count": len(path),
                        "coordinate_count": len(coordinates)
                    }
                }
            else:
                response = {
                    "success": False,
                    "error": "No path found between the specified points",
                    "coordinates": [],
                    "geojson": None
                }

        except Exception as e:
            response = {
                "success": False,
                "error": f"Server error: {str(e)}",
                "coordinates": [],
                "geojson": None
            }

        self.wfile.write(json.dumps(response).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
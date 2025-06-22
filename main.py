from flask import Flask, request, jsonify
from flask_cors import CORS
import os

# Import your existing functions
from astar_optimized import find_path_optimized, path_to_polyline_coordinates

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "SafeBike API"})

@app.route('/api/route', methods=['POST'])
def find_route():
    try:
        data = request.get_json()
        start_coords = (data['start_lat'], data['start_lng'])
        end_coords = (data['end_lat'], data['end_lng'])
        
        G, path = find_path_optimized(start_coords, end_coords, radius_km=5)
        
        if path:
            coordinates = path_to_polyline_coordinates(G, path)
            formatted_coords = [{"lat": coord[0], "lng": coord[1]} for coord in coordinates]
            
            return jsonify({
                "success": True,
                "coordinates": formatted_coords,
                "path_info": {"coordinate_count": len(coordinates)}
            })
        else:
            return jsonify({"success": False, "error": "No route found"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
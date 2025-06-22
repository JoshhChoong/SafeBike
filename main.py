from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import gc

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "SafeBike API"})

@app.route('/api/route', methods=['POST'])
def find_route():
    try:
        import osmnx as ox
        import networkx as nx
        
        data = request.get_json()
        start_coords = (data['start_lat'], data['start_lng'])
        end_coords = (data['end_lat'], data['end_lng'])
        
        # Use smaller radius to reduce memory usage
        center_lat = (start_coords[0] + end_coords[0]) / 2
        center_lng = (start_coords[1] + end_coords[1]) / 2
        
        # Smaller graph = less memory
        G = ox.graph_from_point((center_lat, center_lng), dist=2000, network_type='bike', simplify=True)
        
        # Find nearest nodes
        orig_node = ox.nearest_nodes(G, start_coords[1], start_coords[0])
        dest_node = ox.nearest_nodes(G, end_coords[1], end_coords[0])
        
        # Simple shortest path
        path = nx.shortest_path(G, orig_node, dest_node, weight='length')
        
        # Convert to coordinates
        coordinates = []
        for node in path:
            node_data = G.nodes[node]
            coordinates.append({"lat": node_data['y'], "lng": node_data['x']})
        
        # Clean up memory
        del G
        gc.collect()
        
        return jsonify({
            "success": True,
            "coordinates": coordinates,
            "path_info": {"coordinate_count": len(coordinates)}
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
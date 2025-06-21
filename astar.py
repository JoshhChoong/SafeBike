import osmnx as ox
import json
import heapq
import time

def get_nearest_node_safe(G, coords):
    try:
        return ox.nearest_nodes(G, coords[1], coords[0])
    except AttributeError:
        return ox.get_nearest_node(G, coords)

print("Loading Toronto walking network...")
G = ox.graph_from_place("Toronto, Canada", network_type='walk')

print("Loading streetlight data...")
with open('kwtest1_geometry_only.json') as f:
    light_data = json.load(f)

print("Adding lighting scores to graph edges...")
for u, v, data in G.edges(data=True):
    edge_id = f"{u}_{v}"
    data['lighting_score'] = light_data.get(edge_id, 0.9)  
    data['custom_weight'] = data['length'] / data['lighting_score']

def heuristic(a, b):
    return ox.distance.euclidean_dist_vec(a[0], a[1], b[0], b[1])

def reconstruct_path(came_from, start, goal):
    """Reconstruct the path from start to goal using the came_from dictionary."""
    current = goal
    path = []
    
    while current is not None:
        path.append(current)
        current = came_from.get(current)
    
    path.reverse()
    
    # Check if path actually reaches the goal
    if path[0] == start and path[-1] == goal:
        return path
    else:
        return None

def a_star(G, start, goal, max_iterations=10000):
    """Optimized A* algorithm with iteration limit and early termination."""
    frontier = [(0, start)]
    came_from = {start: None}
    cost_so_far = {start: 0}
    iterations = 0

    while frontier and iterations < max_iterations:
        _, current = heapq.heappop(frontier)
        iterations += 1
        
        if current == goal:
            print(f"A* completed in {iterations} iterations")
            return reconstruct_path(came_from, start, goal)

        for neighbor in G.neighbors(current):
            edge_data = G.get_edge_data(current, neighbor, 0)
            if not edge_data:
                continue
                
            new_cost = cost_so_far[current] + edge_data.get('custom_weight', edge_data.get('length', 1))
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + heuristic(G.nodes[neighbor]['y'], G.nodes[neighbor]['x'])
                heapq.heappush(frontier, (priority, neighbor))
                came_from[neighbor] = current

    print(f"A* stopped after {iterations} iterations without finding path")
    return None

def path_to_polyline_coordinates(G, path):
    """Convert a path of node IDs to Google Maps polyline coordinates."""
    if not path:
        return []
    
    coordinates = []
    for node_id in path:
        node_data = G.nodes[node_id]
        # Google Maps expects [lat, lng] format
        coordinates.append([node_data['y'], node_data['x']])
    
    return coordinates

def path_to_encoded_polyline(G, path):
    """Convert a path to Google's encoded polyline format."""
    coordinates = path_to_polyline_coordinates(G, path)
    
    # Simple polyline encoding (you might want to use a library like polyline for production)
    encoded = ""
    lat = 0
    lng = 0
    
    for coord in coordinates:
        # Encode latitude
        lat_diff = int((coord[0] - lat) * 1e5)
        lat += lat_diff / 1e5
        
        # Encode longitude  
        lng_diff = int((coord[1] - lng) * 1e5)
        lng += lng_diff / 1e5
        
        # Simple encoding (for production, use proper polyline encoding)
        encoded += f"{lat_diff},{lng_diff};"
    
    return encoded.rstrip(';')

def generate_google_maps_polyline(G, path, color="#00FF00", weight=4, opacity=1.0):
    """Generate JavaScript code for Google Maps polyline."""
    coordinates = path_to_polyline_coordinates(G, path)
    
    if not coordinates:
        return "// No path found"
    
    # Convert coordinates to JavaScript array format
    coords_js = ",\n    ".join([f"{{lat: {coord[0]}, lng: {coord[1]}}}" for coord in coordinates])
    
    js_code = f"""const routePath = new google.maps.Polyline({{
  path: [
    {coords_js}
  ],
  geodesic: true,
  strokeColor: "{color}",
  strokeOpacity: {opacity},
  strokeWeight: {weight}
}});

routePath.setMap(map);"""
    
    return js_code

def save_path_to_json(G, path, filename="path_coordinates.json"):
    """Save path coordinates to a JSON file for external use."""
    coordinates = path_to_polyline_coordinates(G, path)
    
    path_data = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[coord[1], coord[0]] for coord in coordinates]  # GeoJSON format: [lng, lat]
        },
        "properties": {
            "description": "A* path optimized for streetlight visibility",
            "node_count": len(path),
            "coordinate_count": len(coordinates)
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(path_data, f, indent=2)
    
    print(f"Path coordinates saved to {filename}")

def load_graph_for_area(center_lat, center_lng, radius_km=5):
    """Load a smaller graph around the specified area for better performance."""
    print(f"Loading graph for area around ({center_lat}, {center_lng}) with radius {radius_km}km...")
    # Use graph_from_point for best compatibility
    G = ox.graph_from_point((center_lat, center_lng), dist=radius_km*1000, network_type='walk', simplify=True)
    print(f"Graph loaded with {len(G.nodes)} nodes and {len(G.edges)} edges")
    return G

# Example usage
if __name__ == "__main__":
    # Define start and end points (latitude, longitude)
    start_coords = (43.494751, -80.524751) 
    end_coords = (43.515037, -80.513197)
    
    print(f"Finding path from {start_coords} to {end_coords}")
    
    # Get nearest nodes in the graph using the correct function
    origin_node = get_nearest_node_safe(G, start_coords)
    destination_node = get_nearest_node_safe(G, end_coords)
    
    print(f"Origin node: {origin_node}")
    print(f"Destination node: {destination_node}")
    
    # Find the path using A*
    start_time = time.time()
    path = a_star(G, origin_node, destination_node)
    end_time = time.time()
    
    print(f"Pathfinding took {end_time - start_time:.2f} seconds")
    
    if path:
        print(f"Path found with {len(path)} nodes")
        
        # Generate different outputs
        coordinates = path_to_polyline_coordinates(G, path)
        print(f"Generated {len(coordinates)} coordinate pairs")
        
        # Save to JSON file
        save_path_to_json(G, path)
        
        # Generate Google Maps JavaScript code
        js_code = generate_google_maps_polyline(G, path)
        print("\nGoogle Maps JavaScript code:")
        print(js_code)
        
        # Save JavaScript code to file
        with open("google_maps_polyline.js", "w") as f:
            f.write(js_code)
        print("\nJavaScript code saved to google_maps_polyline.js")
        
    else:
        print("No path found between the specified points")
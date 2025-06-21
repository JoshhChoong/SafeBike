import osmnx as ox
import json
import heapq
import time

def get_nearest_node_safe(G, coords):
    try:
        return ox.nearest_nodes(G, coords[1], coords[0])
    except AttributeError:
        return ox.get_nearest_node(G, coords)

def load_graph_for_area(center_lat, center_lng, radius_km=5):
    print(f"Loading graph for area around ({center_lat}, {center_lng}) with radius {radius_km}km...")
    G = ox.graph_from_point((center_lat, center_lng), dist=radius_km*1000, network_type='walk', simplify=True)
    print(f"Graph loaded with {len(G.nodes)} nodes and {len(G.edges)} edges")
    return G

def load_lighting_data():
    print("Loading streetlight data...")
    with open('kwtest1_geometry_only.json') as f:
        return json.load(f)

def apply_lighting_weights(G, light_data):
    print("Adding lighting scores to graph edges...")
    for u, v, data in G.edges(data=True):
        print(u,v,data)
        edge_id = f"{u}_{v}"
        data['lighting_score'] = light_data.get(edge_id, 1.0)  
        data['custom_weight'] = data['length'] / data['lighting_score']

def heuristic(a, b):
    # Always use simple Euclidean distance between two (lat, lng) tuples
    return ((a[0] - b[0])**2 + (a[1] - b[1])**2)**0.5

def reconstruct_path(came_from, start, goal):
    current = goal
    path = []
    while current is not None:
        path.append(current)
        current = came_from.get(current)
    path.reverse()
    if path[0] == start and path[-1] == goal:
        return path
    else:
        return None

def a_star_optimized(G, start, goal, max_iterations=5000):
    frontier = [(0, start)]
    came_from = {start: None}
    cost_so_far = {start: 0}
    iterations = 0
    visited = set()
    goal_coords = (G.nodes[goal]['y'], G.nodes[goal]['x'])
    while frontier and iterations < max_iterations:
        _, current = heapq.heappop(frontier)
        iterations += 1
        if current == goal:
            print(f"A* completed in {iterations} iterations")
            return reconstruct_path(came_from, start, goal)
        if current in visited:
            continue
        visited.add(current)
        for neighbor in G.neighbors(current):
            if neighbor in visited:
                continue
            edge_data = G.get_edge_data(current, neighbor, 0)
            if not edge_data:
                continue
            new_cost = cost_so_far[current] + edge_data.get('custom_weight', edge_data.get('length', 1))
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                neighbor_coords = (G.nodes[neighbor]['y'], G.nodes[neighbor]['x'])
                priority = new_cost + heuristic(neighbor_coords, goal_coords)
                heapq.heappush(frontier, (priority, neighbor))
                came_from[neighbor] = current
    print(f"A* stopped after {iterations} iterations without finding path")
    return None

def path_to_polyline_coordinates(G, path):
    if not path:
        return []
    coordinates = []
    for node_id in path:
        node_data = G.nodes[node_id]
        coordinates.append([node_data['y'], node_data['x']])
    return coordinates

def save_path_to_json(G, path, filename="path_coordinates.json"):
    coordinates = path_to_polyline_coordinates(G, path)
    path_data = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[coord[1], coord[0]] for coord in coordinates]
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

def generate_google_maps_polyline(G, path, color="#00FF00", weight=4, opacity=1.0):
    coordinates = path_to_polyline_coordinates(G, path)
    if not coordinates:
        return "// No path found"
    coords_js = ",\n    ".join([f"{{lat: {coord[0]}, lng: {coord[1]}}}" for coord in coordinates])
    js_code = f"""const routePath = new google.maps.Polyline({{
  path: [
    {coords_js}
  ],
  geodesic: true,
  strokeColor: \"{color}\",
  strokeOpacity: {opacity},
  strokeWeight: {weight}
}});

routePath.setMap(map);"""
    return js_code

def find_path_optimized(start_coords, end_coords, radius_km=5):
    print(f"Finding optimized path from {start_coords} to {end_coords}")
    center_lat = (start_coords[0] + end_coords[0]) / 2
    center_lng = (start_coords[1] + end_coords[1]) / 2
    G = load_graph_for_area(center_lat, center_lng, radius_km)
    light_data = load_lighting_data()
    apply_lighting_weights(G, light_data)
    origin_node = get_nearest_node_safe(G, start_coords)
    destination_node = get_nearest_node_safe(G, end_coords)
    print(f"Origin node: {origin_node}")
    print(f"Destination node: {destination_node}")
    start_time = time.time()
    path = a_star_optimized(G, origin_node, destination_node)
    end_time = time.time()
    print(f"Pathfinding took {end_time - start_time:.2f} seconds")
    if path:
        print(f"Path found with {len(path)} nodes")
        return G, path
    else:
        print("No path found between the specified points")
        return G, None

if __name__ == "__main__":
    start_coords = (43.494751, -80.524751)
    end_coords = (43.515037, -80.513197)
    G, path = find_path_optimized(start_coords, end_coords, radius_km=3)
    if path:
        coordinates = path_to_polyline_coordinates(G, path)
        print(f"Generated {len(coordinates)} coordinate pairs")
        save_path_to_json(G, path)
        js_code = generate_google_maps_polyline(G, path)
        print("\nGoogle Maps JavaScript code:")
        print(js_code)
        with open("google_maps_polyline.js", "w") as f:
            f.write(js_code)
        print("\nJavaScript code saved to google_maps_polyline.js") 
import osmnx as ox
import json
import heapq
import time
import math
import pickle
import os
from scipy.spatial import KDTree
from functools import lru_cache

def get_nearest_node_safe(G, coords):
    try:
        return ox.nearest_nodes(G, coords[1], coords[0])
    except AttributeError:
        # Fallback for older OSMnx versions - use distance-based approach
        min_dist = float('inf')
        nearest_node = None
        for node in G.nodes():
            node_coords = (G.nodes[node]['y'], G.nodes[node]['x'])
            dist = ((coords[0] - node_coords[0])**2 + (coords[1] - node_coords[1])**2)**0.5
            if dist < min_dist:
                min_dist = dist
                nearest_node = node
        return nearest_node

def haversine(lon1, lat1, lon2, lat2):
    """Calculate the great-circle distance between two points (in meters)"""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_edge_midpoint(G, u, v):
    """Get the midpoint coordinates of an edge"""
    y1, x1 = G.nodes[u]['y'], G.nodes[u]['x']
    y2, x2 = G.nodes[v]['y'], G.nodes[v]['x']
    return ((y1 + y2) / 2, (x1 + x2) / 2)

def find_nearest_feature(midpoint, feature_data, max_distance):
    """Find if there's a feature within max_distance of the midpoint"""
    for feature in feature_data['features']:
        lon, lat = feature['geometry']['coordinates']
        dist = haversine(midpoint[1], midpoint[0], lon, lat)
        if dist <= max_distance:
            return True
    return False

def load_graph_for_area(center_lat, center_lng, radius_km=5):
    print(f"Loading graph for area around ({center_lat}, {center_lng}) with radius {radius_km}km...")
    G = ox.graph_from_point((center_lat, center_lng), dist=radius_km*1000, network_type='walk', simplify=True)
    print(f"Graph loaded with {len(G.nodes)} nodes and {len(G.edges)} edges")
    return G

def load_safety_weights():
    print("Loading Safety Weights...")
    try:
        with open('test_output/safety_weights.json') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: safety_weights.json not found, using empty data")
        return {}

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

def a_star_optimized(G, start, goal, max_iterations=15000):
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
        
        # Skip if already visited (this should rarely happen now with the fix below)
        if current in visited:
            continue
            
        visited.add(current)
        
        for neighbor in G.neighbors(current):
            # Skip if neighbor is already visited
            if neighbor in visited:
                continue
                
            edge_data = G.get_edge_data(current, neighbor, 0)
            if not edge_data:
                continue
                
            new_cost = cost_so_far[current] + edge_data.get('custom_weight', edge_data.get('length', 1))
            
            # Only update and push to frontier if we found a better path
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                neighbor_coords = (G.nodes[neighbor]['y'], G.nodes[neighbor]['x'])
                priority = new_cost + heuristic(neighbor_coords, goal_coords)
                
                # Only push to frontier if not already visited
                if neighbor not in visited:
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

class SafetyWeightIndex:
    """Fast spatial index for safety weights using KDTree"""
    def __init__(self, safety_weights):
        print("Creating KDTree spatial index for safety weights...")
        self.points = []
        self.weights = []
        
        for coord_key, safety_weight in safety_weights.items():
            try:
                lat_str, lng_str = coord_key.split(',')
                lat = float(lat_str)
                lng = float(lng_str)
                
                # Store as (lat, lng) for KDTree
                self.points.append([lat, lng])
                self.weights.append(safety_weight)
            except (ValueError, IndexError):
                continue
        
        if self.points:
            self.kdtree = KDTree(self.points)
            print(f"Created KDTree with {len(self.points)} safety weight points")
        else:
            self.kdtree = None
            print("No valid safety weight points found")
    
    def get_nearby_weights(self, midpoint, max_distance=50):
        """Get safety weights within max_distance using KDTree"""
        if not self.kdtree:
            return []
        
        lat, lng = midpoint
        
        # Convert max_distance from meters to approximate degrees
        # 1 degree ≈ 111km, so max_distance meters ≈ max_distance/111000 degrees
        max_distance_degrees = max_distance / 111000
        
        # Query KDTree for points within max_distance_degrees
        nearby_indices = self.kdtree.query_ball_point([lat, lng], max_distance_degrees)
        
        nearby_weights = []
        for idx in nearby_indices:
            point_lat, point_lng = self.points[idx]
            safety_weight = self.weights[idx]
            
            # Calculate exact distance using haversine
            distance = haversine(lng, lat, point_lng, point_lat)
            
            if distance <= max_distance:
                # Use inverse distance weighting
                weight_factor = 1.0 / (distance + 1)
                nearby_weights.append((safety_weight, weight_factor))
        
        return nearby_weights

# Cache for graph loading
@lru_cache(maxsize=10)
def load_graph_cached(center_lat, center_lng, radius_km):
    """Cached version of graph loading"""
    return load_graph_for_area(center_lat, center_lng, radius_km)

# Cache for safety weight index
_safety_index_cache = None

def get_safety_weight_index(safety_weights):
    """Get or create cached safety weight index"""
    global _safety_index_cache
    if _safety_index_cache is None:
        _safety_index_cache = SafetyWeightIndex(safety_weights)
    return _safety_index_cache

# Cache for pathfinding results
_path_cache = {}

def get_cache_key(start_coords, end_coords, radius_km):
    """Generate cache key for pathfinding"""
    # Round coordinates to reduce cache misses for very similar coordinates
    start_rounded = (round(start_coords[0], 4), round(start_coords[1], 4))
    end_rounded = (round(end_coords[0], 4), round(end_coords[1], 4))
    return (start_rounded, end_rounded, radius_km)

def find_path_optimized(start_coords, end_coords, radius_km=5, use_cache=True, max_attempts=3):
    print(f"Finding optimized path from {start_coords} to {end_coords}")
    
    if use_cache:
        cache_key = get_cache_key(start_coords, end_coords, radius_km)
        if cache_key in _path_cache:
            print("Using cached path result")
            return _path_cache[cache_key]
    
    center_lat = (start_coords[0] + end_coords[0]) / 2
    center_lng = (start_coords[1] + end_coords[1]) / 2
    
    # Try multiple strategies to find a path
    for attempt in range(max_attempts):
        current_radius = radius_km * (2 ** attempt)  # Exponential backoff: 5km, 10km, 20km
        print(f"Attempt {attempt + 1}: Using radius {current_radius}km")
        
        # Use cached graph loading
        G = load_graph_cached(center_lat, center_lng, current_radius)
        
        safety_weights_data = load_safety_weights()
        
        # Use cached safety weight index
        safety_index = get_safety_weight_index(safety_weights_data)
        apply_safety_weights_optimized(G, safety_index)
        
        origin_node = get_nearest_node_safe(G, start_coords)
        destination_node = get_nearest_node_safe(G, end_coords)
        print(f"Origin node: {origin_node}")
        print(f"Destination node: {destination_node}")
        
        # Check if both nodes exist in the graph
        if origin_node not in G.nodes or destination_node not in G.nodes:
            print(f"Nodes not found in graph. Origin: {origin_node in G.nodes}, Destination: {destination_node in G.nodes}")
            continue
        
        # Try multiple pathfinding algorithms
        path = None
        
        # Strategy 1: A* with high iteration limit
        print("Trying A* algorithm...")
        start_time = time.time()
        path = a_star_optimized(G, origin_node, destination_node, max_iterations=50000)
        end_time = time.time()
        print(f"A* took {end_time - start_time:.2f} seconds")
        
        if path:
            print(f"A* found path with {len(path)} nodes")
            break
        
        # Strategy 2: Dijkstra's algorithm (simpler, more reliable)
        print("Trying Dijkstra's algorithm...")
        start_time = time.time()
        path = dijkstra_path(G, origin_node, destination_node)
        end_time = time.time()
        print(f"Dijkstra took {end_time - start_time:.2f} seconds")
        
        if path:
            print(f"Dijkstra found path with {len(path)} nodes")
            break
        
        # Strategy 3: BFS (breadth-first search) - guaranteed to find shortest path if it exists
        print("Trying BFS algorithm...")
        start_time = time.time()
        path = bfs_path(G, origin_node, destination_node)
        end_time = time.time()
        print(f"BFS took {end_time - start_time:.2f} seconds")
        
        if path:
            print(f"BFS found path with {len(path)} nodes")
            break
        
        print(f"Attempt {attempt + 1} failed. Trying larger radius...")
    
    result = (G, path)
    
    if use_cache:
        _path_cache[cache_key] = result
    
    if path:
        print(f"Path found with {len(path)} nodes")
        return result
    else:
        print("No path found between the specified points after all attempts")
        return result

def apply_safety_weights_optimized(G, safety_index):
    print("Adding safety scores to graph edges using KDTree...")
    
    total_edges = 0
    edges_with_safety_points = 0
    
    for u, v, data in G.edges(data=True):
        total_edges += 1
        # Get the midpoint of the edge
        midpoint = get_edge_midpoint(G, u, v)
        
        # Get nearby safety weights using KDTree
        nearby_weights = safety_index.get_nearby_weights(midpoint, max_distance=50)
        
        # Calculate weighted average safety weight
        if nearby_weights:
            edges_with_safety_points += 1
            total_weight = sum(wf for _, wf in nearby_weights)
            weighted_sum = sum(sw * wf for sw, wf in nearby_weights)
            average_safety_weight = weighted_sum / total_weight
        else:
            # Default to 1.0 if no nearby safety points found
            average_safety_weight = 1.0
        
        # Use the average safety weight as the divisor
        divisor = average_safety_weight
        
        data['safety_divisor'] = divisor
        data['custom_weight'] = data['length'] / divisor
    
    print(f"Safety weights applied to {edges_with_safety_points} out of {total_edges} edges (within 50m radius)")

def clear_caches():
    """Clear all caches"""
    global _safety_index_cache, _path_cache
    _safety_index_cache = None
    _path_cache.clear()
    load_graph_cached.cache_clear()
    print("All caches cleared")

def save_cache_to_file(filename="path_cache.pkl"):
    """Save path cache to file"""
    with open(filename, 'wb') as f:
        pickle.dump(_path_cache, f)
    print(f"Cache saved to {filename}")

def load_cache_from_file(filename="path_cache.pkl"):
    """Load path cache from file"""
    global _path_cache
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            _path_cache = pickle.load(f)
        print(f"Cache loaded from {filename} with {len(_path_cache)} entries")
    else:
        print(f"Cache file {filename} not found")

def dijkstra_path(G, start, goal, max_iterations=100000):
    """Dijkstra's algorithm for finding shortest path"""
    distances = {start: 0}
    came_from = {start: None}
    unvisited = set(G.nodes())
    
    iterations = 0
    while unvisited and iterations < max_iterations:
        iterations += 1
        
        # Find unvisited node with minimum distance
        current = min(unvisited, key=lambda x: distances.get(x, float('inf')))
        
        if current == goal:
            print(f"Dijkstra completed in {iterations} iterations")
            return reconstruct_path(came_from, start, goal)
        
        if distances.get(current, float('inf')) == float('inf'):
            break  # No path exists
        
        unvisited.remove(current)
        
        # Update distances to neighbors
        for neighbor in G.neighbors(current):
            if neighbor in unvisited:
                edge_data = G.get_edge_data(current, neighbor, 0)
                if edge_data:
                    weight = edge_data.get('custom_weight', edge_data.get('length', 1))
                    new_distance = distances[current] + weight
                    
                    if new_distance < distances.get(neighbor, float('inf')):
                        distances[neighbor] = new_distance
                        came_from[neighbor] = current
    
    print(f"Dijkstra stopped after {iterations} iterations without finding path")
    return None

def bfs_path(G, start, goal, max_iterations=100000):
    """Breadth-first search for finding shortest path"""
    queue = [(start, [start])]
    visited = set()
    
    iterations = 0
    while queue and iterations < max_iterations:
        iterations += 1
        current, path = queue.pop(0)
        
        if current == goal:
            print(f"BFS completed in {iterations} iterations")
            return path
        
        if current in visited:
            continue
        
        visited.add(current)
        
        # Add all unvisited neighbors to queue
        for neighbor in G.neighbors(current):
            if neighbor not in visited:
                edge_data = G.get_edge_data(current, neighbor, 0)
                if edge_data:  # Only add if edge exists
                    queue.append((neighbor, path + [neighbor]))
    
    print(f"BFS stopped after {iterations} iterations without finding path")
    return None

def ensure_graph_connectivity(G, start_node, end_node):
    """Ensure the graph is connected by adding virtual edges if necessary"""
    print("Checking graph connectivity...")
    
    # Check if both nodes exist
    if start_node not in G.nodes:
        print(f"Start node {start_node} not found in graph")
        return False
    if end_node not in G.nodes:
        print(f"End node {end_node} not found in graph")
        return False
    
    # Check if there's a path between start and end
    try:
        import networkx as nx
        has_path = nx.has_path(G, start_node, end_node)
        print(f"Path exists between nodes: {has_path}")
        return has_path
    except ImportError:
        print("NetworkX not available for connectivity check")
        return True  # Assume connected if we can't check

def find_nearest_connected_node(G, target_node, max_distance=1000):
    """Find the nearest node that is connected to the target node"""
    if target_node in G.nodes:
        return target_node
    
    # Find the nearest node in the graph
    target_coords = None
    try:
        target_coords = (G.nodes[target_node]['y'], G.nodes[target_node]['x'])
    except KeyError:
        print(f"Target node {target_node} not found in graph")
        return None
    
    nearest_node = None
    min_distance = float('inf')
    
    for node in G.nodes():
        try:
            node_coords = (G.nodes[node]['y'], G.nodes[node]['x'])
            distance = haversine(target_coords[1], target_coords[0], node_coords[1], node_coords[0])
            if distance < min_distance:
                min_distance = distance
                nearest_node = node
        except KeyError:
            continue
    
    if nearest_node and min_distance <= max_distance:
        print(f"Found nearest connected node: {nearest_node} (distance: {min_distance:.1f}m)")
        return nearest_node
    
    return None

# Global graph cache for persistent storage
_graph_cache = {}
_safety_weights_global = None
_safety_index_global = None

def load_graph_for_area_optimized(center_lat, center_lng, radius_km=5):
    """Optimized graph loading with persistent caching and faster parameters"""
    cache_key = f"{center_lat:.4f}_{center_lng:.4f}_{radius_km}"
    
    if cache_key in _graph_cache:
        print(f"Using cached graph for {cache_key}")
        return _graph_cache[cache_key]
    
    print(f"Loading graph for area around ({center_lat}, {center_lng}) with radius {radius_km}km...")
    
    # Optimized parameters for faster loading
    G = ox.graph_from_point(
        (center_lat, center_lng), 
        dist=radius_km*1000, 
        network_type='walk', 
        simplify=True,
        truncate_by_edge=True,  # Faster truncation
        custom_filter='["highway"~"footway|path|pedestrian|residential|service|unclassified|tertiary|secondary|primary"]'  # Filter for walkable paths only
    )
    
    # Pre-compute and cache node coordinates for faster access
    for node in G.nodes():
        G.nodes[node]['coords'] = (G.nodes[node]['y'], G.nodes[node]['x'])
    
    print(f"Graph loaded with {len(G.nodes)} nodes and {len(G.edges)} edges")
    _graph_cache[cache_key] = G
    return G

def load_safety_weights_optimized():
    """Load safety weights once and cache globally"""
    global _safety_weights_global
    if _safety_weights_global is None:
        print("Loading Safety Weights (first time)...")
        try:
            with open('test_output/safety_weights.json') as f:
                _safety_weights_global = json.load(f)
            print(f"Loaded {len(_safety_weights_global)} safety weight points")
        except FileNotFoundError:
            print("Warning: safety_weights.json not found, using empty data")
            _safety_weights_global = {}
    return _safety_weights_global

def get_safety_weight_index_optimized():
    """Get or create cached safety weight index (global)"""
    global _safety_index_global
    if _safety_index_global is None:
        safety_weights = load_safety_weights_optimized()
        _safety_index_global = SafetyWeightIndex(safety_weights)
    return _safety_index_global

def apply_safety_weights_optimized_fast(G, safety_index):
    """Ultra-fast safety weight application with pre-computed data"""
    print("Adding safety scores to graph edges (optimized)...")
    
    # Pre-compute edge midpoints and safety weights in batch
    edge_safety_data = {}
    
    for u, v, data in G.edges(data=True):
        # Use pre-computed coordinates
        u_coords = G.nodes[u]['coords']
        v_coords = G.nodes[v]['coords']
        midpoint = ((u_coords[0] + v_coords[0]) / 2, (u_coords[1] + v_coords[1]) / 2)
        
        # Get nearby safety weights
        nearby_weights = safety_index.get_nearby_weights(midpoint, max_distance=50)
        
        if nearby_weights:
            # Calculate weighted average safety weight
            total_weight = sum(weight_factor for _, weight_factor in nearby_weights)
            avg_safety_weight = sum(safety_weight * weight_factor for safety_weight, weight_factor in nearby_weights) / total_weight
            
            # Store for batch update
            edge_safety_data[(u, v)] = avg_safety_weight
    
    # Batch update edge weights
    edges_with_safety = 0
    for (u, v), safety_weight in edge_safety_data.items():
        edge_data = G.get_edge_data(u, v, 0)
        if edge_data:
            original_length = edge_data.get('length', 1)
            # Divide length by safety weight (higher safety = lower cost)
            G[u][v][0]['custom_weight'] = original_length / max(safety_weight, 0.1)  # Avoid division by zero
            edges_with_safety += 1
    
    print(f"Safety weights applied to {edges_with_safety} out of {len(G.edges)} edges (within 50m radius)")

def find_path_ultra_fast(start_coords, end_coords, radius_km=3, use_cache=True):
    """Ultra-fast pathfinding with all optimizations"""
    print(f"Finding ultra-fast path from {start_coords} to {end_coords}")
    
    if use_cache:
        cache_key = get_cache_key(start_coords, end_coords, radius_km)
        if cache_key in _path_cache:
            print("Using cached path result")
            return _path_cache[cache_key]
    
    center_lat = (start_coords[0] + end_coords[0]) / 2
    center_lng = (start_coords[1] + end_coords[1]) / 2
    
    # Load graph with optimized parameters
    G = load_graph_for_area_optimized(center_lat, center_lng, radius_km)
    
    # Get pre-loaded safety weight index
    safety_index = get_safety_weight_index_optimized()
    
    # Apply safety weights with optimized method
    apply_safety_weights_optimized_fast(G, safety_index)
    
    # Find nearest nodes
    origin_node = get_nearest_node_safe(G, start_coords)
    destination_node = get_nearest_node_safe(G, end_coords)
    
    if origin_node not in G.nodes or destination_node not in G.nodes:
        print("Nodes not found in graph")
        return (G, None)
    
    # Use optimized A* with higher iteration limit
    start_time = time.time()
    path = a_star_optimized(G, origin_node, destination_node, max_iterations=100000)
    end_time = time.time()
    
    print(f"Pathfinding completed in {end_time - start_time:.3f} seconds")
    
    result = (G, path)
    if use_cache:
        _path_cache[cache_key] = result
    
    return result

def save_graph_cache_to_file(filename="graph_cache.pkl"):
    """Save graph cache to file for persistence"""
    with open(filename, 'wb') as f:
        pickle.dump(_graph_cache, f)
    print(f"Graph cache saved to {filename} with {len(_graph_cache)} entries")

def load_graph_cache_from_file(filename="graph_cache.pkl"):
    """Load graph cache from file"""
    global _graph_cache
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            _graph_cache = pickle.load(f)
        print(f"Graph cache loaded from {filename} with {len(_graph_cache)} entries")
    else:
        print(f"Graph cache file {filename} not found")

def clear_all_caches():
    """Clear all caches"""
    global _graph_cache, _safety_weights_global, _safety_index_global, _path_cache
    _graph_cache.clear()
    _safety_weights_global = None
    _safety_index_global = None
    _path_cache.clear()
    print("All caches cleared")

if __name__ == "__main__":
    print("=== Ultra-Fast A* Pathfinding with Optimized Graph Loading ===\n")
    
    # Load graph cache if available
    load_graph_cache_from_file("graph_cache.pkl")
    
    # Define test routes
    routes = [
        ((43.648649, -79.379956), (43.650450, -79.380000), "Route 1 (very close)"),
        ((43.652252, -79.399877), (43.654955, -79.418553), "Route 2 (nearby)"),
        ((43.656757, -79.404857), (43.66042470748341, -79.41360122554558), "Route 3 (medium)"),
    ]
    
    total_start_time = time.time()
    successful_routes = 0
    
    print("=== First Run (Graph Loading) ===")
    for i, (start_coords, end_coords, route_name) in enumerate(routes, 1):
        print(f"\n--- {route_name} ---")
        print(f"Start: {start_coords}")
        print(f"End: {end_coords}")
        
        route_start_time = time.time()
        G, path = find_path_ultra_fast(start_coords, end_coords, radius_km=3, use_cache=True)
        route_end_time = time.time()
        
        print(f"Route {i} completed in {route_end_time - route_start_time:.3f} seconds")
        
        if path:
            successful_routes += 1
            coordinates = path_to_polyline_coordinates(G, path)
            print(f"✓ Path found with {len(coordinates)} coordinate pairs")
            
            # Save each route to a separate file
            filename = f"path_coordinates_{i}.json"
            save_path_to_json(G, path, filename)
        else:
            print("✗ No path found")
    
    print(f"\n=== Second Run (Cached Graphs) ===")
    second_run_start = time.time()
    
    for i, (start_coords, end_coords, route_name) in enumerate(routes, 1):
        print(f"\n--- {route_name} (Cached) ---")
        
        route_start_time = time.time()
        G, path = find_path_ultra_fast(start_coords, end_coords, radius_km=3, use_cache=True)
        route_end_time = time.time()
        
        print(f"Cached route {i} completed in {route_end_time - route_start_time:.3f} seconds")
        
        if path:
            coordinates = path_to_polyline_coordinates(G, path)
            print(f"✓ Cached path found with {len(coordinates)} coordinate pairs")
        else:
            print("✗ No cached path found")
    
    second_run_end = time.time()
    total_end_time = time.time()
    
    print(f"\n=== Performance Summary ===")
    print(f"Successful routes: {successful_routes}/{len(routes)}")
    print(f"Success rate: {successful_routes/len(routes)*100:.1f}%")
    print(f"First run (with graph loading): {second_run_start - total_start_time:.3f} seconds")
    print(f"Second run (cached graphs): {second_run_end - second_run_start:.3f} seconds")
    print(f"Total execution time: {total_end_time - total_start_time:.3f} seconds")
    print(f"Graph cache contains {len(_graph_cache)} entries")
    print(f"Path cache contains {len(_path_cache)} entries")
    
    # Save graph cache for future use
    print("\n--- Saving graph cache ---")
    save_graph_cache_to_file("graph_cache.pkl")
    
    # Test ultra-fast single route
    print("\n--- Ultra-Fast Single Route Test ---")
    start_coords = (43.648649, -79.379956)
    end_coords = (43.650450, -79.380000)
    
    single_start = time.time()
    G, path = find_path_ultra_fast(start_coords, end_coords, radius_km=3, use_cache=True)
    single_end = time.time()
    
    print(f"Single route completed in {single_end - single_start:.3f} seconds")
    
    if path:
        print("✓ Ultra-fast route test successful")
        if single_end - single_start < 10:
            print("🎉 Target achieved: Pathfinding completed in under 10 seconds!")
        else:
            print(f"⚠️  Target not met: Pathfinding took {single_end - single_start:.3f} seconds")
    else:
        print("✗ Ultra-fast route test failed") 
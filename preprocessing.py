import pandas as pd
import numpy as np
import json
from shapely.geometry import Point, LineString
from collections import defaultdict

def preprocess_collision_data(collision_csv_path, output_path="processed_collisions.csv"):
    """
    Preprocess Toronto collision data for route optimization
    
    Args:
        collision_csv_path: Path to raw Toronto collision CSV
        output_path: Where to save processed data
        
    Returns:
        DataFrame: Cleaned collision data with bicycle incidents
    """
    print(f"Loading collision data from {collision_csv_path}...")
    df = pd.read_csv(collision_csv_path)
    
    # Filter for bicycle-involved collisions only
    cyclist_collisions = df[df['BICYCLE'] == 'YES'].copy()
    print(f"Found {len(cyclist_collisions)} bicycle collisions out of {len(df)} total")
    
    # Clean coordinates - remove invalid/missing values
    cyclist_collisions = cyclist_collisions.dropna(subset=['LAT_WGS84', 'LONG_WGS84'])
    
    # Remove invalid coordinates (dataset has near-zero values)
    cyclist_collisions = cyclist_collisions[
        (cyclist_collisions['LAT_WGS84'] > 43.0) &
        (cyclist_collisions['LAT_WGS84'] < 44.0) &
        (cyclist_collisions['LONG_WGS84'] < -79.0) &
        (cyclist_collisions['LONG_WGS84'] > -80.0)
    ]
    
    # Convert date for temporal analysis
    if 'OCC_DATE' in cyclist_collisions.columns:
        cyclist_collisions['OCC_DATE'] = pd.to_numeric(cyclist_collisions['OCC_DATE'], errors='coerce')
        cyclist_collisions['collision_date'] = pd.to_datetime(cyclist_collisions['OCC_DATE'], unit='ms', errors='coerce')
    
    # Create simplified dataset for route optimization
    route_data = cyclist_collisions[['_id', 'LAT_WGS84', 'LONG_WGS84', 'OCC_YEAR', 'OCC_HOUR', 'DIVISION']].copy()
    route_data = route_data.rename(columns={
        'LAT_WGS84': 'latitude', 
        'LONG_WGS84': 'longitude',
        'OCC_YEAR': 'year',
        'OCC_HOUR': 'hour'
    })
    
    print(f"Cleaned data: {len(route_data)} valid bicycle collisions")
    
    # Save processed data
    route_data.to_csv(output_path, index=False)
    print(f"Saved processed collision data to {output_path}")
    
    return route_data

def preprocess_bike_lanes(bike_lanes_csv_path, output_path="processed_bike_lanes.csv"):
    """
    Preprocess Toronto cycling network data for route optimization
    
    Args:
        bike_lanes_csv_path: Path to raw bike lanes CSV
        output_path: Where to save processed data
        
    Returns:
        DataFrame: Cleaned bike lane data with parsed geometries
    """
    print(f"Loading bike lane data from {bike_lanes_csv_path}...")
    df = pd.read_csv(bike_lanes_csv_path)
    
    # Clean bike lane data
    bike_lanes = df.dropna(subset=['SEGMENT_ID', 'geometry']).copy()
    bike_lanes = bike_lanes.drop_duplicates(subset=['SEGMENT_ID'])
    
    # Parse geometry JSON strings
    def parse_geometry_safe(geom_str):
        try:
            geom_dict = json.loads(geom_str)
            if geom_dict['type'] == 'MultiLineString':
                return geom_dict['coordinates'][0]  
            return None
        except:
            return None
    
    bike_lanes['parsed_coordinates'] = bike_lanes['geometry'].apply(parse_geometry_safe)
    bike_lanes = bike_lanes.dropna(subset=['parsed_coordinates'])
    
    # Create simplified dataset for route optimization
    route_bike_data = bike_lanes[[
        'SEGMENT_ID', 'STREET_NAME', 'INFRA_HIGHORDER', 'INFRA_LOWORDER', 
        'parsed_coordinates', 'INSTALLED', 'UPGRADED'
    ]].copy()
    
    print(f"Processed {len(route_bike_data)} bike lane segments")
    
    # Save processed data
    route_bike_data.to_csv(output_path, index=False)
    print(f"Saved processed bike lane data to {output_path}")
    
    return route_bike_data

def create_collision_density_grid(collision_data, grid_size_meters=100):
    """
    Create a grid of collision density for fast route optimization lookups
    
    Args:
        collision_data: DataFrame with latitude/longitude columns
        grid_size_meters: Size of each grid cell in meters
        
    Returns:
        dict: Grid coordinates mapped to collision counts
    """
    print(f"Creating collision density grid with {grid_size_meters}m cells...")
    
    # Convert grid size to approximate degrees (rough approximation for Toronto)
    meters_per_degree_lat = 111000
    meters_per_degree_lng = 111000 * np.cos(np.radians(43.65))  # Toronto latitude
    
    grid_size_lat = grid_size_meters / meters_per_degree_lat
    grid_size_lng = grid_size_meters / meters_per_degree_lng
    
    collision_grid = defaultdict(int)
    
    for _, row in collision_data.iterrows():
        # Snap to grid
        grid_lat = round(row['latitude'] / grid_size_lat) * grid_size_lat
        grid_lng = round(row['longitude'] / grid_size_lng) * grid_size_lng
        
        grid_key = f"{grid_lat:.6f},{grid_lng:.6f}"
        collision_grid[grid_key] += 1
    
    print(f"Created grid with {len(collision_grid)} populated cells")
    return dict(collision_grid)

def create_safety_weights_for_edges(collision_grid, grid_size_meters=100):
    """
    Convert collision grid to safety weights for route optimization
    
    Args:
        collision_grid: Dictionary from create_collision_density_grid()
        grid_size_meters: Grid cell size used
        
    Returns:
        dict: Grid coordinates mapped to safety weights (lower = safer)
    """
    print("Converting collision counts to safety weights...")
    
    safety_weights = {}
    max_collisions = max(collision_grid.values()) if collision_grid else 1
    
    for grid_key, collision_count in collision_grid.items():
        # Safety weight: higher collisions = higher cost
        # Range from 1.0 (safest) to 5.0 (most dangerous)
        if collision_count == 0:
            safety_weight = 1.0
        else:
            # Normalize collision count and scale
            normalized = collision_count / max_collisions
            safety_weight = 1.0 + (normalized * 4.0)
        
        safety_weights[grid_key] = safety_weight
    
    return safety_weights

def export_for_route_optimization(collision_data, bike_lane_data, collision_grid, safety_weights, 
                                output_dir="route_optimization_data/"):
    """
    Export all preprocessed data for route optimization module
    
    Args:
        collision_data: Processed collision DataFrame
        bike_lane_data: Processed bike lane DataFrame  
        collision_grid: Collision density grid
        safety_weights: Safety weight grid
        output_dir: Directory to save files
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Export collision points as simple coordinates
    collision_coords = collision_data[['latitude', 'longitude']].values.tolist()
    with open(f"{output_dir}/collision_points.json", 'w') as f:
        json.dump(collision_coords, f)
    
    # Export collision grid
    with open(f"{output_dir}/collision_grid.json", 'w') as f:
        json.dump(collision_grid, f)
    
    # Export safety weights
    with open(f"{output_dir}/safety_weights.json", 'w') as f:
        json.dump(safety_weights, f)
    
    # Export bike lane segments
    bike_segments = []
    for _, row in bike_lane_data.iterrows():
        bike_segments.append({
            'segment_id': row['SEGMENT_ID'],
            'street_name': row['STREET_NAME'],
            'infrastructure': row['INFRA_HIGHORDER'],
            'coordinates': eval(row['parsed_coordinates']) if isinstance(row['parsed_coordinates'], str) else row['parsed_coordinates']
        })
    
    with open(f"{output_dir}/bike_segments.json", 'w') as f:
        json.dump(bike_segments, f)
    
    # Create summary stats
    summary = {
        'total_collisions': len(collision_data),
        'date_range': f"{collision_data['year'].min()}-{collision_data['year'].max()}" if 'year' in collision_data.columns else 'Unknown',
        'grid_cells': len(collision_grid),
        'bike_segments': len(bike_lane_data),
        'processing_date': pd.Timestamp.now().isoformat()
    }
    
    with open(f"{output_dir}/summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Exported route optimization data to {output_dir}")
    print(f"Summary: {summary}")

def main():
    """
    Main preprocessing pipeline for Toronto bicycle route optimization
    """
    print("=== Toronto Bicycle Route Safety Preprocessing ===")
    
    # Step 1: Process collision data
    collision_data = preprocess_collision_data("toronto_collisions.csv")
    
    # Step 2: Process bike lane data
    bike_lane_data = preprocess_bike_lanes("cycling_network.csv")
    
    # Step 3: Create collision density grid for fast lookups
    collision_grid = create_collision_density_grid(collision_data, grid_size_meters=50)
    
    # Step 4: Convert to safety weights
    safety_weights = create_safety_weights_for_edges(collision_grid)
    
    # Step 5: Export everything for route optimization
    export_for_route_optimization(collision_data, bike_lane_data, collision_grid, safety_weights)
    
    print("\n=== Preprocessing Complete ===")
    print("Ready for route optimization module!")

if __name__ == "__main__":
    main()
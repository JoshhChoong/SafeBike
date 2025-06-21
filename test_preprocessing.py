#!/usr/bin/env python3
"""
Test script for SafeBike data preprocessing
Run this to test just the preprocessing step without the full route optimization
"""

import os
import sys
import json
from preprocessing import (
    preprocess_collision_data, 
    preprocess_bike_lanes,
    create_collision_density_grid,
    create_safety_weights_for_edges,
    export_for_route_optimization
)

def test_data_files_exist():
    """Check if required data files exist"""
    print("=== Checking Data Files ===")
    
    required_files = [
        'toronto_collisions.csv',
        'cycling_network.csv'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ Found {file}")
        else:
            print(f"✗ Missing {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\nError: Missing required files: {missing_files}")
        print("Please add these files to the SafeBike directory")
        return False
    
    return True

def test_preprocessing_step_by_step():
    """Test each preprocessing step individually"""
    print("\n=== Testing Preprocessing Steps ===")
    
    try:
        # Step 1: Test collision data preprocessing
        print("\n1. Testing collision data preprocessing...")
        collision_data = preprocess_collision_data("toronto_collisions.csv", "test_collisions.csv")
        print(f"   ✓ Processed {len(collision_data)} collision records")
        
        # Step 2: Test bike lane preprocessing  
        print("\n2. Testing bike lane preprocessing...")
        bike_lane_data = preprocess_bike_lanes("cycling_network.csv", "test_bike_lanes.csv")
        print(f"   ✓ Processed {len(bike_lane_data)} bike lane segments")
        
        # Step 3: Test collision grid creation
        print("\n3. Testing collision density grid...")
        collision_grid = create_collision_density_grid(collision_data)
        print(f"   ✓ Created grid with {len(collision_grid)} populated cells")
        
        # Step 4: Test safety weight calculation
        print("\n4. Testing safety weight calculation...")
        safety_weights = create_safety_weights_for_edges(collision_grid)
        print(f"   ✓ Generated {len(safety_weights)} safety weights")
        
        # Step 5: Test data export
        print("\n5. Testing data export...")
        export_for_route_optimization(collision_data, bike_lane_data, collision_grid, safety_weights, "test_output/")
        print("   ✓ Exported all data for route optimization")
        
        return True, collision_data, bike_lane_data, collision_grid, safety_weights
        
    except Exception as e:
        print(f"   ✗ Error during preprocessing: {e}")
        return False, None, None, None, None

def validate_output_data(collision_data, bike_lane_data, collision_grid, safety_weights):
    """Validate the quality of preprocessed data"""
    print("\n=== Validating Output Data ===")
    
    # Check collision data quality
    print("\nCollision Data Validation:")
    print(f"  - Total records: {len(collision_data)}")
    print(f"  - Latitude range: {collision_data['latitude'].min():.4f} to {collision_data['latitude'].max():.4f}")
    print(f"  - Longitude range: {collision_data['longitude'].min():.4f} to {collision_data['longitude'].max():.4f}")
    
    if 'year' in collision_data.columns:
        print(f"  - Year range: {collision_data['year'].min()} to {collision_data['year'].max()}")
    
    # Check bike lane data quality
    print(f"\nBike Lane Data Validation:")
    print(f"  - Total segments: {len(bike_lane_data)}")
    print(f"  - Infrastructure types: {bike_lane_data['INFRA_HIGHORDER'].nunique()}")
    print(f"  - Top infrastructure types:")
    for infra_type, count in bike_lane_data['INFRA_HIGHORDER'].value_counts().head(3).items():
        print(f"    - {infra_type}: {count}")
    
    # Check collision grid
    print(f"\nCollision Grid Validation:")
    print(f"  - Grid cells with collisions: {len(collision_grid)}")
    print(f"  - Max collisions per cell: {max(collision_grid.values())}")
    print(f"  - Average collisions per cell: {sum(collision_grid.values()) / len(collision_grid):.2f}")
    
    # Check safety weights
    print(f"\nSafety Weights Validation:")
    print(f"  - Weight range: {min(safety_weights.values()):.2f} to {max(safety_weights.values()):.2f}")
    print(f"  - Average weight: {sum(safety_weights.values()) / len(safety_weights):.2f}")

def test_output_files():
    """Test that output files were created correctly"""
    print("\n=== Testing Output Files ===")
    
    expected_files = [
        'test_output/collision_points.json',
        'test_output/collision_grid.json', 
        'test_output/safety_weights.json',
        'test_output/bike_segments.json',
        'test_output/summary.json'
    ]
    
    all_files_exist = True
    for file_path in expected_files:
        if os.path.exists(file_path):
            print(f"✓ Created {file_path}")
            
            # Test file can be loaded
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                print(f"  - File is valid JSON with {len(data) if isinstance(data, (list, dict)) else 'unknown'} items")
            except:
                print(f"  - Warning: File exists but may have JSON issues")
        else:
            print(f"✗ Missing {file_path}")
            all_files_exist = False
    
    return all_files_exist

def cleanup_test_files():
    """Clean up test files"""
    print("\n=== Cleaning Up Test Files ===")
    
    test_files = [
        'test_collisions.csv',
        'test_bike_lanes.csv'
    ]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"✓ Removed {file}")

def main():
    """Run full preprocessing test"""
    print("SafeBike Data Preprocessing Test")
    print("=" * 40)
    
    # Check if data files exist
    if not test_data_files_exist():
        sys.exit(1)
    
    # Run preprocessing tests
    success, collision_data, bike_lane_data, collision_grid, safety_weights = test_preprocessing_step_by_step()
    
    if not success:
        print("\n❌ Preprocessing test FAILED")
        sys.exit(1)
    
    # Validate output
    validate_output_data(collision_data, bike_lane_data, collision_grid, safety_weights)
    
    # Test output files
    if test_output_files():
        print("\n✅ All output files created successfully")
    else:
        print("\n⚠️  Some output files missing")
    
    # Cleanup
    cleanup_test_files()
    
    print("\n" + "=" * 40)
    print("✅ PREPROCESSING TEST COMPLETED SUCCESSFULLY!")
    print("\nNext steps:")
    print("1. Review the test_output/ directory")
    print("2. Integrate with your existing astar.py")
    print("3. Modify route optimization to use safety_weights.json")

if __name__ == "__main__":
    main()
# Safety Scoring System

This document explains the new safety scoring system that replaces the previous lighting score system.

## Overview

The system now considers two safety factors:
1. **Cycling Lanes** - Positive factor (preferred routes)
2. **Car Accidents** - Negative factor (avoided routes)

## How It Works

### Base System
- Each edge starts with a **base divisor of 1.0**
- Custom weight = `length / divisor`
- **Higher divisor** = **Lower weight** = **Preferred path**
- **Lower divisor** = **Higher weight** = **Avoided path**

### Cycling Lanes (Positive Factor)
- **Distance**: Within 50 meters of edge midpoint
- **Effect**: Increases divisor by **0.10**
- **Result**: Makes the path more attractive (lower weight)

### Car Accidents (Negative Factor)
- **Distance**: Within 500 meters of edge midpoint
- **Effect**: Decreases divisor by **0.20**
- **Result**: Makes the path less attractive (higher weight)

## Scoring Examples

### Example 1: Safe Route
- Edge length: 100m
- Cycling lane within 50m: ✅ (+0.10)
- Car accident within 500m: ❌ (-0.20)
- **Final divisor**: 1.0 + 0.10 - 0.20 = **0.90**
- **Custom weight**: 100 / 0.90 = **111.11** (higher weight, avoided)

### Example 2: Preferred Route
- Edge length: 100m
- Cycling lane within 50m: ✅ (+0.10)
- Car accident within 500m: ❌ (none)
- **Final divisor**: 1.0 + 0.10 = **1.10**
- **Custom weight**: 100 / 1.10 = **90.91** (lower weight, preferred)

### Example 3: Neutral Route
- Edge length: 100m
- Cycling lane within 50m: ❌ (none)
- Car accident within 500m: ❌ (none)
- **Final divisor**: 1.0 = **1.00**
- **Custom weight**: 100 / 1.00 = **100.00** (neutral weight)

## File Structure

### Required JSON Files

#### `cycling_lanes.json`
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [longitude, latitude]
      },
      "properties": {
        "name": "Cycling Lane Name",
        "type": "dedicated_lane"
      }
    }
  ]
}
```

#### `car_accidents.json`
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [longitude, latitude]
      },
      "properties": {
        "date": "2023-01-15",
        "severity": "moderate",
        "type": "intersection_collision"
      }
    }
  ]
}
```

## Implementation Details

### Distance Calculation
Uses the **Haversine formula** to calculate great-circle distances between coordinates:
- Accurate for geographic distances
- Accounts for Earth's curvature
- Returns distance in meters

### Edge Midpoint
For each edge (street segment):
1. Gets coordinates of both nodes
2. Calculates midpoint: `((lat1 + lat2)/2, (lon1 + lon2)/2)`
3. Checks distance from midpoint to all features

### Safety Thresholds
- **Cycling lanes**: 50 meters (close proximity)
- **Car accidents**: 500 meters (wider area of concern)

## Algorithm Behavior

The A* algorithm will now:
1. **Prefer routes** with cycling lanes nearby
2. **Avoid routes** with recent car accidents nearby
3. **Balance** distance with safety factors
4. **Find optimal paths** that maximize safety while minimizing distance

## Output Changes

- **Description**: Now says "optimized for cycling safety and accident avoidance"
- **Debug output**: Shows when cycling lanes or accidents are found near edges
- **Weight calculation**: Uses `safety_divisor` instead of `lighting_score`

## Testing

The system includes sample data files:
- `cycling_lanes.json` - 3 sample cycling lanes
- `car_accidents.json` - 3 sample accident locations

These can be replaced with real data from your city's open data sources. 
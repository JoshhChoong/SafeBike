# A* Pathfinding with Streetlight Visibility Optimization

This project implements an A* pathfinding algorithm that finds optimal walking routes in Toronto, prioritizing paths with high visibility from streetlights. The system generates polylines that can be directly used with the Google Maps API.

## Features

- **A* Pathfinding Algorithm**: Finds optimal routes between two points
- **Streetlight Visibility Optimization**: Prioritizes well-lit streets for safety
- **Google Maps Integration**: Generates polylines ready for Google Maps API
- **Multiple Output Formats**: JSON, GeoJSON, and JavaScript code
- **Web API**: Flask server for easy integration
- **Interactive Interface**: Web-based interface for testing

## Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd Safwalk
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Get a Google Maps API Key**:
   - create env and paste api key from discord

## Usage

### Method 1: Command Line (Direct Python Script)

Run the A* algorithm directly:

```bash
python astar.py
```

This will:
- Load the Toronto walking network
- Apply streetlight visibility weights
- Find a path between the default coordinates
- Generate `path_coordinates.json` and `google_maps_polyline.js`

### Method 2: Web API (Recommended)

Start the Flask server:

```bash
python app.py
```

Then open your browser to `http://localhost:5000` to use the web interface.

### Method 3: Google Maps Integration

1. Run the Python script to generate coordinates:
   ```bash
   python astar.py
   ```

2. Open `google_maps_example.html` in a web browser
3. Click "Load from JSON File" to display the path

## API Endpoints

### POST /api/path
Find an A* path between two points.

**Request Body**:
```json
{
  "start_lat": 43.65107,
  "start_lng": -79.347016,
  "end_lat": 43.6532,
  "end_lng": -79.3832
}
```

**Response**:
```json
{
  "success": true,
  "coordinates": [
    {"lat": 43.65107, "lng": -79.347016},
    {"lat": 43.6515, "lng": -79.3480},
    ...
  ],
  "geojson": {
    "type": "Feature",
    "geometry": {
      "type": "LineString",
      "coordinates": [[-79.347016, 43.65107], ...]
    }
  },
  "path_info": {
    "node_count": 15,
    "coordinate_count": 15
  }
}
```

### GET /api/health
Health check endpoint.

## File Structure

```
Safwalk/
├── astar.py                 # Main A* algorithm implementation
├── app.py                   # Flask web server
├── google_maps_example.html # Google Maps integration example
├── kwtest1_geometry_only.json # Streetlight data
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── path_coordinates.json   # Generated path coordinates (after running)
└── google_maps_polyline.js # Generated JavaScript code (after running)
```

## How It Works

### 1. Graph Construction
- Uses OSMnx to load Toronto's walking network from OpenStreetMap
- Each edge represents a walkable street segment

### 2. Streetlight Weighting
- Loads streetlight visibility data from `kwtest1_geometry_only.json`
- Assigns lighting scores to each edge
- Calculates custom weights: `length / lighting_score`
- Higher lighting scores = lower weights = preferred paths

### 3. A* Algorithm
- Uses Euclidean distance as heuristic
- Finds optimal path considering both distance and lighting
- Returns sequence of node IDs

### 4. Polyline Generation
- Converts node IDs to latitude/longitude coordinates
- Formats for Google Maps API: `{lat: x, lng: y}`
- Also generates GeoJSON format for other mapping libraries

## Customization

### Changing Start/End Points

Edit the coordinates in `astar.py`:

```python
start_coords = (43.65107, -79.347016)  # Your start point
end_coords = (43.6532, -79.3832)       # Your end point
```

### Modifying Path Styling

In `google_maps_example.html`, customize the polyline:

```javascript
const routePath = new google.maps.Polyline({
  path: coordinates,
  geodesic: true,
  strokeColor: "#FF0000",    // Red path
  strokeOpacity: 0.8,        // 80% opacity
  strokeWeight: 6            // Thicker line
});
```

### Adjusting Lighting Weights

Modify the weight calculation in `astar.py`:

```python
# Current: prefers well-lit paths
data['custom_weight'] = data['length'] / data['lighting_score']

# Alternative: balance distance and lighting
data['custom_weight'] = data['length'] * (1 + (1 - data['lighting_score']))
```

## Troubleshooting

### Common Issues

1. **"No path found" error**:
   - Check if coordinates are within Toronto area
   - Ensure coordinates are valid latitude/longitude values

2. **Google Maps not loading**:
   - Verify API key is correct
   - Check if Maps JavaScript API is enabled
   - Ensure billing is set up in Google Cloud Console

3. **OSMnx download issues**:
   - Check internet connection
   - Try running with `ox.config(use_cache=True)`

4. **Missing dependencies**:
   - Run `pip install -r requirements.txt`
   - On Windows, you might need to install Visual C++ build tools

### Performance Tips

- The graph is cached after first load
- For production, consider pre-computing common routes
- Use smaller geographic areas for faster processing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [OSMnx](https://github.com/gboeing/osmnx) for OpenStreetMap data processing
- [OpenStreetMap](https://www.openstreetmap.org/) for map data
- [Google Maps Platform](https://developers.google.com/maps) for mapping services 
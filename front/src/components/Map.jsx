import { useEffect, useRef, useState } from 'react';
import { Loader } from '@googlemaps/js-api-loader';
import './Map.css';

function Map() {
  const mapRef = useRef(null);
  const [map, setMap] = useState(null);
  const [currentPath, setCurrentPath] = useState(null);
  const [markers, setMarkers] = useState([]);
  const pathCoordinatesRef = useRef([]);


  /* global google */
    const flatWhiteStyle = [
    // hide all labels
    { elementType: 'labels', stylers: [{ visibility: 'off' }] },

    // make the base land plain white
    { elementType: 'geometry', stylers: [{ color: '#ffffff' }] },

    // thin light-grey roads
    { featureType: 'road', elementType: 'geometry',
        stylers: [{ color: '#eaeaea' }] },

    // very light road strokes
    { featureType: 'road', elementType: 'geometry.stroke',
        stylers: [{ color: '#d5d5d5' }] },

    // tint water to match your secondary brand colour
    { featureType: 'water', elementType: 'geometry',
        stylers: [{ color: '#D9F0F4' }] }
    ];

  useEffect(() => {
    const loader = new Loader({
      apiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY,
      libraries: ["geometry"]
    });

    loader.load().then(() => {
        /* global google */
      const mapInstance = new google.maps.Map(mapRef.current, {
        center: { lat: 43.504894, lng: -80.518974 },
        zoom: 13,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        styles: flatWhiteStyle
      });

      setMap(mapInstance);
      setTimeout(() => loadPathFromFile(mapInstance), 1000);
    });
  }, []);

  const addMarker = (mapInstance, position, title, color = '#F4E55A') => {
    const marker = new google.maps.Marker({
      position,
      map: mapInstance,
      title,
      icon: {
        path: google.maps.SymbolPath.CIRCLE,
        scale: 8,
        fillColor: color,
        fillOpacity: 1,
        strokeColor: '#000000',
        strokeWeight: 2
      }
    });
    setMarkers(prev => [...prev, marker]);
  };

  const clearMarkers = () => {
    markers.forEach(marker => marker.setMap(null));
    setMarkers([]);
  };

  const clearPath = () => {
    if (currentPath) {
      currentPath.setMap(null);
      setCurrentPath(null);
    }
    clearMarkers();
  };

  const drawPath = (mapInstance, coordinates, color = "#D9F0F4", weight = 4, opacity = 1.0) => {
    clearMarkers();
    if (coordinates.length === 0) return;

    addMarker(mapInstance, coordinates[0], "Start", "#00FF00");
    addMarker(mapInstance, coordinates[coordinates.length - 1], "End", "#FF0000");

    const polyline = new google.maps.Polyline({
      path: coordinates,
      geodesic: true,
      strokeColor: color,
      strokeOpacity: opacity,
      strokeWeight: weight
    });

    polyline.setMap(mapInstance);
    setCurrentPath(polyline);
    fitToRoute(mapInstance, coordinates);
  };

  const fitToRoute = (mapInstance, coords) => {
    const bounds = new google.maps.LatLngBounds();
    coords.forEach(coord => bounds.extend(coord));
    mapInstance.fitBounds(bounds);
    google.maps.event.addListenerOnce(mapInstance, 'bounds_changed', () => {
      mapInstance.setZoom(Math.min(mapInstance.getZoom(), 15));
    });
  };

  const loadPathFromFile = (mapInstance) => {
    fetch('/path_coordinates.json')
      .then(res => res.json())
      .then(data => {
        const coords = data.geometry.coordinates.map(coord => ({
          lat: coord[1],
          lng: coord[0]
        }));
        pathCoordinatesRef.current = coords;
        drawPath(mapInstance, coords);
      })
      .catch(err => {
        console.error('Error loading JSON:', err);
        alert('Failed to load path_coordinates.json');
      });
  };

  return (
    <div className='map-content'>
      <div id="map" ref={mapRef} style={{ height: '100%', width: '100%' }}></div>
    </div>
  );
}

export default Map;

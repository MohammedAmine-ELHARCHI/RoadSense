import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import { useEffect, useState } from 'react'
import { getMockDetections } from '../services/api'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix for default markers
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

const MapPage = () => {
  const [detections, setDetections] = useState([])
  const [selectedType, setSelectedType] = useState('all')

  useEffect(() => {
    setDetections(getMockDetections())
  }, [])

  const filteredDetections = selectedType === 'all' 
    ? detections 
    : detections.filter(d => d.type === selectedType)

  // Casablanca center
  const center = [33.5731, -7.5898]

  return (
    <div className="h-full flex flex-col">
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-4">
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium text-gray-700">Filter by type:</label>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Types</option>
            <option value="D00">D00 - Longitudinal Crack</option>
            <option value="D10">D10 - Transverse Crack</option>
            <option value="D20">D20 - Alligator Crack</option>
            <option value="D40">D40 - Pothole</option>
            <option value="D43">D43 - Crosswalk Blur</option>
            <option value="D44">D44 - White Line Blur</option>
            <option value="D50">D50 - Lateral Crack</option>
          </select>
          <span className="text-sm text-gray-600">
            Showing {filteredDetections.length} detection(s)
          </span>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 bg-white rounded-lg shadow overflow-hidden">
        <MapContainer 
          center={center} 
          zoom={13} 
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {filteredDetections.map((detection) => (
            <Marker 
              key={detection.id} 
              position={[detection.location.lat, detection.location.lng]}
            >
              <Popup>
                <div className="p-2">
                  <h3 className="font-bold text-lg mb-2">{detection.type}</h3>
                  <div className="space-y-1 text-sm">
                    <p><strong>Confidence:</strong> {(detection.confidence * 100).toFixed(0)}%</p>
                    <p><strong>Severity:</strong> {detection.severity.toFixed(1)}/10</p>
                    <p>
                      <strong>Level:</strong>{' '}
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        detection.severity_level === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                        detection.severity_level === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                        detection.severity_level === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {detection.severity_level}
                      </span>
                    </p>
                    <p className="text-gray-500">
                      {new Date(detection.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  )
}

export default MapPage

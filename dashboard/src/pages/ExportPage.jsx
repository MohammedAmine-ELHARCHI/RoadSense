import { Download } from 'lucide-react'

const ExportPage = () => {
  const exportFormats = [
    { name: 'GeoJSON', description: 'Geographic data in JSON format', extension: '.geojson' },
    { name: 'Shapefile', description: 'ESRI Shapefile for GIS software', extension: '.zip' },
    { name: 'KML', description: 'Google Earth compatible format', extension: '.kml' },
    { name: 'CSV', description: 'Comma-separated values', extension: '.csv' },
    { name: 'PDF Report', description: 'Comprehensive analysis report', extension: '.pdf' },
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h2 className="text-xl font-semibold">Export Data</h2>
          <p className="text-sm text-gray-600 mt-1">Download detection results in various formats</p>
        </div>

        <div className="p-6 space-y-4">
          {exportFormats.map((format) => (
            <div key={format.name} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
              <div>
                <h3 className="font-semibold">{format.name}</h3>
                <p className="text-sm text-gray-600">{format.description}</p>
              </div>
              <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                <Download size={18} />
                <span>Export</span>
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default ExportPage

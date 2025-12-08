import { useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle, XCircle, Activity } from 'lucide-react'
import { Chart as ChartJS, ArcElement, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend } from 'chart.js'
import { Doughnut, Bar } from 'react-chartjs-2'
import { getMockDetections } from '../services/api'

ChartJS.register(ArcElement, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend)

const StatCard = ({ title, value, icon: Icon, color, subtitle }) => (
  <div className="bg-white rounded-lg shadow p-6">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-600">{title}</p>
        <p className={`text-3xl font-bold ${color}`}>{value}</p>
        {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
      </div>
      <div className={`p-3 rounded-full ${color.replace('text', 'bg').replace('600', '100')}`}>
        <Icon className={color} size={24} />
      </div>
    </div>
  </div>
)

const HomePage = () => {
  const [detections, setDetections] = useState([])
  const [stats, setStats] = useState({
    total: 0,
    critical: 0,
    high: 0,
    medium: 0,
    low: 0
  })

  useEffect(() => {
    // Load mock data
    const mockData = getMockDetections()
    setDetections(mockData)

    // Calculate stats
    const critical = mockData.filter(d => d.severity_level === 'CRITICAL').length
    const high = mockData.filter(d => d.severity_level === 'HIGH').length
    const medium = mockData.filter(d => d.severity_level === 'MEDIUM').length
    const low = mockData.filter(d => d.severity_level === 'LOW').length

    setStats({
      total: mockData.length,
      critical,
      high,
      medium,
      low
    })
  }, [])

  const severityData = {
    labels: ['Critical', 'High', 'Medium', 'Low'],
    datasets: [{
      label: 'Defects by Severity',
      data: [stats.critical, stats.high, stats.medium, stats.low],
      backgroundColor: [
        'rgba(239, 68, 68, 0.8)',
        'rgba(249, 115, 22, 0.8)',
        'rgba(234, 179, 8, 0.8)',
        'rgba(34, 197, 94, 0.8)',
      ],
      borderWidth: 0
    }]
  }

  const defectTypeData = {
    labels: ['D00', 'D10', 'D20', 'D40', 'D43', 'D44', 'D50'],
    datasets: [{
      label: 'Defects by Type',
      data: [8, 12, 15, 5, 3, 7, 10],
      backgroundColor: 'rgba(59, 130, 246, 0.8)',
    }]
  }

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Detections"
          value={stats.total}
          icon={Activity}
          color="text-blue-600"
          subtitle="Last 24 hours"
        />
        <StatCard
          title="Critical Issues"
          value={stats.critical}
          icon={XCircle}
          color="text-red-600"
          subtitle="Requires immediate attention"
        />
        <StatCard
          title="High Priority"
          value={stats.high}
          icon={AlertTriangle}
          color="text-orange-600"
          subtitle="Schedule repair soon"
        />
        <StatCard
          title="Low/Medium"
          value={stats.medium + stats.low}
          icon={CheckCircle}
          color="text-green-600"
          subtitle="Monitor condition"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Severity Distribution</h3>
          <div className="h-64 flex items-center justify-center">
            <Doughnut data={severityData} options={{ maintainAspectRatio: false }} />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Defects by Type</h3>
          <div className="h-64">
            <Bar 
              data={defectTypeData} 
              options={{ 
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
              }} 
            />
          </div>
        </div>
      </div>

      {/* Recent Detections */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h3 className="text-lg font-semibold">Recent Detections</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Confidence</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Severity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Level</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {detections.map((detection) => (
                <tr key={detection.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                      {detection.type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {(detection.confidence * 100).toFixed(0)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {detection.severity.toFixed(1)}/10
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      detection.severity_level === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                      detection.severity_level === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                      detection.severity_level === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {detection.severity_level}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(detection.timestamp).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default HomePage

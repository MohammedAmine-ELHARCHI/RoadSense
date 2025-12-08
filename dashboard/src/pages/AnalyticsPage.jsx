import { Bar, Line } from 'react-chartjs-2'

const AnalyticsPage = () => {
  const timelineData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [{
      label: 'Detections per Day',
      data: [12, 19, 15, 25, 22, 18, 20],
      borderColor: 'rgb(59, 130, 246)',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      tension: 0.4
    }]
  }

  const severityTrendData = {
    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
    datasets: [
      {
        label: 'Critical',
        data: [5, 7, 4, 6],
        backgroundColor: 'rgba(239, 68, 68, 0.8)',
      },
      {
        label: 'High',
        data: [8, 12, 10, 15],
        backgroundColor: 'rgba(249, 115, 22, 0.8)',
      },
      {
        label: 'Medium',
        data: [15, 18, 20, 22],
        backgroundColor: 'rgba(234, 179, 8, 0.8)',
      }
    ]
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Detection Timeline</h2>
        <div className="h-80">
          <Line data={timelineData} options={{ maintainAspectRatio: false }} />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Severity Trends</h2>
        <div className="h-80">
          <Bar 
            data={severityTrendData} 
            options={{ 
              maintainAspectRatio: false,
              scales: { x: { stacked: true }, y: { stacked: true } }
            }} 
          />
        </div>
      </div>
    </div>
  )
}

export default AnalyticsPage

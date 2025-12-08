const PriorityPage = () => {
  const priorityList = [
    { id: 1, road: 'Avenue Hassan II', defects: 12, avgSeverity: 9.2, priority: 'CRITICAL' },
    { id: 2, road: 'Boulevard Mohammed V', defects: 8, avgSeverity: 8.5, priority: 'HIGH' },
    { id: 3, road: 'Rue Abdelmoumen', defects: 15, avgSeverity: 7.8, priority: 'HIGH' },
    { id: 4, road: 'Boulevard Zerktouni', defects: 6, avgSeverity: 6.2, priority: 'MEDIUM' },
  ]

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <h2 className="text-xl font-semibold">Maintenance Priority List</h2>
        <p className="text-sm text-gray-600 mt-1">Road segments ranked by urgency</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rank</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Road Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Defects</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Severity</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {priorityList.map((item, idx) => (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  #{idx + 1}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {item.road}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {item.defects}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {item.avgSeverity.toFixed(1)}/10
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                    item.priority === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                    item.priority === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {item.priority}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <button className="text-blue-600 hover:text-blue-800">View Details</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default PriorityPage

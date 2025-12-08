const SettingsPage = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-6">Settings</h2>
        
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium mb-3">API Configuration</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Detection Service URL
                </label>
                <input
                  type="text"
                  defaultValue="http://localhost:8001"
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Severity Service URL
                </label>
                <input
                  type="text"
                  defaultValue="http://localhost:8002"
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-medium mb-3">Detection Settings</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Confidence Threshold
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  defaultValue="70"
                  className="w-full"
                />
                <span className="text-sm text-gray-600">70%</span>
              </div>
            </div>
          </div>

          <div className="pt-4">
            <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              Save Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import MapPage from './pages/MapPage'
import UploadPage from './pages/UploadPage'
import AnalyticsPage from './pages/AnalyticsPage'
import PriorityPage from './pages/PriorityPage'
import ExportPage from './pages/ExportPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/priority" element={<PriorityPage />} />
          <Route path="/export" element={<ExportPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App

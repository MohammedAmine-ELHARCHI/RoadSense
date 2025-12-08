import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Home, Map, Upload, BarChart3, ListOrdered, 
  Download, Settings, Menu, X 
} from 'lucide-react'

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const location = useLocation()

  const navigation = [
    { name: 'Overview', href: '/', icon: Home },
    { name: 'Map View', href: '/map', icon: Map },
    { name: 'Upload', href: '/upload', icon: Upload },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'Priority', href: '/priority', icon: ListOrdered },
    { name: 'Export', href: '/export', icon: Download },
    { name: 'Settings', href: '/settings', icon: Settings },
  ]

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-gray-900 text-white transition-all duration-300`}>
        <div className="flex items-center justify-between p-4">
          {sidebarOpen && <h1 className="text-xl font-bold">RoadSense</h1>}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg hover:bg-gray-800"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        <nav className="mt-8">
          {navigation.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.href
            
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center px-4 py-3 ${
                  isActive 
                    ? 'bg-blue-600 border-r-4 border-blue-400' 
                    : 'hover:bg-gray-800'
                } transition-colors`}
              >
                <Icon size={20} />
                {sidebarOpen && <span className="ml-3">{item.name}</span>}
              </Link>
            )
          })}
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm z-10">
          <div className="flex items-center justify-between p-4">
            <h2 className="text-2xl font-bold text-gray-800">
              {navigation.find(item => item.href === location.pathname)?.name || 'RoadSense Dashboard'}
            </h2>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                <span className="text-sm text-gray-600">Services Online</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}

export default Layout

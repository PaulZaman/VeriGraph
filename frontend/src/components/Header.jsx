import { Link } from 'react-router-dom'
import { Search } from 'lucide-react'

function Header() {
  // Determine environment based on API URL
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  let environment = 'dev'
  
  if (apiUrl.includes('verigraph-api.fly.dev')) {
    environment = 'prod'
  } else if (apiUrl.includes('verigraph-api-staging.fly.dev')) {
    environment = 'staging'
  }

  // Environment badge styles
  const envStyles = {
    dev: 'bg-green-100 text-green-700 border-green-300',
    staging: 'bg-yellow-100 text-yellow-700 border-yellow-300',
    prod: 'bg-blue-100 text-blue-700 border-blue-300'
  }

  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2 hover:opacity-80 transition-opacity">
            <Search className="w-6 h-6 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">VeriGraph</h1>
            <span className={`px-2 py-1 text-xs font-semibold rounded-md border ${envStyles[environment]}`}>
              {environment.toUpperCase()}
            </span>
          </Link>
          <nav className="hidden md:flex space-x-6">
            <Link to="/how-it-works" className="text-gray-600 hover:text-gray-900">How It Works</Link>
            <Link to="/about" className="text-gray-600 hover:text-gray-900">About</Link>
            <Link to="/data" className="text-gray-600 hover:text-gray-900">Data</Link>
          </nav>
        </div>
      </div>
    </header>
  )
}

export default Header

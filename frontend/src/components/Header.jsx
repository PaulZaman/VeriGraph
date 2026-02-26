import { Link } from 'react-router-dom'
import { Search } from 'lucide-react'

function Header() {
  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2 hover:opacity-80 transition-opacity">
            <Search className="w-6 h-6 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">VeriGraph</h1>
          </Link>
          <nav className="hidden md:flex space-x-6">
            <Link to="/how-it-works" className="text-gray-600 hover:text-gray-900">How It Works</Link>
            <Link to="/about" className="text-gray-600 hover:text-gray-900">About</Link>
          </nav>
        </div>
      </div>
    </header>
  )
}

export default Header

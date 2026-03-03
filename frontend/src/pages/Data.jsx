import { useState, useEffect, useCallback } from 'react'
import { Database, Search, FileText, Loader2, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react'
import Header from '../components/Header'

function Data() {
  const [modelInfo, setModelInfo] = useState(null)
  const [trainingData, setTrainingData] = useState([])
  const [stats, setStats] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [totalItems, setTotalItems] = useState(0)
  const itemsPerPage = 20

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  // Fetch current model data on mount
  useEffect(() => {
    fetchCurrentModelData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const fetchCurrentModelData = useCallback(async (page = 1) => {
    setLoading(true)
    setError(null)
    try {
      const offset = (page - 1) * itemsPerPage
      const response = await fetch(`${API_URL}/data?offset=${offset}&limit=${itemsPerPage}`)
      const result = await response.json()
      
      if (result.status === 'success') {
        setModelInfo(result.model_info)
        setTrainingData(result.data || [])
        setStats(result.stats)
        setTotalItems(result.pagination?.total || 0)
        setCurrentPage(page)
      } else {
        setError(result.error || 'Failed to load model data')
      }
    } catch (err) {
      console.error('Error fetching current model data:', err)
      setError('Failed to connect to API')
    } finally {
      setLoading(false)
    }
  }, [API_URL, itemsPerPage])

  const handleSearch = async (page = 1) => {
    if (!searchQuery.trim()) {
      // If search is cleared, fetch regular data
      setIsSearching(false)
      fetchCurrentModelData(page)
      return
    }

    setLoading(true)
    setIsSearching(true)
    setError(null)
    try {
      const offset = (page - 1) * itemsPerPage
      const response = await fetch(
        `${API_URL}/data/search?q=${encodeURIComponent(searchQuery)}&offset=${offset}&limit=${itemsPerPage}`
      )
      const result = await response.json()
      
      if (result.status === 'success') {
        setTrainingData(result.data || [])
        setTotalItems(result.pagination?.total || 0)
        setCurrentPage(page)
      } else {
        setError(result.error || 'Search failed')
      }
    } catch (err) {
      console.error('Error searching:', err)
      setError('Failed to connect to API')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Database className="w-8 h-8 text-blue-600" />
            Training Data Viewer
          </h1>
          <p className="mt-2 text-gray-600">
            View training data for the currently active model
          </p>
        </div>

        {error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
            <p className="text-red-700 font-medium">{error}</p>
            <button 
              onClick={fetchCurrentModelData}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        ) : loading && !modelInfo ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-gray-600">Loading model data...</p>
          </div>
        ) : !modelInfo ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <Database className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No model data available</p>
          </div>
        ) : (
          <>
            {/* Model Info Header */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-gray-600">Model Name</div>
                  <div className="text-sm font-semibold mt-1">{modelInfo.model_name}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Version</div>
                  <div className="text-sm font-semibold mt-1">v{modelInfo.version}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Stage</div>
                  <div className="mt-1">
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      modelInfo.stage === 'Production' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {modelInfo.stage}
                    </span>
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Training Samples</div>
                  <div className="text-sm font-semibold mt-1">{stats?.total_samples || 0}</div>
                </div>
              </div>
            </div>

            {/* Data Display */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="p-6">
                <div className="space-y-4">
                    {/* Search Bar */}
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleSearch(1)
                          }
                        }}
                        placeholder="Search claims..."
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <button
                        onClick={() => handleSearch(1)}
                        disabled={loading || !searchQuery.trim()}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                      >
                        {loading ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Search className="w-4 h-4" />
                        )}
                        Search
                      </button>
                      {isSearching && (
                        <button
                          onClick={() => {
                            setSearchQuery('')
                            setIsSearching(false)
                            fetchCurrentModelData(1)
                          }}
                          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                        >
                          Clear
                        </button>
                      )}
                    </div>

                    {isSearching && (
                      <div className="text-sm text-gray-600">
                        Search results for: <span className="font-semibold">"{searchQuery}"</span>
                      </div>
                    )}

                    {loading ? (
                      <div className="text-center py-8">
                        <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto" />
                      </div>
                    ) : trainingData.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                        <p>No training data found</p>
                      </div>
                    ) : (
                      <>
                        <div className="space-y-2">
                          {trainingData.map((item) => (
                            <div key={item.id} className="border border-gray-200 rounded-lg p-3 hover:shadow-sm transition-shadow">
                              <div className="flex justify-between items-start mb-1">
                                <p className="text-sm text-gray-900 flex-1">{item.claim}</p>
                                <span className="text-xs text-gray-400 ml-2">#{item.id}</span>
                              </div>
                              {item.evidence && item.evidence.length > 0 && (
                                <div className="mt-2 pt-2 border-t border-gray-100">
                                  <div className="text-xs font-medium text-gray-600 mb-1">Evidence:</div>
                                  <div className="space-y-1">
                                    {item.evidence.map((ev, idx) => (
                                      <div key={idx} className="text-xs text-gray-500 bg-gray-50 p-1.5 rounded">
                                        {ev}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>

                        {/* Pagination Controls */}
                        {totalItems > 0 && (
                          <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                            <div className="text-sm text-gray-600">
                              Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, totalItems)} of {totalItems.toLocaleString()} {isSearching ? 'results' : 'items'}
                            </div>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => isSearching ? handleSearch(currentPage - 1) : fetchCurrentModelData(currentPage - 1)}
                                disabled={currentPage === 1 || loading}
                                className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
                              >
                                <ChevronLeft className="w-4 h-4" />
                                Previous
                              </button>
                              <div className="text-sm text-gray-600">
                                Page {currentPage} of {Math.ceil(totalItems / itemsPerPage)}
                              </div>
                              <button
                                onClick={() => isSearching ? handleSearch(currentPage + 1) : fetchCurrentModelData(currentPage + 1)}
                                disabled={currentPage >= Math.ceil(totalItems / itemsPerPage) || loading}
                                className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
                              >
                                Next
                                <ChevronRight className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default Data

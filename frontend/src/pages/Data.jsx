import { useState, useEffect } from 'react'
import { Database, Search, FileText, BarChart3, Download, RefreshCw } from 'lucide-react'
import Header from '../components/Header'

function Data() {
  const [files, setFiles] = useState([])
  const [stats, setStats] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [selectedEntity, setSelectedEntity] = useState(null)
  const [loading, setLoading] = useState(false)
  const [dataLoaded, setDataLoaded] = useState(false)
  const [loadingData, setLoadingData] = useState(false)

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  // Fetch available files on mount
  useEffect(() => {
    fetchFiles()
    fetchStats()
  }, [])

  const fetchFiles = async () => {
    try {
      const response = await fetch(`${API_URL}/data/files`)
      const data = await response.json()
      if (data.status === 'success') {
        setFiles(data.files)
      }
    } catch (error) {
      console.error('Error fetching files:', error)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_URL}/data/stats`)
      const data = await response.json()
      if (data.status === 'success') {
        setStats(data.data)
        setDataLoaded(data.data.loaded || false)
      }
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const handleLoadData = async (filename = null) => {
    setLoadingData(true)
    try {
      const url = filename 
        ? `${API_URL}/data/load?filename=${encodeURIComponent(filename)}`
        : `${API_URL}/data/load`
      
      const response = await fetch(url, { method: 'POST' })
      const data = await response.json()
      
      if (data.status === 'success') {
        setStats(data.stats)
        setDataLoaded(true)
        alert(`✅ Loaded ${data.stats.triples} triples successfully!`)
      } else {
        alert(`❌ Failed to load data: ${data.message}`)
      }
    } catch (error) {
      console.error('Error loading data:', error)
      alert('❌ Error loading data')
    } finally {
      setLoadingData(false)
    }
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!searchQuery.trim()) return

    setLoading(true)
    setSearchResults([])
    setSelectedEntity(null)

    try {
      const response = await fetch(`${API_URL}/data/search?q=${encodeURIComponent(searchQuery)}&limit=20`)
      const data = await response.json()
      
      if (data.status === 'success') {
        setSearchResults(data.results)
      } else if (data.status === 'error') {
        alert(data.message)
      }
    } catch (error) {
      console.error('Error searching:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSelectEntity = async (entityUri) => {
    const entityName = entityUri.split('/').pop()
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/data/entity/${encodeURIComponent(entityName)}`)
      const data = await response.json()
      
      if (data.status === 'success') {
        setSelectedEntity(data.entity)
      } else {
        alert('Entity not found')
      }
    } catch (error) {
      console.error('Error fetching entity:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-5xl font-bold text-gray-900 mb-4 flex items-center justify-center gap-3">
            <Database className="w-12 h-12 text-blue-600" />
            Data Viewer
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Explore DBpedia knowledge graph data used for fact-checking
          </p>
        </div>

        {/* Stats Card */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <BarChart3 className="w-6 h-6" />
              Data Statistics
            </h3>
            <button
              onClick={fetchStats}
              className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              title="Refresh stats"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>

          {stats ? (
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center p-4 bg-blue-50 rounded-xl">
                <div className="text-3xl font-bold text-blue-600">{stats.loaded ? 'Loaded' : 'Not Loaded'}</div>
                <div className="text-sm text-gray-600 mt-1">Status</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-xl">
                <div className="text-3xl font-bold text-green-600">{stats.triples?.toLocaleString() || 0}</div>
                <div className="text-sm text-gray-600 mt-1">Triples</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-xl">
                <div className="text-3xl font-bold text-purple-600">{stats.entities?.toLocaleString() || 0}</div>
                <div className="text-sm text-gray-600 mt-1">Entities</div>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500">Loading stats...</div>
          )}

          {!dataLoaded && (
            <div className="mt-6 text-center">
              <button
                onClick={() => handleLoadData()}
                disabled={loadingData}
                className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {loadingData ? (
                  <>
                    <RefreshCw className="inline w-5 h-5 mr-2 animate-spin" />
                    Loading Data...
                  </>
                ) : (
                  <>
                    <Download className="inline w-5 h-5 mr-2" />
                    Load Data Into Memory
                  </>
                )}
              </button>
              <p className="text-sm text-gray-500 mt-2">
                This will load RDF data from DVC storage. May take a few minutes.
              </p>
            </div>
          )}
        </div>

        {/* Available Files */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <FileText className="w-6 h-6" />
            Available Data Files
          </h3>

          {files.length > 0 ? (
            <div className="space-y-3">
              {files.map((file, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div>
                    <div className="font-semibold text-gray-900">{file.name}</div>
                    <div className="text-sm text-gray-600">{file.size_mb} MB  • {file.type}</div>
                  </div>
                  <button
                    onClick={() => handleLoadData(file.name)}
                    disabled={loadingData}
                    className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400"
                  >
                    Load
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              No data files found. Make sure DVC is configured and run <code className="bg-gray-100 px-2 py-1 rounded">dvc pull</code>
            </div>
          )}
        </div>

        {/* Search Section */}
        {dataLoaded && (
          <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
              <Search className="w-6 h-6" />
              Search Entities
            </h3>

            <form onSubmit={handleSearch} className="mb-6">
              <div className="flex gap-4">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search for entities (e.g., Paris, Albert_Einstein)..."
                  className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
                />
                <button
                  type="submit"
                  disabled={loading || !searchQuery.trim()}
                  className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {loading ? 'Searching...' : 'Search'}
                </button>
              </div>
            </form>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-semibold text-gray-700 mb-3">Search Results ({searchResults.length})</h4>
                {searchResults.map((result, index) => (
                  <div
                    key={index}
                    onClick={() => handleSelectEntity(result.uri)}
                    className="p-4 bg-blue-50 rounded-lg hover:bg-blue-100 cursor-pointer transition-colors"
                  >
                    <div className="font-semibold text-blue-900">{result.label}</div>
                    <div className="text-sm text-blue-600 truncate">{result.uri}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Selected Entity Details */}
            {selectedEntity && (
              <div className="mt-8 p-6 bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl">
                <h4 className="text-xl font-bold text-gray-900 mb-4">Entity Details</h4>
                
                <div className="mb-4">
                  <div className="text-sm text-gray-600">Label</div>
                  <div className="text-lg font-semibold text-gray-900">{selectedEntity.label || 'No label'}</div>
                </div>

                <div className="mb-4">
                  <div className="text-sm text-gray-600">URI</div>
                  <a href={selectedEntity.uri} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline break-all">
                    {selectedEntity.uri}
                  </a>
                </div>

                {selectedEntity.types && selectedEntity.types.length > 0 && (
                  <div className="mb-4">
                    <div className="text-sm text-gray-600 mb-2">Types</div>
                    <div className="flex flex-wrap gap-2">
                      {selectedEntity.types.map((type, i) => (
                        <span key={i} className="px-3 py-1 bg-purple-100 text-purple-700 text-sm rounded-full">
                          {type.split('/').pop().replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {selectedEntity.properties && selectedEntity.properties.length > 0 && (
                  <div>
                    <div className="text-sm text-gray-600 mb-2">Properties ({selectedEntity.properties.length})</div>
                    <div className="max-h-96 overflow-y-auto space-y-2">
                      {selectedEntity.properties.map((prop, i) => (
                        <div key={i} className="p-3 bg-white rounded-lg">
                          <div className="text-sm font-semibold text-gray-700 truncate">
                            {prop.predicate.split('/').pop().replace(/_/g, ' ')}
                          </div>
                          <div className="text-sm text-gray-600 break-all">
                            {prop.object}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default Data

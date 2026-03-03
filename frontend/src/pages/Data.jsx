import { useState, useEffect, useCallback } from 'react'
import { Database, Search, FileText, Loader2, AlertCircle, Network } from 'lucide-react'
import { ReactFlow, Background, Controls, MiniMap, useNodesState, useEdgesState } from 'reactflow'
import 'reactflow/dist/style.css'
import Header from '../components/Header'

function Data() {
  const [modelInfo, setModelInfo] = useState(null)
  const [trainingData, setTrainingData] = useState([])
  const [stats, setStats] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('data')

  // Graph state
  const [graphEntity, setGraphEntity] = useState('')
  const [graphLoading, setGraphLoading] = useState(false)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [contextMenu, setContextMenu] = useState(null)

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  // Close context menu on click outside
  useEffect(() => {
    const handleClick = () => setContextMenu(null)
    if (contextMenu) {
      document.addEventListener('click', handleClick)
      return () => document.removeEventListener('click', handleClick)
    }
  }, [contextMenu])

  // Fetch current model data on mount
  useEffect(() => {
    fetchCurrentModelData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const fetchCurrentModelData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_URL}/data`)
      const result = await response.json()
      
      if (result.status === 'success') {
        setModelInfo(result.model_info)
        setTrainingData(result.data || [])
        setStats(result.stats)
      } else {
        setError(result.error || 'Failed to load model data')
      }
    } catch (err) {
      console.error('Error fetching current model data:', err)
      setError('Failed to connect to API')
    } finally {
      setLoading(false)
    }
  }, [API_URL])

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!searchQuery.trim() || !modelInfo) return

    setLoading(true)
    try {
      const response = await fetch(
        `${API_URL}/data/model/${modelInfo.model_id}/search?q=${encodeURIComponent(searchQuery)}&limit=50`
      )
      const data = await response.json()
      
      if (data.status === 'success') {
        setSearchResults(data.results)
        setActiveTab('search')
      }
    } catch (error) {
      console.error('Error searching:', error)
    } finally {
      setLoading(false)
    }
  }

  // Radial layout that spreads nodes across the viewport
  const getLayoutedElements = (nodes, edges) => {
    const centerX = 500
    const centerY = 300
    const baseRadius = 250
    
    // Find center node
    const centerNode = nodes.find(n => n.data.label && 
      n.style?.background === '#3b82f6')
    
    // Separate center from other nodes
    const otherNodes = nodes.filter(n => n.id !== centerNode?.id)
    
    const layoutedNodes = nodes.map((node) => {
      if (node.id === centerNode?.id) {
        // Place center node in the middle
        return {
          ...node,
          position: {
            x: centerX,
            y: centerY
          }
        }
      } else {
        // Arrange other nodes in a circle around center
        const nodeIndex = otherNodes.findIndex(n => n.id === node.id)
        const angle = (nodeIndex / otherNodes.length) * 2 * Math.PI
        
        // Add some variation to radius for visual interest
        const radiusVariation = (nodeIndex % 3) * 50
        const radius = baseRadius + radiusVariation
        
        return {
          ...node,
          position: {
            x: centerX + Math.cos(angle) * radius,
            y: centerY + Math.sin(angle) * radius
          }
        }
      }
    })

    return { nodes: layoutedNodes, edges }
  }

  const handleNodeContextMenu = useCallback((event, node) => {
    event.preventDefault()
    setContextMenu({
      x: event.clientX,
      y: event.clientY,
      node
    })
  }, [])

  const handleGraphSearch = useCallback(async (e, entityOverride = null) => {
    if (e) e.preventDefault()
    const searchEntity = entityOverride || graphEntity
    if (!searchEntity.trim()) return

    setGraphLoading(true)
    setContextMenu(null)
    try {
      const response = await fetch(
        `${API_URL}/graph/entity/${encodeURIComponent(searchEntity)}?depth=1`
      )
      const data = await response.json()
      
      if (data.status === 'success') {
        // Convert nodes to React Flow format
        const flowNodes = data.nodes.map((node) => {
          const isCenter = node.type === 'center'
          return {
            id: node.id,
            data: { label: node.label },
            position: { x: 0, y: 0 }, // Will be set by layout
            style: {
              background: isCenter ? '#3b82f6' : '#e5e7eb',
              color: isCenter ? '#fff' : '#000',
              border: '2px solid #6366f1',
              borderRadius: '8px',
              padding: '10px',
              fontSize: '12px',
              width: '180px',
              textAlign: 'center'
            }
          }
        })

        // Convert edges to React Flow format
        const flowEdges = data.edges.map((edge, index) => ({
          id: `${edge.source}-${edge.target}-${index}`,
          source: edge.source,
          target: edge.target,
          label: edge.label,
          type: 'smoothstep',
          animated: true,
          style: { stroke: '#6366f1' },
          labelStyle: { fontSize: '10px', fill: '#666' }
        }))

        // Apply radial layout around center node
        const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
          flowNodes,
          flowEdges
        )

        setNodes(layoutedNodes)
        setEdges(layoutedEdges)
      }
    } catch (error) {
      console.error('Error fetching graph:', error)
    } finally {
      setGraphLoading(false)
    }
  }, [API_URL, graphEntity, setNodes, setEdges])

  const handleContextMenuSearch = useCallback(() => {
    if (contextMenu?.node) {
      const label = contextMenu.node.data.label
      setGraphEntity(label)
      setContextMenu(null)
      // Trigger search
      setTimeout(() => {
        handleGraphSearch(null, label)
      }, 100)
    }
  }, [contextMenu, handleGraphSearch])

  const getLabelColor = (label) => {
    switch (label?.toUpperCase()) {
      case 'SUPPORTED': return 'bg-green-100 text-green-800'
      case 'REFUTED': return 'bg-red-100 text-red-800'
      case 'NOT ENOUGH INFO': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
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

            {/* Tabs */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="border-b border-gray-200">
                <div className="flex">
                  <button
                    onClick={() => setActiveTab('data')}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'data'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <FileText className="w-4 h-4 inline mr-2" />
                    Data ({trainingData.length})
                  </button>
                  <button
                    onClick={() => setActiveTab('search')}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'search'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <Search className="w-4 h-4 inline mr-2" />
                    Search
                  </button>
                  <button
                    onClick={() => setActiveTab('graph')}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'graph'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <Network className="w-4 h-4 inline mr-2" />
                    Graph
                  </button>
                </div>
              </div>

              <div className="p-6">
                {/* Data Tab */}
                {activeTab === 'data' && (
                  <div className="space-y-4">
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
                      <div className="space-y-4">
                        {trainingData.map((item) => (
                          <div key={item.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                            <div className="flex justify-between items-start mb-2">
                              <span className={`text-xs px-2 py-1 rounded ${getLabelColor(item.label)}`}>
                                {item.label}
                              </span>
                              <span className="text-xs text-gray-500">ID: {item.id}</span>
                            </div>
                            <p className="text-sm text-gray-900 mb-3">{item.claim}</p>
                            {item.evidence && item.evidence.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-gray-200">
                                <div className="text-xs font-semibold text-gray-700 mb-2">Evidence:</div>
                                <div className="space-y-2">
                                  {item.evidence.map((ev, idx) => (
                                    <div key={idx} className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                                      {ev}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Search Tab */}
                {activeTab === 'search' && (
                  <div className="space-y-4">
                    <form onSubmit={handleSearch} className="flex gap-2">
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search claims..."
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <button
                        type="submit"
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
                    </form>

                    {searchResults.length > 0 ? (
                      <div className="space-y-4">
                        <div className="text-sm text-gray-600">
                          Found {searchResults.length} results
                        </div>
                        {searchResults.map((item) => (
                          <div key={item.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                            <div className="flex justify-between items-start mb-2">
                              <span className={`text-xs px-2 py-1 rounded ${getLabelColor(item.label)}`}>
                                {item.label}
                              </span>
                              <span className="text-xs text-gray-500">ID: {item.id}</span>
                            </div>
                            <p className="text-sm text-gray-900 mb-3">{item.claim}</p>
                            {item.evidence && item.evidence.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-gray-200">
                                <div className="text-xs font-semibold text-gray-700 mb-2">Evidence:</div>
                                <div className="space-y-2">
                                  {item.evidence.map((ev, idx) => (
                                    <div key={idx} className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                                      {ev}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : searchQuery && !loading ? (
                      <div className="text-center py-8 text-gray-500">
                        <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                        <p>No results found for "{searchQuery}"</p>
                      </div>
                    ) : null}
                  </div>
                )}

                {/* Graph Tab */}
                {activeTab === 'graph' && (
                  <div className="space-y-4">
                    <form onSubmit={handleGraphSearch} className="flex gap-2">
                      <input
                        type="text"
                        value={graphEntity}
                        onChange={(e) => setGraphEntity(e.target.value)}
                        placeholder="Search entity (e.g., Paris, France, Barack_Obama)..."
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <button
                        type="submit"
                        disabled={graphLoading || !graphEntity.trim()}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                      >
                        {graphLoading ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Network className="w-4 h-4" />
                        )}
                        Load Graph
                      </button>
                    </form>

                    {nodes.length > 0 ? (
                      <div className="h-[600px] border border-gray-200 rounded-lg bg-gray-50">
                        <ReactFlow
                          nodes={nodes}
                          edges={edges}
                          onNodesChange={onNodesChange}
                          onEdgesChange={onEdgesChange}
                          onNodeContextMenu={handleNodeContextMenu}
                          onPaneClick={() => setContextMenu(null)}
                          fitView
                          attributionPosition="bottom-left"
                        >
                          <Background />
                          <Controls />
                          <MiniMap />
                        </ReactFlow>
                        
                        {/* Context Menu */}
                        {contextMenu && (
                          <div
                            style={{
                              position: 'fixed',
                              top: contextMenu.y,
                              left: contextMenu.x,
                              zIndex: 1000
                            }}
                            className="bg-white border border-gray-300 rounded-lg shadow-lg py-1 min-w-[180px]"
                          >
                            <button
                              onClick={handleContextMenuSearch}
                              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
                            >
                              <Search className="w-4 h-4" />
                              Search for "{contextMenu.node?.data?.label}"
                            </button>
                          </div>
                        )}
                      </div>
                    ) : graphEntity && !graphLoading ? (
                      <div className="text-center py-12 text-gray-500">
                        <Network className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                        <p>No graph data found for "{graphEntity}"</p>
                        <p className="text-sm mt-2">Try searching for entities like "Paris", "France", or "Barack_Obama"</p>
                      </div>
                    ) : (
                      <div className="text-center py-12 text-gray-500">
                        <Network className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                        <p>Search for an entity to visualize its DBpedia knowledge graph</p>
                        <p className="text-sm mt-2">Try entities like "Paris", "France", "Albert_Einstein"</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default Data

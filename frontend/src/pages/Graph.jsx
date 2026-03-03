import { useState, useEffect, useCallback } from 'react'
import { Network, Search, Loader2 } from 'lucide-react'
import { ReactFlow, ReactFlowProvider, Background, Controls, MiniMap, useNodesState, useEdgesState, useReactFlow } from 'reactflow'
import 'reactflow/dist/style.css'
import Header from '../components/Header'

function GraphFlow({ nodes, edges, onNodesChange, onEdgesChange, handleNodeContextMenu, setContextMenu, contextMenu, handleContextMenuSearch }) {
  const reactFlowInstance = useReactFlow()

  // Auto-fit view when nodes are loaded
  useEffect(() => {
    if (nodes.length > 0) {
      setTimeout(() => {
        reactFlowInstance.fitView({ padding: 0.2, duration: 400 })
      }, 50)
    }
  }, [nodes, reactFlowInstance])

  return (
    <>
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
    </>
  )
}

function Graph() {
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

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Network className="w-8 h-8 text-blue-600" />
            Knowledge Graph Explorer
          </h1>
          <p className="mt-2 text-gray-600">
            Visualize entity relationships from DBpedia knowledge graph
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
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
                <ReactFlowProvider>
                  <GraphFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    handleNodeContextMenu={handleNodeContextMenu}
                    setContextMenu={setContextMenu}
                    contextMenu={contextMenu}
                    handleContextMenuSearch={handleContextMenuSearch}
                  />
                </ReactFlowProvider>
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
        </div>
      </div>
    </div>
  )
}

export default Graph

import { useState, useEffect, useRef } from 'react'
import { CheckCircle, XCircle, HelpCircle, Shield, Globe, Brain, Zap, Database, Link2, Search } from 'lucide-react'
import Header from '../components/Header'
import ResultCard from '../components/ResultCard'

function Landing() {
  const [searchQuery, setSearchQuery] = useState('')
  const [apiStatus, setApiStatus] = useState('')
  const [apiConnected, setApiConnected] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [taskId, setTaskId] = useState(null)
  const pollingIntervalRef = useRef(null)

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }
  }, [])

  // Poll for task status
  const pollTaskStatus = async (id) => {
    try {
      const response = await fetch(`${API_URL}/verify/${id}`)
      
      if (response.ok) {
        const data = await response.json()
        setResult(data)
        
        // Stop polling if task is completed or failed
        if (data.status === 'completed' || data.status === 'failed') {
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current)
            pollingIntervalRef.current = null
          }
          setLoading(false)
        }
      }
    } catch (error) {
      console.error('Polling error:', error)
    }
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    setLoading(true)
    setApiStatus('')
    setResult(null)
    setTaskId(null)
    
    // Clear any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
    
    try {
      const response = await fetch(`${API_URL}/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ claim: searchQuery }),
      })
      
      if (response.ok) {
        setApiStatus('api connected')
        setApiConnected(true)
        const data = await response.json()
        
        console.log('Task created:', data)
        
        if (data.task_id) {
          setTaskId(data.task_id)
          
          // Set result to pending state
          setResult({
            status: 'pending',
            task_id: data.task_id,
            claim: searchQuery
          })
          
          // Start polling every 1 second
          pollingIntervalRef.current = setInterval(() => {
            pollTaskStatus(data.task_id)
          }, 1000)
          
          // Do first poll immediately
          pollTaskStatus(data.task_id)
        }
      } else {
        setApiStatus('api disconnected')
        setApiConnected(false)
        setResult(null)
        setLoading(false)
      }
    } catch (error) {
      console.error('API Error:', error)
      setApiStatus('api disconnected')
      setApiConnected(false)
      setResult(null)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Header />

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h2 className="text-5xl font-bold text-gray-900 mb-4">
            AI-Powered Fact Verification
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Using a BERT-based GAN discriminator trained on 1.5M knowledge graph triplets to verify claims in 1-2 seconds.
          </p>
        </div>

        {/* Search Bar */}
        <div className="max-w-4xl mx-auto mb-16">
          <form onSubmit={handleSearch} className="relative">
            <div className="flex items-center bg-white rounded-full shadow-lg border-2 border-gray-200 focus-within:border-blue-500 transition-colors">
              <Search className="ml-6 text-gray-400 w-6 h-6" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter a claim to fact-check..."
                className="flex-1 px-6 py-5 text-lg rounded-full focus:outline-none"
              />
              <button
                type="submit"
                disabled={loading}
                className="mr-2 px-8 py-3 bg-blue-600 text-white font-semibold rounded-full hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {loading ? 'Verifying...' : 'Verify'}
              </button>
            </div>
          </form>
          <p className="text-center text-sm text-gray-500 mt-3">
            Example: "The Eiffel Tower is located in Paris, France"
          </p>
        </div>

        {/* Result Display */}
        {result && (
          <ResultCard result={result} claim={searchQuery} />
        )}

        {/* How It Works Section */}
        <div id="how-it-works" className="mb-16 mt-16">
          <div className="bg-white rounded-2xl shadow-lg p-8 md:p-12">
            <h3 className="text-3xl font-bold text-gray-900 mb-6 text-center">How It Works</h3>
            <div className="prose prose-lg max-w-none text-gray-600">
              <p className="text-center mb-8">
                When you enter a claim, the system extracts key triplets (subject, relation, object) using spaCy, 
                then runs them through a BERT-GAN discriminator trained to distinguish factual from fabricated statements. 
                The model learned factual patterns from 1.5M DBpedia triplets and returns a verdict with confidence score — all in ~1.2 seconds.
              </p>
              
              <div className="grid md:grid-cols-3 gap-6 mt-8">
                <div className="text-center p-6 bg-green-50 rounded-xl">
                  <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-600" />
                  <h4 className="font-bold text-green-800 mb-2">SUPPORTED</h4>
                  <p className="text-sm text-gray-600">GAN score ≥ 0.7 — High confidence it's true</p>
                </div>
                <div className="text-center p-6 bg-red-50 rounded-xl">
                  <XCircle className="w-12 h-12 mx-auto mb-3 text-red-600" />
                  <h4 className="font-bold text-red-800 mb-2">REFUTED</h4>
                  <p className="text-sm text-gray-600">GAN score ≤ 0.3 — High confidence it's false</p>
                </div>
                <div className="text-center p-6 bg-yellow-50 rounded-xl">
                  <HelpCircle className="w-12 h-12 mx-auto mb-3 text-yellow-600" />
                  <h4 className="font-bold text-yellow-800 mb-2">NOT ENOUGH INFO</h4>
                  <p className="text-sm text-gray-600">GAN score 0.3-0.7 — Model uncertain</p>
                </div>
              </div>

              <p className="text-center mt-8 text-gray-700">
                The result is a clear verdict along with a <span className="font-semibold">confidence score</span>.
              </p>
            </div>
          </div>
        </div>

        {/* About Section */}
        <div id="about" className="mb-16">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl shadow-lg p-8 md:p-12 text-white">
            <h3 className="text-3xl font-bold mb-6 text-center">Why VeriGraph?</h3>
            <p className="text-lg text-center max-w-4xl mx-auto leading-relaxed">
              Trained on 1.5M DBpedia knowledge graph triplets, our <span className="font-semibold">BERT-GAN discriminator</span> learned 
              factual patterns to distinguish real from fabricated claims. With <span className="font-semibold">81% accuracy</span> and 
              <span className="font-semibold"> 1.2s inference</span>, it delivers fast, reliable fact-checking — 10x-25x faster than 
              traditional systems with comparable accuracy.
            </p>
            <div className="grid md:grid-cols-3 gap-6 mt-10">
              <div className="text-center">
                <Zap className="w-12 h-12 mx-auto mb-2" />
                <h4 className="font-bold mb-2">Lightning Fast</h4>
                <p className="text-sm opacity-90">1.2s inference, offline mode</p>
              </div>
              <div className="text-center">
                <Brain className="w-12 h-12 mx-auto mb-2" />
                <h4 className="font-bold mb-2">81% Accuracy</h4>
                <p className="text-sm opacity-90">Trained on 1.5M triplets</p>
              </div>
              <div className="text-center">
                <Shield className="w-12 h-12 mx-auto mb-2" />
                <h4 className="font-bold mb-2">Production Ready</h4>
                <p className="text-sm opacity-90">MLOps with quality gates</p>
              </div>
            </div>
          </div>
        </div>

        {/* Technology Stack */}
        <div className="bg-gray-50 rounded-2xl p-8 md:p-12">
          <h3 className="text-2xl font-bold text-gray-900 mb-6 text-center">Technology Stack</h3>
          <div className="flex flex-wrap justify-center gap-4">
            <span className="px-4 py-2 bg-white rounded-full text-sm font-medium text-gray-700 shadow-sm flex items-center gap-2">
              <Brain className="w-4 h-4" />
              BERT-GAN Discriminator
            </span>
            <span className="px-4 py-2 bg-white rounded-full text-sm font-medium text-gray-700 shadow-sm flex items-center gap-2">
              <Database className="w-4 h-4" />
              110M Parameters
            </span>
            <span className="px-4 py-2 bg-white rounded-full text-sm font-medium text-gray-700 shadow-sm flex items-center gap-2">
              <Zap className="w-4 h-4" />
              SwapGenerator (Adversarial Training)
            </span>
            <span className="px-4 py-2 bg-white rounded-full text-sm font-medium text-gray-700 shadow-sm flex items-center gap-2">
              <Link2 className="w-4 h-4" />
              Trained on DBpedia KG
            </span>
          </div>
          <p className="text-center text-sm text-gray-500 mt-4">
            Optional: Full pipeline with Entity Linking + DBpedia KB verification (91.7% accuracy, 6.8s)
          </p>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <p className="text-gray-400">
              © 2026 VeriGraph. Building trustworthy AI systems through fact verification.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Landing

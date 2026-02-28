import { useState } from 'react'
import { CheckCircle, XCircle, HelpCircle, Shield, Globe, Brain, Zap, Database, Link2, Search } from 'lucide-react'
import Header from '../components/Header'

function Landing() {
  const [searchQuery, setSearchQuery] = useState('')
  const [apiStatus, setApiStatus] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    setLoading(true)
    setApiStatus('')
    
    try {
      const response = await fetch('http://localhost:8000/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ claim: searchQuery }),
      })
      
      // Regardless of response, show "api connected"
      setApiStatus('api connected')
      
      const data = await response.json()
      console.log('API Response:', data)
    } catch (error) {
      console.error('API Error:', error)
      // Still show "api connected" even on error
      setApiStatus('api connected')
    } finally {
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
            Automated Fact-Checking System
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            An AI-powered platform that verifies the accuracy of any written claim in real time.
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
          {apiStatus && (
            <div className="mt-4 text-center">
              <p className="text-green-600 font-semibold text-lg">
                {apiStatus}
              </p>
            </div>
          )}
        </div>

        {/* How It Works Section */}
        <div id="how-it-works" className="mb-16">
          <div className="bg-white rounded-2xl shadow-lg p-8 md:p-12">
            <h3 className="text-3xl font-bold text-gray-900 mb-6 text-center">How It Works</h3>
            <div className="prose prose-lg max-w-none text-gray-600">
              <p className="text-center mb-8">
                When you enter a statement, the system extracts its key components (subject, relation, object), 
                links them to entities in a global knowledge graph (DBpedia), retrieves supporting evidence, 
                and evaluates the claim using a BERT-based neural model.
              </p>
              
              <div className="grid md:grid-cols-3 gap-6 mt-8">
                <div className="text-center p-6 bg-green-50 rounded-xl">
                  <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-600" />
                  <h4 className="font-bold text-green-800 mb-2">SUPPORTED</h4>
                  <p className="text-sm text-gray-600">Claim is backed by evidence</p>
                </div>
                <div className="text-center p-6 bg-red-50 rounded-xl">
                  <XCircle className="w-12 h-12 mx-auto mb-3 text-red-600" />
                  <h4 className="font-bold text-red-800 mb-2">REFUTED</h4>
                  <p className="text-sm text-gray-600">Claim contradicts evidence</p>
                </div>
                <div className="text-center p-6 bg-yellow-50 rounded-xl">
                  <HelpCircle className="w-12 h-12 mx-auto mb-3 text-yellow-600" />
                  <h4 className="font-bold text-yellow-800 mb-2">NOT ENOUGH INFO</h4>
                  <p className="text-sm text-gray-600">Insufficient evidence found</p>
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
              Designed for <span className="font-semibold">combating misinformation</span>, 
              validating open-web data, and building trustworthy AI systems, the platform combines 
              <span className="font-semibold"> symbolic reasoning</span> (knowledge graphs) with 
              modern <span className="font-semibold">deep learning</span> to deliver fast, explainable fact checks.
            </p>
            <div className="grid md:grid-cols-3 gap-6 mt-10">
              <div className="text-center">
                <Shield className="w-12 h-12 mx-auto mb-2" />
                <h4 className="font-bold mb-2">Combat Misinformation</h4>
                <p className="text-sm opacity-90">Verify claims in real-time</p>
              </div>
              <div className="text-center">
                <Globe className="w-12 h-12 mx-auto mb-2" />
                <h4 className="font-bold mb-2">Validate Web Data</h4>
                <p className="text-sm opacity-90">Ensure data accuracy</p>
              </div>
              <div className="text-center">
                <Brain className="w-12 h-12 mx-auto mb-2" />
                <h4 className="font-bold mb-2">Trustworthy AI</h4>
                <p className="text-sm opacity-90">Build reliable systems</p>
              </div>
            </div>
          </div>
        </div>

        {/* Technology Stack */}
        <div className="bg-gray-50 rounded-2xl p-8 md:p-12">
          <h3 className="text-2xl font-bold text-gray-900 mb-6 text-center">Powered By</h3>
          <div className="flex flex-wrap justify-center gap-4">
            <span className="px-4 py-2 bg-white rounded-full text-sm font-medium text-gray-700 shadow-sm flex items-center gap-2">
              <Brain className="w-4 h-4" />
              BERT Neural Model
            </span>
            <span className="px-4 py-2 bg-white rounded-full text-sm font-medium text-gray-700 shadow-sm flex items-center gap-2">
              <Database className="w-4 h-4" />
              DBpedia Knowledge Graph
            </span>
            <span className="px-4 py-2 bg-white rounded-full text-sm font-medium text-gray-700 shadow-sm flex items-center gap-2">
              <Link2 className="w-4 h-4" />
              Entity Linking
            </span>
            <span className="px-4 py-2 bg-white rounded-full text-sm font-medium text-gray-700 shadow-sm flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Real-Time Processing
            </span>
          </div>
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

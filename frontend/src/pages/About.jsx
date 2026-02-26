import { Link } from 'react-router-dom'
import { Search, ArrowLeft, Shield, Globe, Bot, Target, TrendingUp, Users } from 'lucide-react'

import Header from '../components/Header'

function About() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Back Button */}
        <Link to="/" className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-8">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Home
        </Link>

        {/* Title */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">About VeriGraph</h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Building trustworthy AI systems through automated fact verification
          </p>
        </div>

        {/* Mission Statement */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl shadow-lg p-8 md:p-12 text-white mb-16">
          <h2 className="text-3xl font-bold mb-6 text-center">Our Mission</h2>
          <p className="text-lg text-center max-w-4xl mx-auto leading-relaxed mb-8">
            VeriGraph combines <span className="font-semibold">symbolic reasoning</span> through knowledge graphs 
            with modern <span className="font-semibold">deep learning</span> techniques to deliver fast, accurate, 
            and explainable fact-checking at scale. We believe that access to verified information is fundamental 
            to making informed decisions in the digital age.
          </p>
        </div>

        {/* Use Cases */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Why VeriGraph?</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white rounded-xl shadow-lg p-8">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
                <Shield className="w-8 h-8 text-red-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Combat Misinformation</h3>
              <p className="text-gray-600">
                Help journalists, fact-checkers, and citizens identify false claims and misinformation in real-time. 
                VeriGraph provides evidence-based verdicts to counter the spread of fake news.
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-8">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <Globe className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Validate Web Data</h3>
              <p className="text-gray-600">
                Ensure the accuracy of information scraped from the web. Perfect for data aggregation services, 
                research platforms, and content verification systems that need reliable data sources.
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-8">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <Bot className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Trustworthy AI</h3>
              <p className="text-gray-600">
                Build AI systems that can verify their own outputs and reasoning. Integrate VeriGraph into 
                chatbots, virtual assistants, and knowledge systems to enhance reliability and user trust.
              </p>
            </div>
          </div>
        </div>

        {/* Key Features */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Key Features</h2>
          <div className="bg-white rounded-2xl shadow-lg p-8 md:p-12">
            <div className="space-y-8">
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0 w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                  <Target className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">High Accuracy</h3>
                  <p className="text-gray-600">
                    Our BERT-based model achieves state-of-the-art performance on standard fact-checking benchmarks, 
                    trained on millions of verified claims and evidence pairs.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0 w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Explainable Results</h3>
                  <p className="text-gray-600">
                    Unlike black-box systems, VeriGraph shows you the evidence behind each verdict. Understand why 
                    a claim was supported or refuted with clear, traceable reasoning paths.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0 w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <Users className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Open & Transparent</h3>
                  <p className="text-gray-600">
                    Built on open knowledge graphs (DBpedia) and publicly available datasets. We believe in 
                    transparency and reproducibility in AI systems.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Technology Overview */}
        <div className="bg-gray-50 rounded-2xl p-8 md:p-12 mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">Technology Stack</h2>
          <p className="text-gray-600 text-center max-w-3xl mx-auto mb-8">
            VeriGraph leverages cutting-edge technologies in natural language processing, knowledge representation, 
            and machine learning to provide accurate fact verification.
          </p>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg p-6">
              <h4 className="font-bold text-gray-900 mb-3">Natural Language Processing</h4>
              <ul className="space-y-2 text-gray-600">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>BERT transformers for semantic understanding</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Named entity recognition and extraction</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Relation extraction and classification</span>
                </li>
              </ul>
            </div>
            <div className="bg-white rounded-lg p-6">
              <h4 className="font-bold text-gray-900 mb-3">Knowledge Representation</h4>
              <ul className="space-y-2 text-gray-600">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>DBpedia knowledge graph integration</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Entity linking and disambiguation</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Graph-based reasoning and traversal</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center">
          <Link
            to="/"
            className="inline-block px-8 py-4 bg-blue-600 text-white font-semibold rounded-full hover:bg-blue-700 transition-colors shadow-lg"
          >
            Start Fact-Checking
          </Link>
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

export default About

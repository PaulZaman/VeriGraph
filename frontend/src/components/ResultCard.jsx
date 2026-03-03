import { CheckCircle, XCircle, HelpCircle, Clock, AlertCircle } from 'lucide-react'

function ResultCard({ result, claim }) {
  if (!result) return null

  const getVerdictIcon = (verdict) => {
    switch (verdict) {
      case 'SUPPORTED':
      case 'REAL':
        return <CheckCircle className="w-16 h-16 text-green-500" />
      case 'REFUTED':
      case 'FAKE':
        return <XCircle className="w-16 h-16 text-red-500" />
      case 'NOT ENOUGH INFO':
        return <HelpCircle className="w-16 h-16 text-yellow-500" />
      default:
        return <AlertCircle className="w-16 h-16 text-gray-500" />
    }
  }

  const getVerdictColor = (verdict) => {
    switch (verdict) {
      case 'SUPPORTED':
      case 'REAL':
        return 'bg-green-50 border-green-200'
      case 'REFUTED':
      case 'FAKE':
        return 'bg-red-50 border-red-200'
      case 'NOT ENOUGH INFO':
        return 'bg-yellow-50 border-yellow-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  const getVerdictTextColor = (verdict) => {
    switch (verdict) {
      case 'SUPPORTED':
      case 'REAL':
        return 'text-green-800'
      case 'REFUTED':
      case 'FAKE':
        return 'text-red-800'
      case 'NOT ENOUGH INFO':
        return 'text-yellow-800'
      default:
        return 'text-gray-800'
    }
  }

  // Handle pending or processing status
  if (result.status === 'pending' || result.status === 'processing') {
    return (
      <div className="max-w-4xl mx-auto mt-8">
        <div className="bg-blue-50 border-2 border-blue-200 rounded-2xl shadow-lg p-8">
          <div className="flex items-center justify-center mb-4">
            <div className="animate-spin">
              <Clock className="w-16 h-16 text-blue-500" />
            </div>
          </div>
          <h3 className="text-2xl font-bold text-center text-blue-800 mb-2">
            {result.status === 'pending' ? 'Queued for verification...' : 'Analyzing claim...'}
          </h3>
          <p className="text-center text-blue-600">
            Our ML models are processing your claim. This usually takes a few seconds.
          </p>
        </div>
      </div>
    )
  }

  // Handle failed status
  if (result.status === 'failed') {
    return (
      <div className="max-w-4xl mx-auto mt-8">
        <div className="bg-red-50 border-2 border-red-200 rounded-2xl shadow-lg p-8">
          <div className="flex items-center justify-center mb-4">
            <AlertCircle className="w-16 h-16 text-red-500" />
          </div>
          <h3 className="text-2xl font-bold text-center text-red-800 mb-2">
            Verification Failed
          </h3>
          <p className="text-center text-red-600">
            {result.error || 'An error occurred while processing your claim.'}
          </p>
        </div>
      </div>
    )
  }

  // Handle completed status
  if (result.status === 'completed' && result.verdict) {
    const verdict = result.verdict
    const confidence = result.confidence || 0
    const probabilities = result.probabilities || {}

    return (
      <div className="max-w-4xl mx-auto mt-8">
        <div className={`${getVerdictColor(verdict)} border-2 rounded-2xl shadow-lg p-8`}>
          {/* Verdict Icon and Label */}
          <div className="flex items-center justify-center mb-6">
            {getVerdictIcon(verdict)}
          </div>
          
          <h3 className={`text-3xl font-bold text-center ${getVerdictTextColor(verdict)} mb-4`}>
            {verdict}
          </h3>

          {/* Claim Display */}
          <div className="bg-white rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-500 mb-1">Claim analyzed:</p>
            <p className="text-gray-800 font-medium">{claim}</p>
          </div>

          {/* Confidence Score */}
          <div className="bg-white rounded-lg p-6 mb-6">
            <div className="flex justify-between items-center mb-2">
              <span className="text-gray-700 font-semibold">Confidence Score</span>
              <span className={`text-2xl font-bold ${getVerdictTextColor(verdict)}`}>
                {(confidence * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${
                  verdict === 'SUPPORTED' || verdict === 'REAL' ? 'bg-green-500' :
                  verdict === 'REFUTED' || verdict === 'FAKE' ? 'bg-red-500' :
                  'bg-yellow-500'
                }`}
                style={{ width: `${confidence * 100}%` }}
              />
            </div>
          </div>

          {/* Probability Breakdown */}
          {Object.keys(probabilities).length > 0 && (
            <div className="bg-white rounded-lg p-6 mb-6">
              <h4 className="text-gray-700 font-semibold mb-4">Probability Breakdown</h4>
              <div className="space-y-3">
                {Object.entries(probabilities).map(([label, prob]) => (
                  <div key={label}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-gray-600">{label}</span>
                      <span className="text-sm font-semibold text-gray-800">
                        {(prob * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${prob * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Extracted Triplet */}
          {result.triplet && (
            <div className="bg-white rounded-lg p-6 mb-6">
              <h4 className="text-gray-700 font-semibold mb-3">Extracted Knowledge Triplet</h4>
              <div className="flex items-center justify-center gap-3 text-center">
                <div className="flex-1 bg-blue-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 mb-1">Subject</p>
                  <p className="text-sm font-semibold text-blue-900">{result.triplet.subject}</p>
                </div>
                <div className="flex-shrink-0">
                  <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
                <div className="flex-1 bg-purple-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 mb-1">Relation</p>
                  <p className="text-sm font-semibold text-purple-900">{result.triplet.relation}</p>
                </div>
                <div className="flex-shrink-0">
                  <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
                <div className="flex-1 bg-green-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 mb-1">Object</p>
                  <p className="text-sm font-semibold text-green-900">{result.triplet.object}</p>
                </div>
              </div>
              <p className="text-xs text-gray-500 text-center mt-3">
                The claim was analyzed as this knowledge graph triplet
              </p>
            </div>
          )}

          {/* Model Information */}
          {(result.model_name || result.model_version || result.model) && (
            <div className="bg-white rounded-lg p-4">
              <div className="flex items-center justify-between text-xs text-gray-500">
                {result.model_name && (
                  <span className="flex items-center gap-1">
                    <span className="font-semibold">Model:</span>
                    <span>{result.model_name}</span>
                  </span>
                )}
                {result.model_version && (
                  <span className="flex items-center gap-1">
                    <span className="font-semibold">Version:</span>
                    <span>{result.model_version}</span>
                  </span>
                )}
                {result.model && (
                  <span className="flex items-center gap-1">
                    <span className="font-semibold">Environment:</span>
                    <span className="uppercase">{result.model}</span>
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Mode indicator (legacy) */}
          {result.mode && !result.model_name && (
            <div className="mt-4 text-center">
              <span className="text-xs text-gray-500">
                Mode: {result.mode.toUpperCase()}
              </span>
            </div>
          )}
        </div>
      </div>
    )
  }

  return null
}

export default ResultCard

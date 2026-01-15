import { useState } from 'react'
import './App.css'

function App() {
  const [helloResponse, setHelloResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const callHelloApi = async () => {
    setLoading(true)
    setError(null)
    setHelloResponse(null)

    try {
      const response = await fetch('/api/hello')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setHelloResponse(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <h1>ADWS Test App - Frontend</h1>

      <div className="api-section">
        <h2>Backend API Test</h2>
        <button 
          onClick={callHelloApi} 
          disabled={loading}
          className="api-button"
        >
          {loading ? 'Loading...' : 'Call /api/hello'}
        </button>

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {helloResponse && (
          <div className="success-message">
            <strong>Response:</strong>
            <pre>{JSON.stringify(helloResponse, null, 2)}</pre>
          </div>
        )}
      </div>

      <div className="info-section">
        <h2>Endpoints</h2>
        <ul>
          <li><code>GET /api/hello</code> - Returns <code>{"{ \"hello\": \"world\" }"}</code></li>
          <li><code>GET /api/messages</code> - Returns list of messages from MongoDB</li>
        </ul>
      </div>
    </div>
  )
}

export default App

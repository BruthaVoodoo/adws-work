import { useState } from 'react'
import './App.css'
import MessageList from './MessageList'

function App() {
  const [helloResponse, setHelloResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // Message-related state
  const [messages, setMessages] = useState(null)
  const [messagesLoading, setMessagesLoading] = useState(false)
  const [messagesError, setMessagesError] = useState(null)

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

  const callMessagesApi = async () => {
    setMessagesLoading(true)
    setMessagesError(null)
    setMessages(null)

    try {
      console.log('Loading messages from API...')
      const response = await fetch('/api/messages')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      
      // Validate response structure
      if (!data || !Array.isArray(data.messages)) {
        console.error('Invalid API response:', data)
        throw new Error('Invalid response format: expected messages array')
      }
      
      console.log(`Successfully loaded ${data.messages.length} messages`)
      setMessages(data.messages)
    } catch (err) {
      console.error('Error loading messages:', err)
      setMessagesError(err.message)
    } finally {
      setMessagesLoading(false)
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
          aria-label="Test backend API connectivity"
          aria-describedby={error ? "hello-error" : undefined}
        >
          {loading ? 'Loading...' : 'Call /api/hello'}
        </button>

        {error && (
          <div className="error-message" role="alert" id="hello-error">
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

      <div className="api-section">
        <h2>Messages from MongoDB</h2>
        <button 
          onClick={callMessagesApi} 
          disabled={messagesLoading}
          className="api-button"
          aria-label="Load messages from MongoDB database"
          aria-describedby={messagesError ? "messages-error" : undefined}
        >
          {messagesLoading ? 'Loading...' : 'Load Messages'}
        </button>

        {messagesError && (
          <div className="error-message" role="alert" id="messages-error">
            <strong>Error:</strong> {messagesError}
          </div>
        )}

        {messages && <MessageList messages={messages} />}
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

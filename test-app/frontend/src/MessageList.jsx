import './MessageList.css'

/**
 * MessageList Component
 * 
 * Displays a list of messages with text and timestamps.
 * Handles empty state when no messages are provided.
 * 
 * @param {Object} props - Component props
 * @param {Array} props.messages - Array of message objects with text and createdAt fields
 * @returns {JSX.Element} The rendered message list component
 */
function MessageList({ messages = [] }) {
  // Handle empty state
  if (messages.length === 0) {
    return (
      <div className="message-list-empty">
        <p>No messages found</p>
      </div>
    )
  }

  return (
    <div className="message-list">
      <h3>Messages ({messages.length})</h3>
      <div className="message-list-container">
        {messages.map((message, index) => (
          <div key={index} className="message-item">
            <div className="message-text">
              {message.text}
            </div>
            <div className="message-timestamp">
              {formatTimestamp(message.createdAt)}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * Formats a timestamp into a human-readable format
 * 
 * @param {string|Date} timestamp - The timestamp to format
 * @returns {string} Formatted timestamp string
 */
function formatTimestamp(timestamp) {
  if (!timestamp) return 'No date'
  
  try {
    const date = new Date(timestamp)
    if (isNaN(date.getTime())) return 'Invalid date'
    
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    return 'Invalid date'
  }
}

export default MessageList
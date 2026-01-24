import { describe, expect, test } from 'vitest'
import { render, screen } from '@testing-library/react'
import MessageList from './MessageList'

describe('MessageList', () => {
  test('renders empty state when no messages provided', () => {
    render(<MessageList messages={[]} />)
    expect(screen.getByText('No messages found')).toBeInTheDocument()
  })

  test('renders empty state when messages prop is undefined', () => {
    render(<MessageList />)
    expect(screen.getByText('No messages found')).toBeInTheDocument()
  })

  test('renders message list when messages are provided', () => {
    const messages = [
      {
        text: 'Hello world',
        createdAt: '2026-01-23T15:30:00.000Z'
      },
      {
        text: 'Second message',
        createdAt: '2026-01-23T16:30:00.000Z'
      }
    ]

    render(<MessageList messages={messages} />)
    
    expect(screen.getByText('Messages (2)')).toBeInTheDocument()
    expect(screen.getByText('Hello world')).toBeInTheDocument()
    expect(screen.getByText('Second message')).toBeInTheDocument()
  })

  test('properly formats timestamps', () => {
    const messages = [
      {
        text: 'Test message',
        createdAt: '2026-01-23T15:30:00.000Z'
      }
    ]

    render(<MessageList messages={messages} />)
    
    // Check that a formatted timestamp is present (not the raw ISO string)
    expect(screen.queryByText('2026-01-23T15:30:00.000Z')).not.toBeInTheDocument()
    // The exact format depends on locale, but should contain date elements
    expect(screen.getByText(/2026/)).toBeInTheDocument()
  })

  test('handles messages without timestamps gracefully', () => {
    const messages = [
      {
        text: 'Message without timestamp'
      }
    ]

    render(<MessageList messages={messages} />)
    
    expect(screen.getByText('Message without timestamp')).toBeInTheDocument()
    expect(screen.getByText('No date')).toBeInTheDocument()
  })

  test('handles messages with invalid timestamps', () => {
    const messages = [
      {
        text: 'Message with invalid timestamp',
        createdAt: 'invalid-date'
      }
    ]

    render(<MessageList messages={messages} />)
    
    expect(screen.getByText('Message with invalid timestamp')).toBeInTheDocument()
    expect(screen.getByText('Invalid date')).toBeInTheDocument()
  })

  test('handles many messages without performance issues', () => {
    const messages = Array.from({ length: 100 }, (_, i) => ({
      text: `Message ${i + 1}`,
      createdAt: new Date(Date.now() + i * 1000).toISOString()
    }))

    const { container } = render(<MessageList messages={messages} />)
    
    expect(screen.getByText('Messages (100)')).toBeInTheDocument()
    expect(container.querySelectorAll('.message-item')).toHaveLength(100)
  })

  test('handles long message text correctly', () => {
    const longText = 'This is a very long message that should wrap properly without breaking the layout. '.repeat(10)
    const messages = [
      {
        text: longText,
        createdAt: '2026-01-23T15:30:00.000Z'
      }
    ]

    const { container } = render(<MessageList messages={messages} />)
    
    // Check that the message text is in the DOM (may be broken across multiple elements)
    const messageText = container.querySelector('.message-text')
    expect(messageText).toBeInTheDocument()
    expect(messageText.textContent).toBe(longText)
  })
})
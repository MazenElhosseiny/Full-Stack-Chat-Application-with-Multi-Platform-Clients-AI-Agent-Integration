import { useState, useEffect} from 'react'
import { LoginForm } from './components/LoginForm'
import { ChatMessages } from './components/ChatMessages'
import { ChatInput } from './components/ChatInput'

export function App() {
  const [token, setToken] = useState(null)
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: 'Welcome! Enter your secret key to get started.',
      variant: 'server',
      timestamp: new Date().toLocaleTimeString(),
    },
  ])

  // TODO: Replace the stub below with a real fetch to your Flask server.
  // The server URL comes from the .env file (VITE_SERVER_URL).
  const handleSend = async (text) => {
    // 1. Add the user's message to state immediately (optimistic update)
    const userMsg = {
      id: Date.now(),
      text,
      variant: 'user',
      timestamp: new Date().toLocaleTimeString(),
    }
    setMessages((prev) => [...prev, userMsg])

    // 2. TODO: Send the message to your Flask server
    //    Uncomment and adapt the fetch call below:
    
    const SERVER_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:8080'
    try {
      const res = await fetch(`${SERVER_URL}/chat`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` ,
        },
        credentials: 'include',
        body: JSON.stringify({ message: text }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
    
      const serverMsg = {
        id: Date.now(),
        text: data.response || JSON.stringify(data),
        variant: 'server',
        timestamp: new Date().toLocaleTimeString(),
      }
      setMessages((prev) => [...prev, serverMsg])
    } catch (err) {
      const errorMsg = {
        id: Date.now(),
        text: `Error: ${err.message}`,
        variant: 'error',
        timestamp: new Date().toLocaleTimeString(),
      }
      setMessages((prev) => [...prev, errorMsg])
    }
  }

  useEffect(() => {
  if (!token) return

  const SERVER_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:8080'

  const loadHistory = async () => {
    try {
      const res = await fetch(`${SERVER_URL}/history`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()

      const historyMsgs = data.flatMap((entry, i) => [
        {
          id: `history-user-${i}`,
          text: entry.message,
          variant: 'user',
          timestamp: new Date(entry.created_at).toLocaleTimeString(),
        },
        {
          id: `history-server-${i}`,
          text: entry.response,
          variant: 'server',
          timestamp: new Date(entry.created_at).toLocaleTimeString(),
        },
      ])

      setMessages((prev) => [...prev, ...historyMsgs])
    } catch (err) {
      console.error('Failed to load history:', err)
    }
  }

  loadHistory()
  }, [token])

  // Not authenticated → show login form
  if (!token) {
    return <LoginForm onAuth={setToken} />
  }

  // Authenticated → show chat interface
  return (
    <div className="flex flex-col h-screen max-w-2xl mx-auto">
      <header className="p-4 border-b bg-white">
        <h1 className="text-xl font-bold">CSC 6304 Chat</h1>
        <p className="text-xs text-gray-500">Week 5 — Full-Stack</p>
      </header>
      <ChatMessages messages={messages} />
      <ChatInput onSend={handleSend} />
    </div>
  )
  
}

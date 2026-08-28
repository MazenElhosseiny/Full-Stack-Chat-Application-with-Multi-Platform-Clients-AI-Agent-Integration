import { useState } from 'react'

export function ChatInput({ onSend }) {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!text.trim() || loading) return

    setLoading(true)
    await onSend(text.trim())
    setText('')
    setLoading(false)
  }

  return (
    <footer className="border-t bg-white p-4">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <label htmlFor="message-input" className="sr-only">
          Type a message
        </label>
        <input
          id="message-input"
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type a message..."
          className="flex-1 border-2 rounded-xl px-4 py-2 focus:outline-none focus:border-blue-500"
          autoComplete="off"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !text.trim()}
          className="bg-blue-600 text-white font-bold px-6 py-2 rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </footer>
  )
}

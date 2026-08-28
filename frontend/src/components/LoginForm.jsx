import { useState } from 'react'

// TODO: Replace with your Sprites.dev URL (or localhost for development)
const SERVER_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:8080'

export function LoginForm({ onAuth }) {
  const [key, setKey] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!key.trim()) return

    setLoading(true)
    setError(null)

    try {
      // TODO: POST to /auth — send { key }, receive { token }
      const res = await fetch(`${SERVER_URL}/auth`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: key }),
        credentials: 'include',
      })

      if (!res.ok) {
        throw new Error(
          res.status === 401
            ? 'Invalid secret key'
            : `Server error: ${res.status}`
        )
      }

      const data = await res.json()
      onAuth(data.token) // pass token up to App — transitions to chat view
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex items-center justify-center h-screen bg-gray-50">
      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-4 w-full max-w-sm p-6 bg-white rounded-2xl shadow-lg"
      >
        <h1 className="text-2xl font-bold text-center">CSC 6304 Chat</h1>
        <p className="text-sm text-gray-500 text-center">
          Enter your secret key to authenticate
        </p>

        <label
          htmlFor="secret-key"
          className="text-sm font-medium text-gray-700"
        >
          Secret Key
        </label>
        <input
          id="secret-key"
          type="password"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          placeholder="Enter your secret key..."
          className="border-2 rounded-xl px-4 py-2 text-lg focus:outline-none focus:border-blue-500"
          autoComplete="off"
        />

        {error && (
          <p className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg p-2">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white font-bold py-2 rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {loading ? 'Authenticating...' : 'Authenticate'}
        </button>
      </form>
    </main>
  )
}

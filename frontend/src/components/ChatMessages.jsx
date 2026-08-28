import { useEffect, useRef } from 'react'
import { MessageBubble } from './MessageBubble'

export function ChatMessages({ messages }) {
  const bottomRef = useRef(null)

  // Auto-scroll to the bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <main className="flex-1 overflow-y-auto p-4 bg-gray-50">
      {messages.length === 0 ? (
        <p className="text-center text-gray-400 mt-8">
          No messages yet. Start a conversation!
        </p>
      ) : (
        <div className="flex flex-col gap-2">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} {...msg} />
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </main>
  )
}

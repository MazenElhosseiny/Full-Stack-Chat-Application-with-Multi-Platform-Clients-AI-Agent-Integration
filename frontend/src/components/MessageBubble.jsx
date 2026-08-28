export function MessageBubble({ text, timestamp, variant }) {
  const isUser = variant === 'user'
  const isError = variant === 'error'

  const baseClasses =
    'max-w-[70%] p-3 rounded-2xl text-sm leading-relaxed'

  const variantClasses = isError
    ? 'self-center bg-red-100 text-red-800 border border-red-200'
    : isUser
      ? 'self-end bg-blue-600 text-white'
      : 'self-start bg-white border border-gray-200 text-gray-900'

  return (
    <article className={`${baseClasses} ${variantClasses}`}>
      <p>{text}</p>
      <time className="block text-xs mt-1 opacity-70">{timestamp}</time>
    </article>
  )
}

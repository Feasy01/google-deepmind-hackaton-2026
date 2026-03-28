import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { sendMessage, type ChatMessage } from '../api/chat'

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')

  const mutation = useMutation({
    mutationFn: (variables: { message: string; history: ChatMessage[] }) =>
      sendMessage(variables.message, variables.history),
    onSuccess: (data) => {
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }])
    },
  })

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || mutation.isPending) return

    const userMsg: ChatMessage = { role: 'user', content: trimmed }
    const updatedHistory = [...messages, userMsg]
    setMessages(updatedHistory)
    setInput('')
    mutation.mutate({ message: trimmed, history: messages })
  }

  return (
    <div className="flex h-[calc(100vh-120px)] flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto pb-4">
        {messages.length === 0 && (
          <p className="pt-20 text-center text-gray-500">
            Send a message to start chatting with DeepMind.
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-800 text-gray-100'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {mutation.isPending && (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-gray-800 px-4 py-2 text-gray-400">
              Thinking...
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-3 border-t border-gray-800 pt-4">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type a message..."
          className="flex-1 rounded-xl border border-gray-700 bg-gray-900 px-4 py-3 text-gray-100 placeholder-gray-500 outline-none focus:border-indigo-500"
        />
        <button
          onClick={handleSend}
          disabled={mutation.isPending}
          className="rounded-xl bg-indigo-600 px-6 py-3 font-medium text-white transition hover:bg-indigo-500 disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  )
}

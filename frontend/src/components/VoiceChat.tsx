import { useState, useRef, useCallback } from 'react'
import Vapi from '@vapi-ai/web'

const VAPI_PUBLIC_KEY = import.meta.env.VITE_VAPI_PUBLIC_KEY || ''

export function VoiceChat() {
  const [status, setStatus] = useState<'idle' | 'connecting' | 'active'>('idle')
  const [transcript, setTranscript] = useState<string[]>([])
  const vapiRef = useRef<Vapi | null>(null)

  const startCall = useCallback(() => {
    if (!VAPI_PUBLIC_KEY) {
      alert('Set VITE_VAPI_PUBLIC_KEY in frontend/.env')
      return
    }

    const vapi = new Vapi(VAPI_PUBLIC_KEY)
    vapiRef.current = vapi

    vapi.on('call-start', () => setStatus('active'))
    vapi.on('call-end', () => {
      setStatus('idle')
      vapiRef.current = null
    })
    vapi.on('message', (msg) => {
      if (msg.type === 'transcript' && msg.transcriptType === 'final') {
        setTranscript((prev) => [
          ...prev,
          `${msg.role === 'user' ? 'You' : 'Assistant'}: ${msg.transcript}`,
        ])
      }
    })
    vapi.on('error', (err) => {
      console.error('Vapi error:', err)
      setStatus('idle')
    })

    setStatus('connecting')
    vapi.start({
      firstMessage: "Hi! I'm your DeepMind assistant. How can I help you today?",
      model: {
        provider: 'google',
        model: 'gemini-2.0-flash',
      },
      voice: {
        provider: '11labs',
        voiceId: '21m00Tcm4TlvDq8ikWAM',
      },
    })
  }, [])

  const endCall = useCallback(() => {
    vapiRef.current?.stop()
    setStatus('idle')
  }, [])

  return (
    <div className="flex h-[calc(100vh-120px)] flex-col items-center justify-center gap-8">
      <div className="text-center">
        <div
          className={`mx-auto mb-6 flex h-32 w-32 items-center justify-center rounded-full transition-all ${
            status === 'active'
              ? 'animate-pulse bg-indigo-600/30 ring-4 ring-indigo-500'
              : status === 'connecting'
                ? 'bg-yellow-600/20 ring-4 ring-yellow-500'
                : 'bg-gray-800'
          }`}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-12 w-12 text-gray-300"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
            />
          </svg>
        </div>

        <p className="mb-4 text-lg text-gray-400">
          {status === 'idle' && 'Press the button to start a voice conversation'}
          {status === 'connecting' && 'Connecting...'}
          {status === 'active' && 'Listening... Speak now'}
        </p>

        {status === 'idle' ? (
          <button
            onClick={startCall}
            className="rounded-xl bg-indigo-600 px-8 py-3 font-medium text-white transition hover:bg-indigo-500"
          >
            Start Voice Chat
          </button>
        ) : (
          <button
            onClick={endCall}
            className="rounded-xl bg-red-600 px-8 py-3 font-medium text-white transition hover:bg-red-500"
          >
            End Call
          </button>
        )}
      </div>

      {transcript.length > 0 && (
        <div className="w-full max-w-md rounded-xl border border-gray-800 bg-gray-900 p-4">
          <h3 className="mb-3 text-sm font-medium text-gray-400">Transcript</h3>
          <div className="max-h-60 space-y-2 overflow-y-auto text-sm">
            {transcript.map((line, i) => (
              <p key={i} className="text-gray-300">
                {line}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

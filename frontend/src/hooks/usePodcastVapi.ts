import { useState, useRef, useCallback } from 'react'
import VapiModule from '@vapi-ai/web'

// Handle CJS default export interop
const Vapi = (VapiModule as any).default ?? VapiModule

const VAPI_PUBLIC_KEY = import.meta.env.VITE_VAPI_PUBLIC_KEY || ''
const VAPI_WEBHOOK_URL = import.meta.env.VITE_VAPI_WEBHOOK_URL || ''

export type PodcastMode = 'button' | 'always-listening'

export interface TranscriptEntry {
  role: 'user' | 'assistant'
  text: string
}

interface UsePodcastVapiOptions {
  podcastId: string
  mode: PodcastMode
  onStopPlayer: () => number // returns currentTime in seconds
  onStartPlayer: () => void
}

export function usePodcastVapi({
  podcastId,
  onStopPlayer,
  onStartPlayer,
}: UsePodcastVapiOptions) {
  const [status, setStatus] = useState<'idle' | 'connecting' | 'active'>('idle')
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([])
  const vapiRef = useRef<Vapi | null>(null)

  const startCall = useCallback(() => {
    if (!VAPI_PUBLIC_KEY) {
      alert('Set VITE_VAPI_PUBLIC_KEY in frontend/.env')
      return
    }

    const vapi = new Vapi(VAPI_PUBLIC_KEY)
    vapiRef.current = vapi

    vapi.on('call-start', () => {
      console.log('[Vapi] call started')
      setStatus('active')
    })
    vapi.on('call-end', () => {
      console.log('[Vapi] call ended')
      setStatus('idle')
      vapiRef.current = null
    })

    vapi.on('message', (msg: any) => {
      console.log('[Vapi message]', msg)
      // Handle tool calls from the assistant
      if (msg.type === 'tool-calls') {
        for (const toolCall of msg.toolCalls || []) {
          const fnName = toolCall.function?.name
          if (fnName === 'stop_player') {
            const seconds = onStopPlayer()
            const minutes = Math.floor(seconds / 60)
            const secs = Math.floor(seconds % 60)
            const timeStr = `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
            // Inject timestamp as system message so the model knows the position
            vapi.send({
              type: 'add-message',
              message: {
                role: 'system',
                content: `Podcast paused at ${timeStr} (${Math.floor(seconds)} seconds). Use this as timestamp_seconds when calling search_knowledge or search_previous_episodes.`,
              },
            })
          } else if (fnName === 'start_player') {
            onStartPlayer()
          }
        }
      }

      // Handle transcript updates
      if (msg.type === 'transcript' && msg.transcriptType === 'final') {
        setTranscript((prev) => [
          ...prev,
          {
            role: msg.role === 'user' ? 'user' : 'assistant',
            text: msg.transcript,
          },
        ])
      }
    })

    vapi.on('error', (err: any) => {
      console.error('[Vapi] error:', err)
      setStatus('idle')
    })

    setStatus('connecting')
    console.log('[Vapi] starting call for podcast:', podcastId)

    // Use inline assistant config with tools
    vapi.start({
      firstMessage:
        "I'm listening along with you. Feel free to ask me anything about the podcast!",
      model: {
        provider: 'google',
        model: 'gemini-2.0-flash',
        messages: [
          {
            role: 'system',
            content: `You are an interactive podcast companion assistant. The user is listening to a podcast and may ask questions about what they're hearing.

IMPORTANT RULES:
1. When the user asks ANY question or says something that sounds like a question (e.g., "hey andrew, what is HRV?", "what did he mean by that?"), IMMEDIATELY call the stop_player tool to pause the podcast, then call search_knowledge or search_previous_episodes with their question and the timestamp_seconds from the system message.
2. Use search_knowledge for factual questions about topics. Use search_previous_episodes for questions about what was discussed in the podcast.
3. When the user says something like "thank you", "thanks", "got it", "resume", "continue", "play", or any dismissal phrase, call start_player to resume the podcast.
4. After getting the answer, speak it naturally to the user.
5. Keep your answers concise and conversational.
6. The podcast_id for this session is: ${podcastId}
7. Always resume the podcast, even after invalid tool use.
`,
          },
        ],
        tools: [
          {
            type: 'function',
            function: {
              name: 'stop_player',
              description:
                'Pause the podcast player. Call this immediately when the user asks a question.',
              parameters: {
                type: 'object',
                properties: {},
                required: [],
              },
            },
            async: true,
          },
          {
            type: 'function',
            function: {
              name: 'start_player',
              description:
                'Resume the podcast player. Call this when the user is done with their question and wants to continue listening.',
              parameters: {
                type: 'object',
                properties: {},
                required: [],
              },
            },
            async: true,
          },
          {
            type: 'function',
            function: {
              name: 'search_knowledge',
              description:
                'Search articles for factual knowledge about a topic. Use when the caller asks a factual question.',
              parameters: {
                type: 'object',
                properties: {
                  query: {
                    type: 'string',
                    description:
                      'The search query based on what the user is asking',
                  },
                  conversation_context: {
                    type: 'string',
                    description:
                      'Last 30 seconds of conversation for additional context',
                  },
                  timestamp_seconds: {
                    type: 'integer',
                    description:
                      'The podcast playback position in seconds when the user asked. Get this from the system message.',
                  },
                },
                required: ['query'],
              },
            },
            server: {
              url: `${VAPI_WEBHOOK_URL}/api/vapi/webhook`,
            },
          },
          {
            type: 'function',
            function: {
              name: 'search_previous_episodes',
              description:
                'Search previous podcast episodes. Use when the caller asks about something discussed in a past episode.',
              parameters: {
                type: 'object',
                properties: {
                  query: {
                    type: 'string',
                    description:
                      'The search query based on what the user is asking',
                  },
                  conversation_context: {
                    type: 'string',
                    description:
                      'Last 30 seconds of conversation for additional context',
                  },
                  timestamp_seconds: {
                    type: 'integer',
                    description:
                      'The podcast playback position in seconds when the user asked. Get this from the system message.',
                  },
                },
                required: ['query'],
              },
            },
            server: {
              url: `${VAPI_WEBHOOK_URL}/api/vapi/webhook`,
            },
          },
        ],
      },
      voice: {
        provider: '11labs',
        voiceId: '21m00Tcm4TlvDq8ikWAM',
      },
      transcriber: {
        provider: 'deepgram',
        model: 'nova-2',
        language: 'en',
      },
      silenceTimeoutSeconds: 600,
      backgroundDenoisingEnabled: true,
      clientMessages: ['tool-calls', 'transcript'],
      metadata: {
        mode: 'podcast',
        podcast_id: podcastId,
      },
    } as any)
  }, [podcastId, onStopPlayer, onStartPlayer])

  const endCall = useCallback(() => {
    vapiRef.current?.stop()
    setStatus('idle')
  }, [])

  const clearTranscript = useCallback(() => {
    setTranscript([])
  }, [])

  return { startCall, endCall, clearTranscript, status, transcript }
}

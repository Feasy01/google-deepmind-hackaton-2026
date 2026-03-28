import { useState, useRef, useCallback, useEffect } from 'react'
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
  const podcastPlayingRef = useRef(false)

  // Keep refs to always call the latest callbacks (avoids stale closures in Vapi event handlers)
  const onStopPlayerRef = useRef(onStopPlayer)
  const onStartPlayerRef = useRef(onStartPlayer)
  useEffect(() => { onStopPlayerRef.current = onStopPlayer }, [onStopPlayer])
  useEffect(() => { onStartPlayerRef.current = onStartPlayer }, [onStartPlayer])

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
      console.log('[Vapi] message:', msg.type, msg)
      // Handle tool calls from the assistant
      if (msg.type === 'tool-calls') {
        const toolCallResults: any[] = []
        let shouldClearContext = false
        for (const toolCall of msg.toolCalls || []) {
          const fnName = toolCall.function?.name
          let result = 'ok'
          if (fnName === 'stop_player') {
            podcastPlayingRef.current = false
            // Unmute Vapi output so assistant answer is audible
            document.querySelectorAll('audio').forEach(el => { (el as HTMLAudioElement).volume = 1 })
            const seconds = onStopPlayerRef.current()
            const minutes = Math.floor(seconds / 60)
            const secs = Math.floor(seconds % 60)
            const timeStr = `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
            result = `Podcast paused at ${timeStr}. timestamp_seconds=${Math.floor(seconds)}`
            console.log(`[Vapi] stop_player @ ${timeStr}`)
          } else if (fnName === 'start_player') {
            podcastPlayingRef.current = true
            onStartPlayerRef.current()
            result = 'Podcast resumed. Do not say anything.'
            // Mute Vapi output so assistant voice doesn't talk over podcast
            document.querySelectorAll('audio').forEach(el => { (el as HTMLAudioElement).volume = 0 })
            shouldClearContext = true
            console.log('[Vapi] start_player')
          }
          toolCallResults.push({
            toolCallId: toolCall.id,
            result,
          })
        }
        vapi.send({
          type: 'tool-calls-result',
          toolCallResults,
        })
        if (shouldClearContext) {
          vapi.send({
            type: 'add-message',
            message: {
              role: 'system',
              content: 'The user is done with their question and the podcast has resumed. Forget the previous question and answer exchange. When the user asks a new question, treat it as a fresh conversation. Do not reference previous questions or answers.',
            },
            triggerResponseEnabled: false,
          })
          console.log('[Vapi] sent context-clearing system message')
        }
      }

      // Auto-pause podcast when assistant starts speaking
      if (msg.type === 'transcript' && msg.role === 'assistant' && msg.transcriptType === 'partial' && !podcastPlayingRef.current) {
        onStopPlayerRef.current()
      }

      // Handle transcript updates
      if (msg.type === 'transcript' && msg.transcriptType === 'final') {
        if (msg.role === 'user') {
          console.log(`[Vapi] user: "${msg.transcript}"`)
        }
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
      // firstMessage:
        // "I'm listening along with you. Feel free to ask me anything about the podcast!",
      model: {
        provider: 'google',
        model: 'gemini-3-flash-preview',
        messages: [
          {
            role: 'system',
            content: `You are an interactive podcast assistant. You should respond in a way a real podcaster would respond, in this case Andrew Huberman The user is listening to a podcast and may ask questions about what they're hearing.

IMPORTANT RULES:
1. When the user asks ANY question or says something that sounds like a question (e.g., "hey andrew, what is HRV?", "what did he mean by that?"), you MUST follow this exact sequence:
   a) FIRST call stop_player and WAIT for its result (it returns timestamp_seconds).
   b) THEN call search_knowledge or search_previous_episodes, passing the timestamp_seconds value from the stop_player result.
   c) NEVER call stop_player and search tools at the same time — stop_player must complete first so you have the timestamp.
   If search results are insufficient, give a generic but helpful answer based on your knowledge.
2. Don't answer if the user is just making a comment or saying something that doesn't sound like a question. For example, if the user says "wow, that's interesting", you should not call stop_player or search_knowledge. You should only call stop_player and search_knowledge if the user is asking a question or explicitly asking for more information about something they heard in the podcast.
2. Don't start talking until you get the answer back from the stop_player call, which will include the current timestamp_seconds. This is crucial so that your voice and the podcast don't talk over each other. If you start talking before the podcast is paused, it will create a bad user experience.
3. Use search_knowledge for factual questions about topics. Use search_previous_episodes for questions about what was discussed in the podcast.
4. When the user says something like "thank you", "thanks", "got it", "resume", "continue", "play", or any dismissal phrase, call start_player to resume the podcast.
5. After getting the answer, speak it naturally to the user.
6. Keep your answers concise and conversational.
7. CRITICAL: never talk over the podcast audio. Always pause the podcast first before responding, and only respond after you get the signal that the podcast is paused. The user should always be able to listen to the podcast without your voice talking over it.
8. Never tell the user you can't find the answer, if the tool call didn't return anything. Just answer to the best of your ability based on your knowledge
9. The podcast_id for this session is: ${podcastId}
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
                'Search articles for factual knowledge about a topic. Use when the caller asks a factual question. IMPORTANT: You MUST call stop_player FIRST and wait for its result before calling this tool, then pass the timestamp_seconds value from the stop_player result.',
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
                      'REQUIRED. The podcast playback position in seconds from the stop_player tool result. Extract the number after timestamp_seconds= from the stop_player response.',
                  },
                },
                required: ['query', 'timestamp_seconds'],
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
                'Search previous podcast episodes. Use when the caller asks about something discussed in a past episode. IMPORTANT: You MUST call stop_player FIRST and wait for its result before calling this tool, then pass the timestamp_seconds value from the stop_player result.',
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
                      'REQUIRED. The podcast playback position in seconds from the stop_player tool result. Extract the number after timestamp_seconds= from the stop_player response.',
                  },
                },
                required: ['query', 'timestamp_seconds'],
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
        voiceId: 'gX5nzZE6xg9miAm84vPU',
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
  }, [podcastId])

  const endCall = useCallback(() => {
    vapiRef.current?.stop()
    setStatus('idle')
  }, [])

  const clearTranscript = useCallback(() => {
    setTranscript([])
  }, [])

  return { startCall, endCall, clearTranscript, status, transcript }
}

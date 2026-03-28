import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchPodcasts, getPodcastAudioUrl } from '../api/podcast'
import { useAudioPlayer } from '../hooks/useAudioPlayer'
import { usePodcastVapi, type PodcastMode } from '../hooks/usePodcastVapi'

function formatTime(seconds: number): string {
  if (!isFinite(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

export function PodcastPlayer() {
  const [selectedPodcast, setSelectedPodcast] = useState<string>('')
  const [mode, setMode] = useState<PodcastMode>('button')
  const audio = useAudioPlayer()

  const { data: podcasts = [], isLoading: loadingPodcasts } = useQuery({
    queryKey: ['podcasts'],
    queryFn: fetchPodcasts,
  })

  const onStopPlayer = useCallback(() => {
    audio.pause()
    return audio.currentTime
  }, [audio])

  const onStartPlayer = useCallback(() => {
    audio.resume()
  }, [audio])

  const vapi = usePodcastVapi({
    podcastId: selectedPodcast,
    mode,
    onStopPlayer,
    onStartPlayer,
  })

  const handlePlayPause = () => {
    if (audio.isPlaying) {
      audio.pause()
    } else if (audio.currentTime > 0) {
      audio.resume()
    } else if (selectedPodcast) {
      audio.play(getPodcastAudioUrl(selectedPodcast))
    }
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    audio.seek(Number(e.target.value))
  }

  const handleSelectPodcast = (id: string) => {
    if (id !== selectedPodcast) {
      audio.stop()
      vapi.endCall()
      vapi.clearTranscript()
      setSelectedPodcast(id)
    }
  }

  const progress = audio.duration > 0 ? (audio.currentTime / audio.duration) * 100 : 0

  return (
    <div className="flex h-[calc(100vh-120px)] flex-col gap-6">
      {/* Podcast Selector */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
        <label className="mb-2 block text-sm font-medium text-gray-400">
          Select Podcast
        </label>
        {loadingPodcasts ? (
          <p className="text-sm text-gray-500">Loading podcasts...</p>
        ) : podcasts.length === 0 ? (
          <p className="text-sm text-gray-500">
            No podcasts found. Drop .mp3 files into backend/media/podcasts/
          </p>
        ) : (
          <select
            value={selectedPodcast}
            onChange={(e) => handleSelectPodcast(e.target.value)}
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-gray-100 outline-none focus:border-indigo-500"
          >
            <option value="">Choose a podcast...</option>
            {podcasts.map((p) => (
              <option key={p.id} value={p.id}>
                {p.id}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Audio Player */}
      {selectedPodcast && (
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
          <div className="mb-3 flex items-center gap-4">
            <button
              onClick={handlePlayPause}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-600 text-white transition hover:bg-indigo-500"
            >
              {audio.isPlaying ? (
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                </svg>
              ) : (
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              )}
            </button>
            <div className="flex-1">
              <input
                type="range"
                min={0}
                max={audio.duration || 0}
                step={0.1}
                value={audio.currentTime}
                onChange={handleSeek}
                className="w-full accent-indigo-500"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>{formatTime(audio.currentTime)}</span>
                <span>{formatTime(audio.duration)}</span>
              </div>
            </div>
          </div>
          {/* Progress bar visual */}
          <div className="h-1 w-full overflow-hidden rounded-full bg-gray-800">
            <div
              className="h-full bg-indigo-500 transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Mode Toggle */}
      {selectedPodcast && (
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => setMode('button')}
            className={`rounded-xl border p-4 text-left transition ${
              mode === 'button'
                ? 'border-indigo-500 bg-indigo-600/10'
                : 'border-gray-800 bg-gray-900 hover:border-gray-700'
            }`}
          >
            <h3 className="mb-1 text-sm font-semibold text-gray-200">
              Button Press
            </h3>
            <p className="text-xs text-gray-500">
              Press a button to activate the assistant
            </p>
          </button>
          <button
            onClick={() => setMode('always-listening')}
            className={`rounded-xl border p-4 text-left transition ${
              mode === 'always-listening'
                ? 'border-indigo-500 bg-indigo-600/10'
                : 'border-gray-800 bg-gray-900 hover:border-gray-700'
            }`}
          >
            <h3 className="mb-1 text-sm font-semibold text-gray-200">
              Always Listening
            </h3>
            <p className="text-xs text-gray-500">
              Assistant listens continuously for questions
            </p>
          </button>
        </div>
      )}

      {/* Vapi Controls */}
      {selectedPodcast && (
        <div className="flex items-center gap-4">
          {vapi.status === 'idle' ? (
            <button
              onClick={vapi.startCall}
              className="rounded-xl bg-emerald-600 px-6 py-3 font-medium text-white transition hover:bg-emerald-500"
            >
              {mode === 'button' ? 'Activate Assistant' : 'Start Listening Mode'}
            </button>
          ) : (
            <button
              onClick={vapi.endCall}
              className="rounded-xl bg-red-600 px-6 py-3 font-medium text-white transition hover:bg-red-500"
            >
              Stop Assistant
            </button>
          )}

          {/* Status indicator */}
          <div className="flex items-center gap-2">
            <div
              className={`h-2.5 w-2.5 rounded-full ${
                vapi.status === 'active'
                  ? 'animate-pulse bg-emerald-400'
                  : vapi.status === 'connecting'
                    ? 'animate-pulse bg-yellow-400'
                    : 'bg-gray-600'
              }`}
            />
            <span className="text-sm text-gray-400">
              {vapi.status === 'idle' && 'Assistant inactive'}
              {vapi.status === 'connecting' && 'Connecting...'}
              {vapi.status === 'active' && 'Assistant active — ask a question!'}
            </span>
          </div>
        </div>
      )}

      {/* Transcript Panel */}
      {vapi.transcript.length > 0 && (
        <div className="flex-1 overflow-hidden rounded-xl border border-gray-800 bg-gray-900">
          <div className="border-b border-gray-800 px-4 py-2">
            <h3 className="text-sm font-medium text-gray-400">Conversation</h3>
          </div>
          <div className="max-h-60 space-y-2 overflow-y-auto p-4">
            {vapi.transcript.map((entry, i) => (
              <div
                key={i}
                className={`flex ${entry.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm ${
                    entry.role === 'user'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-800 text-gray-100'
                  }`}
                >
                  {entry.text}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

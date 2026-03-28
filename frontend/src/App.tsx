import { useState, useCallback, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchPodcasters, getPodcastAudioUrl, getPodcastImageUrl } from './api/podcast'
import type { Episode } from './api/podcast'
import { useAudioPlayer } from './hooks/useAudioPlayer'
import { usePodcastVapi } from './hooks/usePodcastVapi'
import { PodcasterSection } from './components/PodcasterSection'
import { PlayerBar } from './components/PlayerBar'
import { MobilePlayer } from './components/MobilePlayer'

interface SelectedEpisode {
  podcaster: string
  episodeId: string
  episodeName: string
  imageUrl: string | null
}

function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

function App() {
  const [selected, setSelected] = useState<SelectedEpisode | null>(null)
  const [mobilePlayerOpen, setMobilePlayerOpen] = useState(false)

  const { data: podcasters = [], isLoading } = useQuery({
    queryKey: ['podcasters'],
    queryFn: fetchPodcasters,
  })

  const audio = useAudioPlayer()
  const pendingAudioUrlRef = useRef<string | null>(null)

  const onStopPlayer = useCallback(() => {
    audio.pause()
    return audio.currentTime
  }, [audio])

  const onStartPlayer = useCallback(() => {
    audio.resume()
  }, [audio])

  const onConnected = useCallback(() => {
    if (pendingAudioUrlRef.current) {
      audio.play(pendingAudioUrlRef.current)
      pendingAudioUrlRef.current = null
    }
  }, [audio])

  const vapi = usePodcastVapi({
    podcastId: selected?.episodeId ?? '',
    mode: 'always-listening',
    onStopPlayer,
    onStartPlayer,
    onConnected,
  })

  const selectEpisode = useCallback(
    (podcasterName: string, episode: Episode) => {
      // Block interaction while Vapi is connecting
      if (vapi.status === 'connecting') return

      // If same episode, just toggle play
      if (selected?.episodeId === episode.id && selected?.podcaster === podcasterName) {
        if (audio.isPlaying) {
          audio.pause()
        } else if (audio.currentTime > 0) {
          audio.resume()
        } else {
          audio.play(getPodcastAudioUrl(podcasterName, episode.id))
        }
        // Open mobile player on tap
        if (window.innerWidth <= 700) {
          setMobilePlayerOpen(true)
        }
        return
      }

      // Different episode — stop everything, start fresh
      audio.stop()
      vapi.endCall()
      vapi.clearTranscript()

      // Find the podcaster's cover image to use as default
      const podcasterData = podcasters.find((p) => p.podcaster === podcasterName)
      const coverUrl = podcasterData?.cover
        ? getPodcastImageUrl(podcasterName, podcasterData.cover)
        : null

      setSelected({
        podcaster: podcasterName,
        episodeId: episode.id,
        episodeName: episode.name,
        imageUrl: coverUrl,
      })

      // Defer audio until Vapi is connected
      pendingAudioUrlRef.current = getPodcastAudioUrl(podcasterName, episode.id)
      vapi.startCall()

      // Open mobile player on mobile
      if (window.innerWidth <= 700) {
        setMobilePlayerOpen(true)
      }
    },
    [selected, audio, vapi],
  )

  const togglePlayPause = useCallback(() => {
    if (audio.isPlaying) {
      audio.pause()
    } else {
      audio.resume()
    }
  }, [audio])

  const handleSeek = useCallback(
    (time: number) => {
      audio.seek(time)
    },
    [audio],
  )

  const handleSkip = useCallback(
    (seconds: number) => {
      audio.seek(Math.max(0, Math.min(audio.duration, audio.currentTime + seconds)))
    },
    [audio],
  )

  return (
    <div style={{ minHeight: '100vh' }}>
      {/* Topbar */}
      <header
        className="sticky top-0 flex items-center justify-between"
        style={{
          padding: '1.25rem clamp(1.5rem, 5vw, 4rem)',
          borderBottom: '2px solid var(--border-heavy)',
          background: 'var(--bg)',
          zIndex: 100,
        }}
      >
        <div
          style={{
            fontSize: '1.1rem',
            fontWeight: 700,
            letterSpacing: '-0.03em',
            textTransform: 'uppercase' as const,
          }}
        >
          ECHO{' '}
          <span style={{ fontWeight: 400, color: 'var(--ink-2)', marginLeft: '0.15rem' }}>
            — Podcasts
          </span>
        </div>
        <div
          className="flex items-center gap-6"
          style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--ink-2)' }}
        >
          <a href="#" style={{ color: 'inherit', textDecoration: 'none' }}>
            Browse
          </a>
          <a href="#" style={{ color: 'inherit', textDecoration: 'none' }}>
            Library
          </a>
        </div>
      </header>

      {/* Main content */}
      <main
        style={{
          maxWidth: 1200,
          margin: '0 auto',
          padding: 'clamp(2rem, 5vw, 3rem) clamp(1.5rem, 5vw, 4rem)',
        }}
      >
        {isLoading && (
          <>
            <style>{`
              .skeleton-section {
                display: grid;
                grid-template-columns: 280px 1fr;
                border-top: 2px solid var(--border-heavy);
                min-height: 400px;
                animation: fade-in 400ms var(--ease-out-quart) both;
              }
              .skeleton-sidebar {
                padding: 1.5rem 1.5rem 1.5rem 0;
                border-right: 1px solid var(--border);
              }
              .skeleton-bone {
                background: linear-gradient(90deg, var(--surface) 25%, #e8e0d5 50%, var(--surface) 75%);
                background-size: 200% 100%;
                animation: shimmer 1.5s infinite;
                border-radius: 4px;
              }
              .skeleton-row {
                display: grid;
                grid-template-columns: 48px 1fr 48px;
                gap: 1rem;
                padding: 1rem 1rem 1rem 1.5rem;
                border-bottom: 1px solid var(--border);
              }
              @media (max-width: 700px) {
                .skeleton-section { grid-template-columns: 1fr; min-height: auto; }
                .skeleton-sidebar { border-right: none; border-bottom: 1px solid var(--border); padding: 1.25rem 0; display: grid; grid-template-columns: 64px 1fr; gap: 0 0.85rem; }
              }
            `}</style>
            {[0, 1].map((i) => (
              <div key={i} className="skeleton-section" style={{ animationDelay: `${i * 120}ms` }}>
                <div className="skeleton-sidebar">
                  <div className="skeleton-bone" style={{ aspectRatio: '1', width: '100%', marginBottom: '1rem', borderRadius: 6 }} />
                  <div>
                    <div className="skeleton-bone" style={{ height: 16, width: '70%', marginBottom: '0.5rem' }} />
                    <div className="skeleton-bone" style={{ height: 12, width: '50%' }} />
                  </div>
                </div>
                <div>
                  {[0, 1, 2, 3, 4].map((j) => (
                    <div key={j} className="skeleton-row">
                      <div className="skeleton-bone" style={{ height: 12, width: 24 }} />
                      <div className="skeleton-bone" style={{ height: 14, width: `${60 + j * 8}%` }} />
                      <div className="skeleton-bone" style={{ height: 32, width: 32, borderRadius: '50%' }} />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </>
        )}

        {podcasters.map((p, i) => (
          <div
            key={p.podcaster}
            style={{
              animation: `fade-in-up 500ms var(--ease-out-expo) ${i * 150}ms both`,
            }}
          >
            <PodcasterSection
              podcaster={p}
              selectedEpisodeId={
                selected?.podcaster === p.podcaster ? selected.episodeId : null
              }
              onSelectEpisode={(ep) => selectEpisode(p.podcaster, ep)}
            />
          </div>
        ))}
      </main>

      {/* Bottom spacer for player */}
      {selected && <div style={{ height: 120 }} />}

      {/* Desktop player */}
      {selected && (
        <PlayerBar
          episodeName={selected.episodeName}
          podcasterName={selected.podcaster}
          imageUrl={selected.imageUrl}
          isPlaying={audio.isPlaying}
          currentTime={audio.currentTime}
          duration={audio.duration}
          onTogglePlay={togglePlayPause}
          onSeek={handleSeek}
          onSkip={handleSkip}
          disabled={vapi.status === 'connecting'}
        />
      )}

      {/* Mobile player */}
      {selected && (
        <MobilePlayer
          isOpen={mobilePlayerOpen}
          onClose={() => setMobilePlayerOpen(false)}
          episodeName={selected.episodeName}
          podcasterName={selected.podcaster}
          initials={getInitials(selected.podcaster)}
          imageUrl={selected.imageUrl}
          isPlaying={audio.isPlaying}
          currentTime={audio.currentTime}
          duration={audio.duration}
          onTogglePlay={togglePlayPause}
          onSeek={handleSeek}
          onSkip={handleSkip}
          disabled={vapi.status === 'connecting'}
        />
      )}
    </div>
  )
}

export default App

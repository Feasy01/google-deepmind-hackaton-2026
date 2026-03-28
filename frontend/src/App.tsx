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
    mode: 'always-listening',
    onStopPlayer,
    onStartPlayer,
    onConnected,
  })

  const selectEpisode = useCallback(
    (podcasterName: string, episode: Episode) => {
      // If same episode, just toggle play
      if (selected?.episodeId === episode.id && selected?.podcaster === podcasterName) {
        if (audio.isPlaying) {
          audio.pause()
        } else if (audio.currentTime > 0) {
          audio.resume()
        } else {
          // First play of already-selected episode — gate on Vapi
          const url = getPodcastAudioUrl(podcasterName, episode.id)
          if (vapi.status === 'active') {
            audio.play(url)
          } else {
            pendingAudioUrlRef.current = url
          }
        }
        // Open mobile player on tap
        if (window.innerWidth <= 700) {
          setMobilePlayerOpen(true)
        }
        return
      }

      // Different episode — stop audio, update context, but do NOT auto-play
      audio.stop()
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

      // Update Vapi assistant context with the new podcast
      vapi.setPodcast(episode.id)

      // Open mobile player on mobile
      if (window.innerWidth <= 700) {
        setMobilePlayerOpen(true)
      }
    },
    [selected, audio, vapi, podcasters],
  )

  const togglePlayPause = useCallback(() => {
    if (audio.isPlaying) {
      audio.pause()
    } else if (audio.currentTime > 0) {
      // Resuming — Vapi is already connected at this point
      audio.resume()
    } else if (selected) {
      // Starting playback for the first time — gate on Vapi connection
      const url = getPodcastAudioUrl(selected.podcaster, selected.episodeId)
      if (vapi.status === 'active') {
        audio.play(url)
      } else {
        pendingAudioUrlRef.current = url
      }
    }
  }, [audio, selected, vapi.status])

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
          <p style={{ color: 'var(--ink-3)', fontSize: '0.85rem' }}>Loading podcasts...</p>
        )}

        {podcasters.map((p) => (
          <PodcasterSection
            key={p.podcaster}
            podcaster={p}
            selectedEpisodeId={
              selected?.podcaster === p.podcaster ? selected.episodeId : null
            }
            onSelectEpisode={(ep) => selectEpisode(p.podcaster, ep)}
          />
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
        />
      )}
    </div>
  )
}

export default App

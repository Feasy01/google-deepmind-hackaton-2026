# Echo Warm Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the existing dark frontend with a warm-cream themed podcast app where the AI assistant auto-arms on play.

**Architecture:** Single-page React app with react-query for data fetching. App.tsx owns all state (selected episode, audio player, Vapi). Presentational components render podcaster sections, episode rows, and player UIs. Tailwind v4 for styling with CSS custom properties for theme tokens.

**Tech Stack:** React 19, TypeScript, Tailwind CSS v4, Vite, react-query, Vapi Web SDK

**Spec:** `docs/superpowers/specs/2026-03-28-echo-warm-frontend-design.md`
**Mockup reference:** `frontend/mockups/mockup-2b-warm.html`

---

### Task 1: Clean up — remove old components and update base files

**Files:**
- Delete: `frontend/src/components/Chat.tsx`
- Delete: `frontend/src/components/VoiceChat.tsx`
- Delete: `frontend/src/api/chat.ts`
- Modify: `frontend/index.html`
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Delete old components**

```bash
rm frontend/src/components/Chat.tsx
rm frontend/src/components/VoiceChat.tsx
rm frontend/src/api/chat.ts
```

- [ ] **Step 2: Update `frontend/index.html`**

Replace the full file with:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Echo — Podcasts</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;1,6..72,400&display=swap"
      rel="stylesheet"
    />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 3: Update `frontend/src/index.css`**

Replace the full file with:

```css
@import "tailwindcss";

:root {
  --bg: #faf7f2;
  --surface: #f0ebe3;
  --ink: #2c2418;
  --ink-2: #6b5d4d;
  --ink-3: #a89882;
  --accent: #b45309;
  --accent-bg: #fef3c7;
  --border: #e2d9cc;
  --border-heavy: #2c2418;
  --player-bg: #2c2418;
  --player-surface: #3d3226;
}

*,
*::before,
*::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Space Grotesk', sans-serif;
  background: var(--bg);
  color: var(--ink);
  -webkit-font-smoothing: antialiased;
}
```

- [ ] **Step 4: Verify the app still compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -5
```

Expected: Errors about missing imports in App.tsx (Chat, VoiceChat) — this is fine, we rewrite App.tsx in the next task.

- [ ] **Step 5: Commit**

```bash
git add -A frontend/src/components/Chat.tsx frontend/src/components/VoiceChat.tsx frontend/src/api/chat.ts frontend/index.html frontend/src/index.css
git commit -m "chore: remove old components, add warm theme and Google Fonts"
```

---

### Task 2: Update API layer

**Files:**
- Modify: `frontend/src/api/podcast.ts`

- [ ] **Step 1: Rewrite `frontend/src/api/podcast.ts`**

```ts
export interface Episode {
  id: string
  name: string
  filename: string
}

export interface Podcaster {
  podcaster: string
  categories: string[]
  description: string
  episodes: Episode[]
}

export async function fetchPodcasters(): Promise<Podcaster[]> {
  const res = await fetch('/api/podcast/')
  if (!res.ok) throw new Error('Failed to fetch podcasters')
  return res.json()
}

export function getPodcastAudioUrl(podcaster: string, episodeId: string): string {
  return `/api/podcast/${encodeURIComponent(podcaster)}/${encodeURIComponent(episodeId)}/audio`
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/podcast.ts
git commit -m "feat: update podcast API types to match backend podcaster response"
```

---

### Task 3: Create EpisodeRow component

**Files:**
- Create: `frontend/src/components/EpisodeRow.tsx`

- [ ] **Step 1: Create `frontend/src/components/EpisodeRow.tsx`**

```tsx
import type { Episode } from '../api/podcast'

interface EpisodeRowProps {
  episode: Episode
  index: number
  isActive: boolean
  onSelect: () => void
}

export function EpisodeRow({ episode, index, isActive, onSelect }: EpisodeRowProps) {
  const num = String(index + 1).padStart(2, '0')

  return (
    <div
      onClick={onSelect}
      className="grid items-center gap-4 border-b cursor-pointer transition-colors duration-150"
      style={{
        gridTemplateColumns: '48px 1fr 60px 48px',
        padding: '1rem 1rem 1rem 1.5rem',
        borderColor: 'var(--border)',
        background: isActive ? 'var(--accent-bg)' : undefined,
      }}
      onMouseEnter={(e) => {
        if (!isActive) e.currentTarget.style.background = 'var(--surface)'
      }}
      onMouseLeave={(e) => {
        if (!isActive) e.currentTarget.style.background = ''
      }}
    >
      {/* Number */}
      <span
        className="text-xs font-semibold tabular-nums"
        style={{ color: isActive ? 'var(--accent)' : 'var(--ink-3)' }}
      >
        {num}
      </span>

      {/* Info */}
      <div>
        <div
          className="text-sm font-semibold"
          style={{ letterSpacing: '-0.01em', color: 'var(--ink)' }}
        >
          {episode.name}
        </div>
      </div>

      {/* Duration placeholder */}
      <span
        className="text-xs tabular-nums text-right"
        style={{ color: 'var(--ink-3)' }}
      >
        —
      </span>

      {/* Play button */}
      <button
        onClick={(e) => {
          e.stopPropagation()
          onSelect()
        }}
        className="flex items-center justify-center rounded-full transition-all duration-150 cursor-pointer"
        style={{
          width: 32,
          height: 32,
          border: isActive ? 'none' : '1.5px solid var(--border)',
          background: isActive ? 'var(--accent)' : 'transparent',
        }}
      >
        <svg
          viewBox="0 0 24 24"
          style={{
            width: 12,
            height: 12,
            fill: isActive ? '#fff' : 'var(--ink-3)',
            marginLeft: 1.5,
          }}
        >
          <path d="M8 5v14l11-7z" />
        </svg>
      </button>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/EpisodeRow.tsx
git commit -m "feat: add EpisodeRow component"
```

---

### Task 4: Create PodcasterSection component

**Files:**
- Create: `frontend/src/components/PodcasterSection.tsx`

- [ ] **Step 1: Create `frontend/src/components/PodcasterSection.tsx`**

```tsx
import type { Podcaster, Episode } from '../api/podcast'
import { EpisodeRow } from './EpisodeRow'

interface PodcasterSectionProps {
  podcaster: Podcaster
  selectedEpisodeId: string | null
  onSelectEpisode: (episode: Episode) => void
}

function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export function PodcasterSection({
  podcaster,
  selectedEpisodeId,
  onSelectEpisode,
}: PodcasterSectionProps) {
  return (
    <section
      className="grid"
      style={{
        gridTemplateColumns: '280px 1fr',
        borderTop: '2px solid var(--border-heavy)',
        minHeight: 'calc(100vh - 200px)',
      }}
    >
      {/* Left panel — podcaster info */}
      <aside
        className="sticky self-start"
        style={{
          top: 70,
          borderRight: '1px solid var(--border)',
          padding: '1.5rem 1.5rem 1.5rem 0',
        }}
      >
        {/* Avatar */}
        <div
          className="flex items-center justify-center rounded-md w-full"
          style={{
            aspectRatio: '1',
            background: 'var(--surface)',
            fontFamily: "'Newsreader', serif",
            fontSize: '3.5rem',
            fontStyle: 'italic',
            color: 'var(--ink-3)',
            borderRadius: 6,
          }}
        >
          {getInitials(podcaster.podcaster)}
        </div>

        {/* Name */}
        <div
          className="font-bold"
          style={{
            fontSize: '1rem',
            letterSpacing: '-0.02em',
            marginTop: '1rem',
          }}
        >
          {podcaster.podcaster}
        </div>

        {/* Categories */}
        <div style={{ fontSize: '0.75rem', color: 'var(--ink-3)', marginTop: '0.2rem' }}>
          {podcaster.categories.join(' \u00B7 ')}
        </div>

        {/* Bio */}
        <div
          style={{
            fontSize: '0.78rem',
            color: 'var(--ink-2)',
            marginTop: '0.75rem',
            lineHeight: 1.5,
          }}
        >
          {podcaster.description}
        </div>

        {/* Episode count */}
        <div
          className="font-semibold uppercase"
          style={{
            marginTop: '1.25rem',
            fontSize: '0.7rem',
            letterSpacing: '0.08em',
            color: 'var(--ink-3)',
          }}
        >
          {podcaster.episodes.length} episode{podcaster.episodes.length !== 1 ? 's' : ''}
        </div>
      </aside>

      {/* Right panel — episode table */}
      <div>
        {/* Table header */}
        <div
          className="grid font-semibold uppercase"
          style={{
            gridTemplateColumns: '48px 1fr 60px 48px',
            gap: '1rem',
            padding: '0.6rem 1rem 0.6rem 1.5rem',
            borderBottom: '1px solid var(--ink)',
            fontSize: '0.65rem',
            letterSpacing: '0.08em',
            color: 'var(--ink-3)',
          }}
        >
          <span>#</span>
          <span>Title</span>
          <span className="text-right">Duration</span>
          <span />
        </div>

        {/* Episode rows */}
        {podcaster.episodes.map((ep, i) => (
          <EpisodeRow
            key={ep.id}
            episode={ep}
            index={i}
            isActive={ep.id === selectedEpisodeId}
            onSelect={() => onSelectEpisode(ep)}
          />
        ))}
      </div>
    </section>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/PodcasterSection.tsx
git commit -m "feat: add PodcasterSection two-panel layout component"
```

---

### Task 5: Create PlayerBar component (desktop)

**Files:**
- Create: `frontend/src/components/PlayerBar.tsx`

- [ ] **Step 1: Create `frontend/src/components/PlayerBar.tsx`**

```tsx
interface PlayerBarProps {
  episodeName: string
  podcasterName: string
  isPlaying: boolean
  currentTime: number
  duration: number
  onTogglePlay: () => void
  onSeek: (time: number) => void
  onSkip: (seconds: number) => void
}

function formatTime(seconds: number): string {
  if (!isFinite(seconds) || seconds < 0) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

export function PlayerBar({
  episodeName,
  podcasterName,
  isPlaying,
  currentTime,
  duration,
  onTogglePlay,
  onSeek,
  onSkip,
}: PlayerBarProps) {
  const progress = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <div
      className="fixed bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-4 z-200 max-md:hidden"
      style={{
        width: 'min(600px, calc(100% - 3rem))',
        background: 'var(--player-bg)',
        color: '#f0ebe3',
        borderRadius: 10,
        padding: '1rem 1.25rem',
        boxShadow: '0 8px 32px rgba(44,36,24,0.22)',
      }}
    >
      {/* Episode info */}
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate" style={{ fontSize: '0.82rem' }}>
          {episodeName}
        </div>
        <div style={{ fontSize: '0.7rem', color: '#a89882', marginTop: '0.1rem' }}>
          {podcasterName}
        </div>
      </div>

      {/* Time */}
      <span
        className="whitespace-nowrap tabular-nums"
        style={{ fontSize: '0.65rem', color: '#7a6c58' }}
      >
        {formatTime(currentTime)} / {formatTime(duration)}
      </span>

      {/* Controls */}
      <div className="flex items-center gap-4">
        {/* Rewind 15s */}
        <button
          onClick={() => onSkip(-15)}
          className="flex items-center cursor-pointer transition-colors duration-150"
          style={{ background: 'none', border: 'none', color: '#a89882' }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#f0ebe3')}
          onMouseLeave={(e) => (e.currentTarget.style.color = '#a89882')}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M1 4v6h6" /><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
          </svg>
        </button>

        {/* Play/Pause */}
        <button
          onClick={onTogglePlay}
          className="flex items-center justify-center rounded-full cursor-pointer transition-transform duration-100 hover:scale-110"
          style={{
            width: 36,
            height: 36,
            background: 'var(--accent)',
            border: 'none',
          }}
        >
          {isPlaying ? (
            <svg viewBox="0 0 24 24" style={{ fill: '#fff', width: 14, height: 14 }}>
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" style={{ fill: '#fff', width: 14, height: 14, marginLeft: 2 }}>
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>

        {/* Forward 15s */}
        <button
          onClick={() => onSkip(15)}
          className="flex items-center cursor-pointer transition-colors duration-150"
          style={{ background: 'none', border: 'none', color: '#a89882' }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#f0ebe3')}
          onMouseLeave={(e) => (e.currentTarget.style.color = '#a89882')}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M23 4v6h-6" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
        </button>
      </div>

      {/* Progress bar */}
      <div
        className="absolute left-4 right-4 bottom-0 cursor-pointer"
        style={{ height: 2, background: 'var(--player-surface)', borderRadius: 1 }}
        onClick={(e) => {
          const rect = e.currentTarget.getBoundingClientRect()
          const pct = (e.clientX - rect.left) / rect.width
          onSeek(pct * duration)
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${progress}%`,
            background: 'var(--accent)',
            borderRadius: 1,
          }}
        />
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/PlayerBar.tsx
git commit -m "feat: add PlayerBar floating desktop player component"
```

---

### Task 6: Create MobilePlayer component

**Files:**
- Create: `frontend/src/components/MobilePlayer.tsx`

- [ ] **Step 1: Create `frontend/src/components/MobilePlayer.tsx`**

```tsx
interface MobilePlayerProps {
  isOpen: boolean
  onClose: () => void
  episodeName: string
  podcasterName: string
  initials: string
  isPlaying: boolean
  currentTime: number
  duration: number
  onTogglePlay: () => void
  onSeek: (time: number) => void
  onSkip: (seconds: number) => void
}

function formatTime(seconds: number): string {
  if (!isFinite(seconds) || seconds < 0) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

export function MobilePlayer({
  isOpen,
  onClose,
  episodeName,
  podcasterName,
  initials,
  isPlaying,
  currentTime,
  duration,
  onTogglePlay,
  onSeek,
  onSkip,
}: MobilePlayerProps) {
  if (!isOpen) return null

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <div
      className="fixed inset-0 z-300 flex flex-col overflow-hidden md:!hidden"
      style={{ background: 'var(--player-bg)', color: '#f0ebe3' }}
    >
      {/* Top bar */}
      <div className="flex items-center justify-between shrink-0" style={{ padding: '1rem 1.25rem' }}>
        <button
          onClick={onClose}
          className="flex items-center gap-1.5 cursor-pointer transition-colors duration-150"
          style={{
            background: 'none',
            border: 'none',
            color: '#a89882',
            fontFamily: 'inherit',
            fontSize: '0.8rem',
            fontWeight: 500,
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5" /><path d="M12 19l-7-7 7-7" />
          </svg>
          Back
        </button>
        <span
          className="font-semibold uppercase"
          style={{ fontSize: '0.68rem', letterSpacing: '0.08em', color: '#7a6c58' }}
        >
          Now Playing
        </span>
      </div>

      {/* Body */}
      <div className="flex-1 flex flex-col items-center justify-center gap-8" style={{ padding: '2rem 2rem 1rem' }}>
        {/* Artwork */}
        <div
          className="flex items-center justify-center"
          style={{
            width: 'min(280px, 65vw)',
            aspectRatio: '1',
            borderRadius: 14,
            background: 'var(--player-surface)',
            fontFamily: "'Newsreader', serif",
            fontSize: '4rem',
            fontStyle: 'italic',
            color: '#6b5d4d',
          }}
        >
          {initials}
        </div>

        {/* Info */}
        <div className="text-center">
          <div className="font-semibold" style={{ fontSize: '1.25rem', letterSpacing: '-0.02em' }}>
            {episodeName}
          </div>
          <div style={{ fontSize: '0.85rem', color: '#a89882', marginTop: '0.3rem' }}>
            {podcasterName}
          </div>
        </div>

        {/* Progress */}
        <div className="w-full" style={{ maxWidth: 360 }}>
          <div
            className="w-full cursor-pointer"
            style={{ height: 4, background: 'var(--player-surface)', borderRadius: 2 }}
            onClick={(e) => {
              const rect = e.currentTarget.getBoundingClientRect()
              const pct = (e.clientX - rect.left) / rect.width
              onSeek(pct * duration)
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${progress}%`,
                background: 'var(--accent)',
                borderRadius: 2,
              }}
            />
          </div>
          <div
            className="flex justify-between tabular-nums"
            style={{ marginTop: '0.4rem', fontSize: '0.68rem', color: '#7a6c58' }}
          >
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-8" style={{ paddingBottom: '1rem' }}>
          <button
            onClick={() => onSkip(-15)}
            className="flex items-center cursor-pointer transition-colors duration-150"
            style={{ background: 'none', border: 'none', color: '#a89882' }}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M1 4v6h6" /><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
            </svg>
          </button>

          <button
            onClick={onTogglePlay}
            className="flex items-center justify-center rounded-full cursor-pointer transition-transform duration-100 hover:scale-105"
            style={{
              width: 56,
              height: 56,
              background: 'var(--accent)',
              border: 'none',
            }}
          >
            {isPlaying ? (
              <svg viewBox="0 0 24 24" style={{ fill: '#fff', width: 22, height: 22 }}>
                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" style={{ fill: '#fff', width: 22, height: 22, marginLeft: 3 }}>
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>

          <button
            onClick={() => onSkip(15)}
            className="flex items-center cursor-pointer transition-colors duration-150"
            style={{ background: 'none', border: 'none', color: '#a89882' }}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M23 4v6h-6" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/MobilePlayer.tsx
git commit -m "feat: add MobilePlayer fullscreen overlay component"
```

---

### Task 7: Rewrite App.tsx — main layout with auto-arming Vapi

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Rewrite `frontend/src/App.tsx`**

```tsx
import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchPodcasters, getPodcastAudioUrl } from './api/podcast'
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

  const onStopPlayer = useCallback(() => {
    audio.pause()
    return audio.currentTime
  }, [audio])

  const onStartPlayer = useCallback(() => {
    audio.resume()
  }, [audio])

  const vapi = usePodcastVapi({
    podcastId: selected?.episodeId ?? '',
    mode: 'always-listening',
    onStopPlayer,
    onStartPlayer,
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

      setSelected({
        podcaster: podcasterName,
        episodeId: episode.id,
        episodeName: episode.name,
      })

      // Start audio + auto-arm Vapi
      const url = getPodcastAudioUrl(podcasterName, episode.id)
      audio.play(url)

      // Small delay so the podcastId state is set before startCall reads it
      setTimeout(() => {
        vapi.startCall()
      }, 100)

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
        className="sticky top-0 z-100 flex items-center justify-between"
        style={{
          padding: '1.25rem clamp(1.5rem, 5vw, 4rem)',
          borderBottom: '2px solid var(--border-heavy)',
          background: 'var(--bg)',
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
          <a href="#" className="no-underline hover:text-[var(--ink)]" style={{ color: 'inherit', textDecoration: 'none' }}>
            Browse
          </a>
          <a href="#" className="no-underline hover:text-[var(--ink)]" style={{ color: 'inherit', textDecoration: 'none' }}>
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
```

- [ ] **Step 2: Verify the app compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: rewrite App.tsx with warm theme, podcaster list, and auto-arming Vapi"
```

---

### Task 8: Add mobile responsive styles to PodcasterSection

**Files:**
- Modify: `frontend/src/components/PodcasterSection.tsx`
- Modify: `frontend/src/components/EpisodeRow.tsx`

The desktop layout is done but we need mobile breakpoints. On mobile (<=700px):
- PodcasterSection collapses to single column with compact header
- EpisodeRow hides number, duration, description — shows only title + play button

- [ ] **Step 1: Update `PodcasterSection.tsx` to add mobile styles**

Add a `<style>` tag at the top of the component return, and use CSS classes instead of inline grid styles so media queries work.

Replace the entire `PodcasterSection.tsx` with:

```tsx
import type { Podcaster, Episode } from '../api/podcast'
import { EpisodeRow } from './EpisodeRow'

interface PodcasterSectionProps {
  podcaster: Podcaster
  selectedEpisodeId: string | null
  onSelectEpisode: (episode: Episode) => void
}

function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export function PodcasterSection({
  podcaster,
  selectedEpisodeId,
  onSelectEpisode,
}: PodcasterSectionProps) {
  return (
    <>
      <style>{`
        .podcaster-grid {
          display: grid;
          grid-template-columns: 280px 1fr;
          border-top: 2px solid var(--border-heavy);
          min-height: calc(100vh - 200px);
        }
        .podcaster-sidebar {
          border-right: 1px solid var(--border);
          padding: 1.5rem 1.5rem 1.5rem 0;
          position: sticky;
          top: 70px;
          align-self: start;
        }
        .podcaster-bio { display: block; }
        .podcaster-ep-count { display: block; }
        .ep-table-header {
          display: grid;
          grid-template-columns: 48px 1fr 60px 48px;
          gap: 1rem;
          padding: 0.6rem 1rem 0.6rem 1.5rem;
          border-bottom: 1px solid var(--ink);
          font-size: 0.65rem;
          font-weight: 600;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: var(--ink-3);
        }

        @media (max-width: 700px) {
          .podcaster-grid {
            grid-template-columns: 1fr;
            min-height: auto;
            border-top: 1px solid var(--border);
          }
          .podcaster-sidebar {
            position: static;
            border-right: none;
            border-bottom: 1px solid var(--border);
            padding: 1.25rem 0;
            display: grid;
            grid-template-columns: 64px 1fr;
            gap: 0 0.85rem;
            align-items: start;
          }
          .podcaster-avatar-mobile {
            font-size: 1.8rem !important;
            border-radius: 4px !important;
            margin-bottom: 0 !important;
          }
          .podcaster-bio { display: none; }
          .podcaster-ep-count { grid-column: 1 / -1; margin-top: 0.75rem; }
          .ep-table-header { display: none; }
        }
      `}</style>

      <section className="podcaster-grid">
        {/* Left panel */}
        <aside className="podcaster-sidebar">
          <div
            className="podcaster-avatar-mobile flex items-center justify-center w-full"
            style={{
              aspectRatio: '1',
              background: 'var(--surface)',
              fontFamily: "'Newsreader', serif",
              fontSize: '3.5rem',
              fontStyle: 'italic',
              color: 'var(--ink-3)',
              borderRadius: 6,
              marginBottom: '1rem',
            }}
          >
            {getInitials(podcaster.podcaster)}
          </div>

          <div>
            <div className="font-bold" style={{ fontSize: '1rem', letterSpacing: '-0.02em' }}>
              {podcaster.podcaster}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--ink-3)', marginTop: '0.2rem' }}>
              {podcaster.categories.join(' \u00B7 ')}
            </div>
          </div>

          <div
            className="podcaster-bio"
            style={{ fontSize: '0.78rem', color: 'var(--ink-2)', marginTop: '0.75rem', lineHeight: 1.5 }}
          >
            {podcaster.description}
          </div>

          <div
            className="podcaster-ep-count font-semibold uppercase"
            style={{ marginTop: '1.25rem', fontSize: '0.7rem', letterSpacing: '0.08em', color: 'var(--ink-3)' }}
          >
            {podcaster.episodes.length} episode{podcaster.episodes.length !== 1 ? 's' : ''}
          </div>
        </aside>

        {/* Right panel */}
        <div>
          <div className="ep-table-header">
            <span>#</span>
            <span>Title</span>
            <span className="text-right">Duration</span>
            <span />
          </div>

          {podcaster.episodes.map((ep, i) => (
            <EpisodeRow
              key={ep.id}
              episode={ep}
              index={i}
              isActive={ep.id === selectedEpisodeId}
              onSelect={() => onSelectEpisode(ep)}
            />
          ))}
        </div>
      </section>
    </>
  )
}
```

- [ ] **Step 2: Update `EpisodeRow.tsx` for mobile**

Replace the entire file:

```tsx
import type { Episode } from '../api/podcast'

interface EpisodeRowProps {
  episode: Episode
  index: number
  isActive: boolean
  onSelect: () => void
}

export function EpisodeRow({ episode, index, isActive, onSelect }: EpisodeRowProps) {
  const num = String(index + 1).padStart(2, '0')

  return (
    <>
      <style>{`
        .ep-row {
          display: grid;
          grid-template-columns: 48px 1fr 60px 48px;
          align-items: center;
          gap: 1rem;
          padding: 1rem 1rem 1rem 1.5rem;
          border-bottom: 1px solid var(--border);
          cursor: pointer;
          transition: background 0.15s;
        }
        .ep-row:hover { background: var(--surface); }
        .ep-row.ep-active { background: var(--accent-bg); }
        .ep-row.ep-active:hover { background: var(--accent-bg); }
        .ep-row-num { display: block; }
        .ep-row-dur { display: block; }

        @media (max-width: 700px) {
          .ep-row {
            grid-template-columns: 1fr 48px;
            padding: 0.85rem 0;
            gap: 0.75rem;
          }
          .ep-row-num { display: none; }
          .ep-row-dur { display: none; }
        }
      `}</style>

      <div
        className={`ep-row ${isActive ? 'ep-active' : ''}`}
        onClick={onSelect}
      >
        <span
          className="ep-row-num text-xs font-semibold tabular-nums"
          style={{ color: isActive ? 'var(--accent)' : 'var(--ink-3)' }}
        >
          {num}
        </span>

        <div>
          <div className="text-sm font-semibold" style={{ letterSpacing: '-0.01em' }}>
            {episode.name}
          </div>
        </div>

        <span
          className="ep-row-dur text-xs tabular-nums text-right"
          style={{ color: 'var(--ink-3)' }}
        >
          —
        </span>

        <button
          onClick={(e) => { e.stopPropagation(); onSelect() }}
          className="flex items-center justify-center rounded-full cursor-pointer transition-all duration-150"
          style={{
            width: 32,
            height: 32,
            border: isActive ? 'none' : '1.5px solid var(--border)',
            background: isActive ? 'var(--accent)' : 'transparent',
          }}
        >
          <svg
            viewBox="0 0 24 24"
            style={{ width: 12, height: 12, fill: isActive ? '#fff' : 'var(--ink-3)', marginLeft: 1.5 }}
          >
            <path d="M8 5v14l11-7z" />
          </svg>
        </button>
      </div>
    </>
  )
}
```

- [ ] **Step 3: Verify compilation**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/PodcasterSection.tsx frontend/src/components/EpisodeRow.tsx
git commit -m "feat: add mobile responsive layout for podcaster section and episode rows"
```

---

### Task 9: Delete old PodcastPlayer component and verify full build

**Files:**
- Delete: `frontend/src/components/PodcastPlayer.tsx`

- [ ] **Step 1: Delete the old PodcastPlayer**

```bash
rm frontend/src/components/PodcastPlayer.tsx
```

- [ ] **Step 2: Run full build**

```bash
cd frontend && npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 3: Commit**

```bash
git add -A frontend/src/components/PodcastPlayer.tsx
git commit -m "chore: remove old PodcastPlayer component"
```

---

### Task 10: Manual smoke test

- [ ] **Step 1: Start the dev server**

```bash
cd frontend && npm run dev
```

- [ ] **Step 2: Verify in browser**

Open `http://localhost:5173` and check:
- Warm cream background, Space Grotesk typography
- Topbar shows "ECHO — Podcasts" with Browse/Library links
- Podcaster sections render with avatar, name, categories, description, episode count
- Episode table has header row and episode rows
- Clicking an episode highlights it (amber background) and starts audio
- Floating player appears at bottom with controls
- Resize to mobile width (<=700px): layout collapses, tapping episode opens fullscreen player
- Vapi auto-starts when episode plays (check console for `[Vapi] call started`)

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: address smoke test issues"
```

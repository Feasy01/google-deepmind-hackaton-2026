import { useState, useRef, useCallback } from 'react'

interface PlayerBarProps {
  episodeName: string
  podcasterName: string
  imageUrl: string | null
  isPlaying: boolean
  currentTime: number
  duration: number
  onTogglePlay: () => void
  onSeek: (time: number) => void
  onSkip: (seconds: number) => void
  disabled?: boolean
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
  imageUrl,
  isPlaying,
  currentTime,
  duration,
  onTogglePlay,
  onSeek,
  onSkip,
  disabled,
}: PlayerBarProps) {
  const progress = duration > 0 ? (currentTime / duration) * 100 : 0
  const [scrubbing, setScrubbing] = useState(false)
  const progressRef = useRef<HTMLDivElement>(null)

  const handleProgressClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const rect = e.currentTarget.getBoundingClientRect()
      const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
      onSeek(pct * duration)
    },
    [onSeek, duration],
  )

  const handleScrubStart = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      setScrubbing(true)
      const onMove = (ev: MouseEvent) => {
        if (!progressRef.current) return
        const rect = progressRef.current.getBoundingClientRect()
        const pct = Math.max(0, Math.min(1, (ev.clientX - rect.left) / rect.width))
        onSeek(pct * duration)
      }
      const onUp = () => {
        setScrubbing(false)
        window.removeEventListener('mousemove', onMove)
        window.removeEventListener('mouseup', onUp)
      }
      window.addEventListener('mousemove', onMove)
      window.addEventListener('mouseup', onUp)
      // Seek to click position immediately
      handleProgressClick(e)
    },
    [onSeek, duration, handleProgressClick],
  )

  return (
    <>
      <style>{`
        .player-bar {
          position: fixed;
          bottom: 1.5rem;
          left: 50%;
          display: flex;
          align-items: center;
          gap: 1rem;
          width: min(600px, calc(100% - 3rem));
          background: var(--player-bg);
          color: #f0ebe3;
          border-radius: 10px;
          padding: 1rem 1.25rem;
          box-shadow: 0 8px 32px rgba(44,36,24,0.22);
          z-index: 200;
          animation: slide-up-player 500ms var(--ease-out-expo) both;
        }
        @media (max-width: 767px) { .player-bar { display: none; } }

        /* Progress bar */
        .player-progress {
          position: absolute;
          left: 1rem;
          right: 1rem;
          bottom: 0;
          height: 3px;
          background: var(--player-surface);
          border-radius: 2px;
          cursor: pointer;
          transition: height 200ms var(--ease-out-quart);
        }
        .player-progress:hover,
        .player-progress.is-scrubbing {
          height: 6px;
        }
        .player-progress-fill {
          height: 100%;
          background: var(--accent);
          border-radius: 2px;
          position: relative;
          transition: width 100ms linear;
        }
        /* Scrub handle */
        .player-progress-fill::after {
          content: '';
          position: absolute;
          right: -5px;
          top: 50%;
          transform: translateY(-50%) scale(0);
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: var(--accent);
          box-shadow: 0 0 6px rgba(180,83,9,0.4);
          transition: transform 200ms var(--ease-out-quart);
        }
        .player-progress:hover .player-progress-fill::after,
        .player-progress.is-scrubbing .player-progress-fill::after {
          transform: translateY(-50%) scale(1);
        }

        /* Control buttons */
        .player-ctrl {
          background: none;
          border: none;
          color: #a89882;
          cursor: pointer;
          display: flex;
          align-items: center;
          transition: color 150ms, transform 100ms var(--ease-out-quart);
        }
        .player-ctrl:hover { color: #f0ebe3; }
        .player-ctrl:active { transform: scale(0.9); }

        .player-play {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background: var(--accent);
          border: none;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: transform 150ms var(--ease-out-quart), box-shadow 150ms;
        }
        .player-play:hover { transform: scale(1.1); box-shadow: 0 0 16px rgba(180,83,9,0.35); }
        .player-play:active { transform: scale(0.95); }
        .player-play:disabled { opacity: 0.5; pointer-events: none; }
        .player-play.is-connecting {
          animation: pulse-accent 1.2s infinite;
        }

        .player-connecting-label {
          font-size: 0.6rem;
          color: var(--accent);
          font-weight: 500;
          letter-spacing: 0.04em;
          animation: pulse-accent 1.2s infinite;
          white-space: nowrap;
        }

        /* Thumbnail entrance */
        .player-thumb {
          width: 40px;
          height: 40px;
          border-radius: 6px;
          object-fit: cover;
          flex-shrink: 0;
          animation: fade-in 300ms var(--ease-out-quart) both;
        }
      `}</style>

      <div className="player-bar">
        {imageUrl && (
          <img src={imageUrl} alt={episodeName} className="player-thumb" />
        )}

        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium truncate" style={{ fontSize: '0.82rem' }}>
            {episodeName}
          </div>
          <div style={{ fontSize: '0.7rem', color: '#a89882', marginTop: '0.1rem' }}>
            {podcasterName}
          </div>
        </div>

        <span
          className="whitespace-nowrap tabular-nums"
          style={{ fontSize: '0.65rem', color: '#7a6c58' }}
        >
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>

        <div className="flex items-center gap-4">
          <button className="player-ctrl" onClick={() => onSkip(-15)}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M1 4v6h6" /><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
            </svg>
          </button>

          {disabled && <span className="player-connecting-label">Connecting...</span>}
          <button className={`player-play ${disabled ? 'is-connecting' : ''}`} onClick={onTogglePlay} disabled={disabled}>
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

          <button className="player-ctrl" onClick={() => onSkip(15)}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M23 4v6h-6" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
            </svg>
          </button>
        </div>

        <div
          ref={progressRef}
          className={`player-progress ${scrubbing ? 'is-scrubbing' : ''}`}
          onMouseDown={handleScrubStart}
        >
          <div className="player-progress-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>
    </>
  )
}

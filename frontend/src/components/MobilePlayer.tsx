import { useRef, useCallback, useState } from 'react'

interface MobilePlayerProps {
  isOpen: boolean
  onClose: () => void
  episodeName: string
  podcasterName: string
  initials: string
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

export function MobilePlayer({
  isOpen,
  onClose,
  episodeName,
  podcasterName,
  initials,
  imageUrl,
  isPlaying,
  currentTime,
  duration,
  onTogglePlay,
  onSeek,
  onSkip,
  disabled,
}: MobilePlayerProps) {
  const progress = duration > 0 ? (currentTime / duration) * 100 : 0
  const [closing, setClosing] = useState(false)
  const [dragY, setDragY] = useState(0)
  const dragStartY = useRef(0)
  const isDragging = useRef(false)
  const panelRef = useRef<HTMLDivElement>(null)

  const handleClose = useCallback(() => {
    setClosing(true)
    setTimeout(() => {
      setClosing(false)
      setDragY(0)
      onClose()
    }, 300)
  }, [onClose])

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    dragStartY.current = e.touches[0].clientY
    isDragging.current = false
  }, [])

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    const dy = e.touches[0].clientY - dragStartY.current
    if (dy > 0) {
      isDragging.current = true
      setDragY(dy)
    }
  }, [])

  const handleTouchEnd = useCallback(() => {
    if (dragY > 120) {
      handleClose()
    } else {
      setDragY(0)
    }
    isDragging.current = false
  }, [dragY, handleClose])

  if (!isOpen && !closing) return null

  const dragOpacity = dragY > 0 ? Math.max(0.3, 1 - dragY / 400) : 1

  return (
    <>
      <style>{`
        .mobile-backdrop {
          position: fixed;
          inset: 0;
          background: rgba(44,36,24,0.6);
          z-index: 299;
          animation: fade-in 300ms var(--ease-out-quart) both;
        }
        .mobile-backdrop.is-closing {
          opacity: 0;
          transition: opacity 250ms var(--ease-out-quart);
        }

        .mobile-panel {
          position: fixed;
          inset: 0;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          background: var(--player-bg);
          color: #f0ebe3;
          z-index: 300;
          animation: slide-up-mobile 400ms var(--ease-out-expo) both;
          will-change: transform;
        }
        .mobile-panel.is-closing {
          transform: translateY(100%);
          transition: transform 300ms var(--ease-out-quart);
        }

        .mobile-drag-handle {
          width: 36px;
          height: 4px;
          border-radius: 2px;
          background: #7a6c58;
          margin: 0.5rem auto 0;
          opacity: 0.5;
        }

        .mobile-ctrl {
          background: none;
          border: none;
          color: #a89882;
          cursor: pointer;
          display: flex;
          align-items: center;
          transition: color 150ms, transform 100ms var(--ease-out-quart);
        }
        .mobile-ctrl:active { transform: scale(0.85); color: #f0ebe3; }

        .mobile-play {
          width: 56px;
          height: 56px;
          border-radius: 50%;
          background: var(--accent);
          border: none;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: transform 150ms var(--ease-out-quart), box-shadow 200ms;
        }
        .mobile-play:active { transform: scale(0.92); }
        .mobile-play:disabled { opacity: 0.5; pointer-events: none; }
        .mobile-play.is-connecting {
          animation: pulse-accent 1.2s infinite;
        }
        .mobile-connecting-label {
          font-size: 0.72rem;
          color: var(--accent);
          font-weight: 500;
          letter-spacing: 0.04em;
          animation: pulse-accent 1.2s infinite;
        }

        .mobile-progress {
          width: 100%;
          height: 4px;
          background: var(--player-surface);
          border-radius: 2px;
          cursor: pointer;
          transition: height 150ms var(--ease-out-quart);
        }
        .mobile-progress:active { height: 8px; }
        .mobile-progress-fill {
          height: 100%;
          background: var(--accent);
          border-radius: 2px;
          position: relative;
          transition: width 100ms linear;
        }
        .mobile-progress-fill::after {
          content: '';
          position: absolute;
          right: -6px;
          top: 50%;
          transform: translateY(-50%);
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: var(--accent);
          box-shadow: 0 0 8px rgba(180,83,9,0.4);
        }

        .mobile-artwork {
          animation: fade-in-up 500ms var(--ease-out-expo) 100ms both;
        }
        .mobile-info {
          animation: fade-in-up 500ms var(--ease-out-expo) 200ms both;
        }
        .mobile-controls-group {
          animation: fade-in-up 500ms var(--ease-out-expo) 300ms both;
        }

        @media (min-width: 768px) {
          .mobile-backdrop, .mobile-panel { display: none !important; }
        }
      `}</style>

      {/* Backdrop */}
      <div
        className={`mobile-backdrop ${closing ? 'is-closing' : ''}`}
        onClick={handleClose}
        style={{ opacity: dragOpacity }}
      />

      {/* Panel */}
      <div
        ref={panelRef}
        className={`mobile-panel ${closing ? 'is-closing' : ''}`}
        style={{
          transform: dragY > 0 ? `translateY(${dragY}px)` : undefined,
          transition: isDragging.current ? 'none' : undefined,
        }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {/* Drag handle */}
        <div className="mobile-drag-handle" />

        {/* Top bar */}
        <div className="flex items-center justify-between shrink-0" style={{ padding: '0.75rem 1.25rem' }}>
          <button className="mobile-ctrl" onClick={handleClose} style={{ fontFamily: 'inherit', fontSize: '0.8rem', fontWeight: 500, gap: '0.375rem' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5" /><path d="M12 19l-7-7 7-7" />
            </svg>
            Back
          </button>
          <span className="font-semibold uppercase" style={{ fontSize: '0.68rem', letterSpacing: '0.08em', color: '#7a6c58' }}>
            Now Playing
          </span>
        </div>

        {/* Body */}
        <div className="flex-1 flex flex-col items-center justify-center gap-8" style={{ padding: '2rem 2rem 1rem' }}>
          {/* Artwork */}
          <div className="mobile-artwork">
            {imageUrl ? (
              <img
                src={imageUrl}
                alt={episodeName}
                style={{
                  width: 'min(280px, 65vw)',
                  aspectRatio: '1',
                  objectFit: 'cover',
                  borderRadius: 14,
                  background: 'var(--player-surface)',
                }}
              />
            ) : (
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
            )}
          </div>

          {/* Info */}
          <div className="text-center mobile-info">
            <div className="font-semibold" style={{ fontSize: '1.25rem', letterSpacing: '-0.02em' }}>
              {episodeName}
            </div>
            <div style={{ fontSize: '0.85rem', color: '#a89882', marginTop: '0.3rem' }}>
              {podcasterName}
            </div>
          </div>

          {/* Progress */}
          <div className="w-full mobile-controls-group" style={{ maxWidth: 360 }}>
            <div
              className="mobile-progress"
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect()
                const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
                onSeek(pct * duration)
              }}
            >
              <div className="mobile-progress-fill" style={{ width: `${progress}%` }} />
            </div>
            <div
              className="flex justify-between tabular-nums"
              style={{ marginTop: '0.4rem', fontSize: '0.68rem', color: '#7a6c58' }}
            >
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>

          {/* Connecting indicator */}
          {disabled && (
            <div className="mobile-connecting-label" style={{ marginTop: '-0.5rem' }}>
              Connecting to assistant...
            </div>
          )}

          {/* Controls */}
          <div className="flex items-center gap-8 mobile-controls-group" style={{ paddingBottom: '1rem' }}>
            <button className="mobile-ctrl" onClick={() => onSkip(-15)}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M1 4v6h6" /><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
              </svg>
            </button>

            <button className={`mobile-play ${disabled ? 'is-connecting' : ''}`} onClick={onTogglePlay} disabled={disabled}>
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

            <button className="mobile-ctrl" onClick={() => onSkip(15)}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M23 4v6h-6" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

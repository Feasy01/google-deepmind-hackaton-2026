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
  if (!isOpen) return null

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <div
      className="fixed inset-0 flex flex-col overflow-hidden md:!hidden"
      style={{ background: 'var(--player-bg)', color: '#f0ebe3', zIndex: 300 }}
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
            disabled={disabled}
            className="flex items-center justify-center rounded-full cursor-pointer transition-transform duration-100 hover:scale-105"
            style={{
              width: 56,
              height: 56,
              background: 'var(--accent)',
              border: 'none',
              ...(disabled ? { opacity: 0.5, pointerEvents: 'none' as const } : {}),
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

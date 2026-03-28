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
      className="fixed bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-4 max-md:hidden"
      style={{
        width: 'min(600px, calc(100% - 3rem))',
        background: 'var(--player-bg)',
        color: '#f0ebe3',
        borderRadius: 10,
        padding: '1rem 1.25rem',
        boxShadow: '0 8px 32px rgba(44,36,24,0.22)',
        zIndex: 200,
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

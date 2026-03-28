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

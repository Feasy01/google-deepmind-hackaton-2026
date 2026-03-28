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
          transition: background 180ms var(--ease-out-quart), transform 100ms var(--ease-out-quart);
          position: relative;
        }
        .ep-row::before {
          content: '';
          position: absolute;
          left: 0;
          top: 0;
          bottom: 0;
          width: 3px;
          background: var(--accent);
          border-radius: 0 2px 2px 0;
          transform: scaleY(0);
          transition: transform 250ms var(--ease-out-expo);
        }
        .ep-row.ep-active::before { transform: scaleY(1); }
        .ep-row:hover { background: var(--surface); }
        .ep-row:active { transform: scale(0.995); }
        .ep-row.ep-active { background: var(--accent-bg); }
        .ep-row.ep-active:hover { background: var(--accent-bg); }
        .ep-row-num { display: block; }
        .ep-row-dur { display: block; }

        /* Play button */
        .ep-play-btn {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: transform 150ms var(--ease-out-quart),
                      background 180ms var(--ease-out-quart),
                      border-color 180ms var(--ease-out-quart),
                      box-shadow 200ms;
        }
        .ep-play-btn:hover {
          transform: scale(1.12);
          box-shadow: 0 0 12px rgba(180,83,9,0.2);
        }
        .ep-play-btn:active { transform: scale(0.9); }
        .ep-play-btn.is-active {
          background: var(--accent);
          border: none;
        }
        .ep-play-btn.is-active:hover {
          box-shadow: 0 0 16px rgba(180,83,9,0.35);
        }
        .ep-play-btn:not(.is-active) {
          background: transparent;
          border: 1.5px solid var(--border);
        }
        .ep-play-btn:not(.is-active):hover {
          border-color: var(--accent);
          background: rgba(180,83,9,0.06);
        }

        @media (max-width: 700px) {
          .ep-row {
            grid-template-columns: 1fr 48px;
            padding: 0.85rem 0;
            gap: 0.75rem;
          }
          .ep-row::before { display: none; }
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
          className={`ep-play-btn ${isActive ? 'is-active' : ''}`}
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

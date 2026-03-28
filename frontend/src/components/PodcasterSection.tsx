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

# Echo — Warm Theme Frontend Redesign

## Summary

Replace the existing dark-themed, tab-based frontend (Chat / Voice / Podcast) with a light, warm-cream themed podcast app using the 2B Warm mockup. The AI assistant auto-arms when a podcast plays — no manual toggle.

## Scope

### Remove
- `components/Chat.tsx`
- `components/VoiceChat.tsx`
- `api/chat.ts`

### Keep & adapt
- `hooks/useAudioPlayer.ts` — no changes needed
- `hooks/usePodcastVapi.ts` — no changes needed, called automatically on play
- `api/podcast.ts` — update types to match actual backend response

### New / rewrite
| File | Purpose |
|------|---------|
| `App.tsx` | Top-level layout, fetches podcasters, manages selected episode state |
| `components/PodcasterSection.tsx` | Two-panel layout for one podcaster (sidebar + episode table) |
| `components/EpisodeRow.tsx` | Single episode row in the table |
| `components/PlayerBar.tsx` | Floating dark pill player (desktop, >=701px) |
| `components/MobilePlayer.tsx` | Fullscreen overlay player (mobile, <=700px) |
| `index.css` | Warm theme CSS variables, base styles, Google Fonts import |
| `index.html` | Update title to "Echo", add Google Fonts preconnect |

## API Layer

### Backend shape (GET `/api/podcast/`)

```ts
interface Episode {
  id: string
  name: string
  filename: string
}

interface Podcaster {
  podcaster: string
  categories: string[]
  description: string
  episodes: Episode[]
}
```

Response: `Podcaster[]`

### Audio URL

```
/api/podcast/{podcaster}/{episodeId}/audio
```

Update `getPodcastAudioUrl` to accept both podcaster and episodeId.

## App State

```ts
// In App.tsx
const [selected, setSelected] = useState<{
  podcaster: string
  episodeId: string
  episodeName: string
} | null>(null)
```

- `podcasters` — fetched via react-query
- `selected` — which episode is active (null = nothing playing, player hidden)

Audio player and Vapi hooks live in App.tsx so the player bar and mobile player can access them.

## Auto-Arming AI Assistant

When the user clicks play on an episode:
1. `useAudioPlayer.play(url)` starts audio
2. `usePodcastVapi.startCall()` fires automatically — no user action needed
3. Vapi is in always-listening mode by default

Switching episodes:
1. `audio.stop()` + `vapi.endCall()` + `vapi.clearTranscript()`
2. Set new selected episode
3. Start new audio + new Vapi call

Pausing audio does NOT end the Vapi call — assistant stays ready.

## Desktop Layout (>700px)

### Topbar (sticky)
- Left: `ECHO — Podcasts` (ECHO bold uppercase, "— Podcasts" lighter)
- Right: "Browse" / "Library" links (decorative, non-functional for now)
- Bottom border: 2px solid `--ink`

### Per podcaster section
- Top border: 2px solid `--ink` as section divider
- Two-panel grid: `280px | 1fr`
- **Left panel** (sticky at top:70px):
  - Square avatar placeholder with initials (Newsreader italic)
  - Podcaster name (bold)
  - Categories joined with middot
  - Description text
  - Episode count label
- **Right panel**:
  - Header row: #, Title, Duration, (play col)
  - Episode rows: number, title + description, duration, circular play button
  - Active row: amber background `--accent-bg`, red number, filled play button
  - Hover row: `--surface` background

### Player bar
- Fixed bottom, centered, max-width 600px
- Dark background (`--player-bg: #2c2418`)
- Contents: episode info (title + artist), time display, rewind/play/forward, progress bar
- Hidden when no episode selected
- Hidden on mobile

## Mobile Layout (<=700px)

### Browsing (default)
- Single column, no two-panel grid
- Podcaster header: compact row (64px avatar + name/tag inline)
- Hide: bio, episode count, table header, episode numbers, durations, descriptions
- Episode rows: just title + play button
- No player bar shown

### Playing (fullscreen overlay)
- Opens when tapping an episode row on mobile
- Covers entire screen (`position: fixed; inset: 0`)
- Dark background matching player-bg
- Contents (vertically centered):
  - Back button + "Now Playing" label at top
  - Large artwork placeholder (280px square)
  - Episode title, artist, description
  - Progress bar with time labels
  - Large rewind / play / forward controls
- Dismissed via Back button → returns to library
- Hidden on desktop (`display: none !important` at >=701px)

## Theme

### CSS Variables
```css
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
```

### Typography
- UI: Space Grotesk (400, 500, 600, 700)
- Display / avatars: Newsreader (italic 400)
- Loaded via Google Fonts in `index.html`

### Styling approach
- CSS variables for theme tokens
- Tailwind v4 for utility classes
- Component-specific styles via Tailwind classes inline (matching existing codebase pattern)

## Component Details

### `App.tsx`
- Fetches `podcasters` via react-query
- Owns `selected` state, `useAudioPlayer`, `usePodcastVapi`
- Renders: Topbar → PodcasterSection (for each podcaster) → PlayerBar → MobilePlayer
- Handles `selectEpisode(podcaster, episode)` — stops old, starts new audio+vapi
- Handles `togglePlayPause()`, `seek()`, skip forward/back 15s

### `PodcasterSection.tsx`
Props: `podcaster: Podcaster`, `selectedEpisodeId: string | null`, `onSelectEpisode: (ep) => void`
- Renders the two-panel grid with sidebar and episode table
- Each row calls `onSelectEpisode` on click

### `EpisodeRow.tsx`
Props: `episode: Episode`, `index: number`, `isActive: boolean`, `onSelect: () => void`
- Single table row with number, title, description (placeholder), duration (placeholder), play button

### `PlayerBar.tsx`
Props: audio state (isPlaying, currentTime, duration), episode info, control callbacks
- Only renders when an episode is selected
- Hidden on mobile via CSS

### `MobilePlayer.tsx`
Props: same as PlayerBar + `isOpen: boolean`, `onClose: () => void`, podcaster info
- Fullscreen overlay, only shown on mobile when `isOpen` is true
- Back button calls `onClose`

## What this spec does NOT cover
- Routing (single page, no router needed)
- Real podcast metadata (descriptions, durations) — placeholders for now
- Browse/Library navigation — decorative links only
- Podcast artwork images — initials placeholders only

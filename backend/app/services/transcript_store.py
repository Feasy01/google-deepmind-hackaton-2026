"""In-memory transcript store.

Loads all .txt transcript files at startup and keeps them in RAM.
Provides fast lookup of ~30s transcript windows by episode_id + timestamp.
"""

import logging
import pathlib
import re

from app.core.config import settings

logger = logging.getLogger("transcript_store")

_TIMESTAMP_RE = re.compile(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$")


def _parse_timestamp(ts: str) -> int | None:
    """Convert 'H:MM', 'MM:SS', or 'HH:MM:SS' to total seconds."""
    m = _TIMESTAMP_RE.match(ts.strip())
    if not m:
        return None
    parts = [int(p) for p in m.groups() if p is not None]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    # For M:SS or H:MM — treat as M:SS (matches the podcast format)
    return parts[0] * 60 + parts[1]


class TranscriptSegment:
    __slots__ = ("start_seconds", "text")

    def __init__(self, start_seconds: int, text: str):
        self.start_seconds = start_seconds
        self.text = text


class TranscriptStore:
    """Keeps all parsed transcripts in memory, keyed by episode_id."""

    def __init__(self):
        self._store: dict[str, list[TranscriptSegment]] = {}

    @property
    def loaded_episodes(self) -> list[str]:
        return list(self._store.keys())

    def load_all(self) -> None:
        """Scan MEDIA_DIR for .txt transcript files and load them all."""
        media = pathlib.Path(settings.MEDIA_DIR)
        if not media.exists():
            logger.warning("MEDIA_DIR %s does not exist, no transcripts loaded", media)
            return

        count = 0
        for podcaster_dir in sorted(media.iterdir()):
            if not podcaster_dir.is_dir() or podcaster_dir.name == "articles":
                continue
            for txt_file in sorted(podcaster_dir.glob("*.txt")):
                if txt_file.name == "podcast.txt":
                    continue
                episode_id = txt_file.stem
                segments = self._parse_transcript(txt_file)
                if segments:
                    self._store[episode_id] = segments
                    count += 1
                    logger.debug("Loaded transcript: %s (%d segments)", episode_id, len(segments))

        logger.info("Transcript store loaded: %d episodes", count)

    @staticmethod
    def _parse_transcript(path: pathlib.Path) -> list[TranscriptSegment]:
        """Parse a transcript .txt file into timestamped segments."""
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        segments: list[TranscriptSegment] = []
        current_ts: int | None = None
        current_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            ts = _parse_timestamp(stripped)
            if ts is not None:
                # Save previous segment
                if current_ts is not None and current_lines:
                    segments.append(TranscriptSegment(current_ts, " ".join(current_lines)))
                current_ts = ts
                current_lines = []
            elif stripped:
                current_lines.append(stripped)

        # Last segment
        if current_ts is not None and current_lines:
            segments.append(TranscriptSegment(current_ts, " ".join(current_lines)))

        return segments

    def get_context(self, episode_id: str, timestamp_seconds: int, window_seconds: int = 30) -> str:
        """Get ~window_seconds of transcript text around the given timestamp.

        Returns the concatenated text of all segments whose start time falls
        within [timestamp - window_seconds, timestamp].
        """
        segments = self._store.get(episode_id)
        if not segments:
            logger.warning("No transcript in store for episode_id=%s", episode_id)
            return ""

        window_start = max(0, timestamp_seconds - window_seconds)
        window_end = timestamp_seconds

        matching = [
            seg for seg in segments
            if window_start <= seg.start_seconds <= window_end
        ]

        if not matching:
            # Fallback: find the single closest segment
            closest = min(segments, key=lambda s: abs(s.start_seconds - timestamp_seconds))
            logger.debug("get_context: no segments in window, using closest at %ds", closest.start_seconds)
            return closest.text

        result = " ".join(seg.text for seg in matching)
        logger.debug(
            "get_context: episode=%s ts=%ds window=[%d,%d] matched=%d segments, %d chars",
            episode_id, timestamp_seconds, window_start, window_end, len(matching), len(result),
        )
        return result


transcript_store = TranscriptStore()

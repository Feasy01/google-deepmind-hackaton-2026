import pathlib

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings

router = APIRouter()


def _media_dir() -> pathlib.Path:
    return pathlib.Path(settings.MEDIA_DIR)


@router.get("/")
async def list_podcasts():
    """List available podcasts by scanning MEDIA_DIR for .mp3 files."""
    media = _media_dir()
    if not media.exists():
        return []

    podcasts = []
    for f in sorted(media.glob("*.mp3")):
        podcasts.append(
            {
                "id": f.stem,
                "filename": f.name,
            }
        )
    return podcasts


@router.get("/{podcast_id}/audio")
async def get_podcast_audio(podcast_id: str):
    """Serve an MP3 file. Supports range requests for seeking."""
    # Prevent path traversal
    if "/" in podcast_id or "\\" in podcast_id or ".." in podcast_id:
        raise HTTPException(status_code=400, detail="Invalid podcast ID")

    path = _media_dir() / f"{podcast_id}.mp3"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Podcast not found")

    return FileResponse(
        path=str(path),
        media_type="audio/mpeg",
        filename=path.name,
    )

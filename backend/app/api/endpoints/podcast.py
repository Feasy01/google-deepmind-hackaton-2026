import json
import pathlib

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings

router = APIRouter()


def _media_dir() -> pathlib.Path:
    return pathlib.Path(settings.MEDIA_DIR)


def _parse_podcast_txt(path: pathlib.Path) -> dict:
    """Parse a podcast.txt file: line 1 = display name, line 2 = categories, line 3 = description."""
    if not path.exists():
        return {"name": None, "categories": [], "description": ""}
    lines = path.read_text().strip().splitlines()
    name = lines[0].strip() if lines else None
    categories = [c.strip() for c in lines[1].split("·")] if len(lines) > 1 else []
    description = lines[2].strip() if len(lines) > 2 else ""
    return {"name": name, "categories": categories, "description": description}


def _parse_episode_filename(filename: str) -> dict:
    """Parse '{podcast_id}-{name}.mp3' into id and display name."""
    stem = pathlib.Path(filename).stem
    dash_idx = stem.find("-")
    if dash_idx == -1:
        return {"id": stem, "name": stem}
    podcast_id = stem[: dash_idx]
    name = stem[dash_idx + 1 :].replace("-", " ").title()
    return {"id": stem, "name": name}


def _find_cover_image(podcaster_dir: pathlib.Path) -> str | None:
    """Find a cover image (webp/png/jpg) that doesn't match an episode filename."""
    episode_stems = {f.stem for f in podcaster_dir.glob("*.mp3")}
    for ext in ("*.webp", "*.png", "*.jpg", "*.jpeg"):
        for img in podcaster_dir.glob(ext):
            if img.stem not in episode_stems:
                return img.name
    return None


def _find_episode_image(podcaster_dir: pathlib.Path, episode_id: str) -> str | None:
    """Find an image file matching the episode id stem."""
    for ext in (".webp", ".png", ".jpg", ".jpeg"):
        img = podcaster_dir / f"{episode_id}{ext}"
        if img.exists():
            return img.name
    return None


@router.get("/")
async def list_podcasters():
    """List all podcasters and their episodes by scanning MEDIA_DIR subdirectories."""
    media = _media_dir()
    if not media.exists():
        return []

    podcasters = []
    for podcaster_dir in sorted(media.iterdir()):
        if not podcaster_dir.is_dir() or podcaster_dir.name == "articles":
            continue

        meta = _parse_podcast_txt(podcaster_dir / "podcast.txt")
        cover = _find_cover_image(podcaster_dir)
        episodes = []
        for f in sorted(podcaster_dir.glob("*.mp3")):
            ep = _parse_episode_filename(f.name)
            episodes.append(
                {
                    "id": ep["id"],
                    "name": ep["name"],
                    "filename": f.name,
                }
            )

        podcasters.append(
            {
                "podcaster": podcaster_dir.name,
                "name": meta["name"] or podcaster_dir.name,
                "categories": meta["categories"],
                "description": meta["description"],
                "cover": cover,
                "episodes": episodes,
            }
        )

    return podcasters


def _validate_path_part(*parts: str) -> None:
    for part in parts:
        if "/" in part or "\\" in part or ".." in part:
            raise HTTPException(status_code=400, detail="Invalid path")


def _get_podcaster_dir(podcaster: str) -> pathlib.Path:
    _validate_path_part(podcaster)
    d = _media_dir() / podcaster
    if not d.is_dir():
        raise HTTPException(status_code=404, detail="Podcaster not found")
    return d


@router.get("/{podcaster}")
async def get_podcaster(podcaster: str):
    """Get a single podcaster's metadata and episode list."""
    podcaster_dir = _get_podcaster_dir(podcaster)
    meta = _parse_podcast_txt(podcaster_dir / "podcast.txt")
    cover = _find_cover_image(podcaster_dir)
    episodes = []
    for f in sorted(podcaster_dir.glob("*.mp3")):
        ep = _parse_episode_filename(f.name)
        episodes.append({"id": ep["id"], "name": ep["name"], "filename": f.name})

    return {
        "podcaster": podcaster_dir.name,
        "name": meta["name"] or podcaster_dir.name,
        "categories": meta["categories"],
        "description": meta["description"],
        "cover": cover,
        "episodes": episodes,
    }


_IMAGE_MEDIA_TYPES = {
    ".webp": "image/webp",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


@router.get("/{podcaster}/image/{filename}")
async def get_image(podcaster: str, filename: str):
    """Serve an image file (webp/png/jpg) from a podcaster directory."""
    _validate_path_part(podcaster, filename)
    path = _get_podcaster_dir(podcaster) / filename
    suffix = path.suffix.lower()
    if suffix not in _IMAGE_MEDIA_TYPES:
        raise HTTPException(status_code=400, detail="Not a supported image format")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(
        path=str(path),
        media_type=_IMAGE_MEDIA_TYPES[suffix],
        filename=path.name,
    )


@router.get("/{podcaster}/{episode_id}")
async def get_episode(podcaster: str, episode_id: str):
    """Get episode metadata: name, whether transcript is available."""
    _validate_path_part(podcaster, episode_id)
    podcaster_dir = _get_podcaster_dir(podcaster)

    mp3_path = podcaster_dir / f"{episode_id}.mp3"
    if not mp3_path.exists():
        raise HTTPException(status_code=404, detail="Episode not found")

    ep = _parse_episode_filename(mp3_path.name)
    json_path = podcaster_dir / f"{episode_id}.json"
    image = _find_episode_image(podcaster_dir, episode_id)

    return {
        "id": ep["id"],
        "name": ep["name"],
        "podcaster": podcaster,
        "has_transcript": json_path.exists(),
        "image": image,
    }


@router.get("/{podcaster}/{episode_id}/audio")
async def get_podcast_audio(podcaster: str, episode_id: str):
    """Serve an MP3 file from a podcaster directory."""
    _validate_path_part(podcaster, episode_id)
    path = _get_podcaster_dir(podcaster) / f"{episode_id}.mp3"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Episode not found")

    return FileResponse(
        path=str(path),
        media_type="audio/mpeg",
        filename=path.name,
    )


@router.get("/{podcaster}/{episode_id}/transcript")
async def get_episode_transcript(podcaster: str, episode_id: str):
    """Return the parsed transcript (timestamps + text) for an episode."""
    _validate_path_part(podcaster, episode_id)
    json_path = _get_podcaster_dir(podcaster) / f"{episode_id}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Transcript not found")

    data = json.loads(json_path.read_text())
    return {
        "episode_id": episode_id,
        "title": data.get("title", ""),
        "speaker": data.get("speaker", ""),
        "source": data.get("source", ""),
        "transcript": data.get("transcript", []),
    }

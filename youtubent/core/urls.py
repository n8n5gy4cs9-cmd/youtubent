import re
from urllib.parse import parse_qs, urlparse

_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extract_video_id(text: str) -> str | None:
    """Return the 11-char YouTube id from watch/youtu.be/shorts/embed/live URLs (or a bare id)."""
    text = text.strip()
    if _ID.match(text):
        return text
    if "://" not in text:
        text = "https://" + text
    u = urlparse(text)
    host = (u.hostname or "").lower().removeprefix("www.").removeprefix("m.")
    if host == "youtu.be":
        cand = u.path.lstrip("/").split("/")[0]
    elif host in ("youtube.com", "music.youtube.com", "youtube-nocookie.com"):
        parts = [p for p in u.path.split("/") if p]
        if u.path.startswith("/watch"):
            cand = parse_qs(u.query).get("v", [""])[0]
        elif len(parts) >= 2 and parts[0] in ("shorts", "embed", "live", "v"):
            cand = parts[1]
        else:
            return None
    else:
        return None
    return cand if _ID.match(cand) else None


def watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"

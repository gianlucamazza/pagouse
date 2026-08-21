"""Origin gates. Scheme blocks are shipped; origin tokens come from user config."""

from __future__ import annotations

from urllib.parse import urlparse

from pagouse.config import Config, load_config
from pagouse.errors import Denied

# Browser-internal documents. Not a site catalog — the page agent equivalent
# of refusing Super+ key combos on the seat.
BLOCKED_SCHEMES = frozenset(
    {
        "chrome",
        "chrome-extension",
        "chrome-search",
        "chrome-untrusted",
        "about",
        "file",
        "devtools",
        "data",
        "javascript",
        "view-source",
        "edge",
        "brave",
    }
)


def origin_of(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme:
        return ""
    if parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return f"{parsed.scheme}:"


def scheme_blocked(url: str) -> bool:
    scheme = (urlparse(url).scheme or "").lower()
    return scheme in BLOCKED_SCHEMES or not scheme.startswith("http")


def origin_permitted(url: str, config: Config | None = None) -> bool:
    """True when this URL may be targeted. Scheme blocks always apply."""
    if scheme_blocked(url):
        return False
    cfg = config if config is not None else load_config()
    origin = origin_of(url).lower().rstrip("/")
    deny = {item.lower().rstrip("/") for item in cfg.deny_origins}
    if origin in deny:
        return False
    if not cfg.allow_origins:
        return True
    allow = {item.lower().rstrip("/") for item in cfg.allow_origins}
    return origin in allow


def require_origin(url: str, config: Config | None = None) -> str:
    """Return the origin or raise Denied."""
    cfg = config if config is not None else load_config()
    if scheme_blocked(url):
        scheme = origin_of(url) or urlparse(url).scheme or "empty"
        raise Denied(f"refusing non-http(s) url ({scheme})")
    origin = origin_of(url)
    if not origin_permitted(url, cfg):
        raise Denied(f"origin not permitted: {origin}")
    return origin

"""Public per-track Newgrounds license inspector; it never downloads audio."""
from __future__ import annotations

import html
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def validate_track_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or parsed.netloc.lower() not in {"newgrounds.com", "www.newgrounds.com"}:
        raise ValueError("Use an HTTPS Newgrounds track URL")
    if not re.fullmatch(r"/audio/listen/\d+/?", parsed.path):
        raise ValueError("Use an individual Newgrounds Audio Portal track URL")
    return f"https://www.newgrounds.com{parsed.path.rstrip('/')}"


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def parse_track_page(track_url: str, page_html: str) -> dict:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", page_html, re.I | re.S)
    title = _clean(title_match.group(1)) if title_match else "Untitled Newgrounds track"
    marker = re.search(r"Licensing Terms", page_html, re.I)
    if not marker:
        terms = "Licensing terms were not found on the public page."
    else:
        remainder = page_html[marker.end():]
        boundary = re.search(r"<(?:h[1-6]|section|footer)[^>]*>|Credits\s*&amp;\s*Info", remainder, re.I)
        terms = _clean(remainder[:boundary.start()] if boundary else remainder[:8000])
    normalized = terms.lower()
    if "noncommercial" in normalized or "may not use this work for commercial" in normalized:
        commercial_status = "not_allowed"
    elif "specific arrangements" in normalized or "please contact me" in normalized or "contact me" in normalized:
        commercial_status = "artist_permission_required"
    elif "free to copy" in normalized and "attribution" in normalized:
        commercial_status = "allowed_with_attribution"
    else:
        commercial_status = "manual_review_required"
    return {"track_url": track_url, "title": title, "license_terms": terms[:4000], "commercial_status": commercial_status, "verified_at_source": track_url, "downloaded": False}


def inspect_track(track_url: str) -> dict:
    track_url = validate_track_url(track_url)
    request = Request(track_url, headers={"User-Agent": "ASTRA-License-Inspector/1.0 (+local property film rights review)"})
    with urlopen(request, timeout=20) as response:
        page_html = response.read().decode("utf-8", errors="replace")
    return parse_track_page(track_url, page_html)

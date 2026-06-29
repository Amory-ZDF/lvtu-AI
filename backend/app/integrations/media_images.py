from __future__ import annotations

import logging
from typing import Any, Protocol
from urllib.parse import quote

import httpx

from app.schemas.planning import ImageResource

logger = logging.getLogger(__name__)


class ImageLookup(Protocol):
    def find(self, *, query: str, category: str, alt: str) -> ImageResource | None:
        """Return a real remote image for the query, or None when no safe match exists."""


class WikimediaImageLookup:
    """Small no-key image lookup for product MVP.

    It only returns remote Wikimedia/Wikipedia image URLs and never downloads image files
    into the repository. Callers should keep a local generated-card fallback because image
    coverage varies by city and POI.
    """

    def __init__(self, timeout_seconds: float = 2.0) -> None:
        self.timeout_seconds = timeout_seconds
        self._cache: dict[str, ImageResource | None] = {}

    def find(self, *, query: str, category: str, alt: str) -> ImageResource | None:
        normalized = " ".join(query.split())
        if not normalized:
            return None
        cache_key = f"{category}:{normalized}"
        if cache_key not in self._cache:
            self._cache[cache_key] = self._find_uncached(
                query=normalized,
                category=category,
                alt=alt,
            )
        return self._cache[cache_key]

    def _find_uncached(self, *, query: str, category: str, alt: str) -> ImageResource | None:
        try:
            title_queries = [query]
            if category == "destination" and not query.endswith(("市", "州", "县", "区")):
                title_queries.insert(0, f"{query}市")
            for title_query in title_queries:
                image = self._from_zh_wikipedia_title(title_query, category, alt)
                if image:
                    return image
            return self._from_zh_wikipedia_search(query, category, alt) or self._from_commons(
                query,
                category,
                alt,
            )
        except httpx.HTTPError as exc:
            logger.info("Wikimedia image lookup failed for %s: %s", query, exc)
            return None

    def _from_zh_wikipedia_title(
        self,
        query: str,
        category: str,
        alt: str,
    ) -> ImageResource | None:
        data = self._get_json(
            "https://zh.wikipedia.org/w/api.php",
            {
                "action": "query",
                "titles": query,
                "prop": "pageimages",
                "piprop": "thumbnail|original|name",
                "pithumbsize": 960,
                "redirects": 1,
                "format": "json",
                "origin": "*",
            },
        )
        pages = (data.get("query") or {}).get("pages") or {}
        return self._first_page_image(
            pages=list(pages.values()),
            query=query,
            category=category,
            alt=alt,
        )

    def _from_zh_wikipedia_search(
        self,
        query: str,
        category: str,
        alt: str,
    ) -> ImageResource | None:
        data = self._get_json(
            "https://zh.wikipedia.org/w/api.php",
            {
                "action": "query",
                "generator": "search",
                "gsrsearch": query,
                "gsrlimit": 5,
                "prop": "pageimages",
                "piprop": "thumbnail|original|name",
                "pithumbsize": 960,
                "redirects": 1,
                "format": "json",
                "origin": "*",
            },
        )
        pages = (data.get("query") or {}).get("pages") or {}
        return self._first_page_image(
            pages=sorted(pages.values(), key=lambda item: item.get("index", 99)),
            query=query,
            category=category,
            alt=alt,
        )

    def _first_page_image(
        self,
        *,
        pages: list[dict[str, Any]],
        query: str,
        category: str,
        alt: str,
    ) -> ImageResource | None:
        for page in pages:
            thumbnail = page.get("thumbnail") or {}
            original = page.get("original") or {}
            image_url = thumbnail.get("source") or original.get("source")
            if not _is_usable_photo_url(str(image_url or "")):
                continue
            title = str(page.get("title") or query)
            return ImageResource(
                category=category,
                url=str(image_url),
                thumbnail_url=str(thumbnail.get("source") or image_url),
                alt=alt,
                provider="wikimedia-pageimage",
                placeholder=False,
                source_url=f"https://zh.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}",
                license="See Wikimedia source page",
                credit="Wikimedia contributors",
            )
        return None

    def _from_commons(self, query: str, category: str, alt: str) -> ImageResource | None:
        data = self._get_json(
            "https://commons.wikimedia.org/w/api.php",
            {
                "action": "query",
                "generator": "search",
                "gsrsearch": query,
                "gsrnamespace": 6,
                "gsrlimit": 8,
                "prop": "imageinfo",
                "iiprop": "url|mime|extmetadata",
                "iiurlwidth": 960,
                "format": "json",
                "origin": "*",
            },
        )
        pages = (data.get("query") or {}).get("pages") or {}
        for page in sorted(pages.values(), key=lambda item: item.get("index", 99)):
            image_info = (page.get("imageinfo") or [{}])[0]
            image_url = str(image_info.get("thumburl") or image_info.get("url") or "")
            mime = str(image_info.get("mime") or "")
            if mime not in {"image/jpeg", "image/png", "image/webp"}:
                continue
            if not _is_usable_photo_url(image_url):
                continue
            metadata = image_info.get("extmetadata") or {}
            return ImageResource(
                category=category,
                url=image_url,
                thumbnail_url=image_url,
                alt=alt,
                provider="wikimedia-commons",
                placeholder=False,
                source_url=str(image_info.get("descriptionurl") or ""),
                license=_metadata_value(metadata, "LicenseShortName"),
                credit=_metadata_value(metadata, "Artist")
                or _metadata_value(metadata, "Credit"),
            )
        return None

    def _get_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(
                url,
                params=params,
                headers={"User-Agent": "LvTravel/0.1 (https://lv.zdfamory.com/)"},
            )
            response.raise_for_status()
            return response.json()


def _metadata_value(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key) or {}
    text = str(value.get("value") or "").strip()
    return text or None


def _is_usable_photo_url(url: str) -> bool:
    if not url:
        return False
    lower = url.lower()
    if not lower.startswith("https://"):
        return False
    if ".svg" in lower:
        return False
    if not lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
        return False
    blocked_fragments = (
        "flag_of",
        "location_map",
        "map_",
        "_map",
        "subdivision",
        "seal_of",
        "coat_of_arms",
        "emblem",
        "logo",
        "icon",
    )
    return not any(fragment in lower for fragment in blocked_fragments)

"""TMDB (The Movie Database) API wrapper — movie discovery by mood/genre.

Uses the TMDB API to search movies and TV shows matching mood-based genre tags.
"""

from __future__ import annotations

import logging
from typing import Optional

from cinematic_mood_weaver.config import settings
from cinematic_mood_weaver.types.models import MovieRecommendation

logger = logging.getLogger(__name__)


class TMDBClient:
    """Wraps the TMDB API for mood-based movie and TV discovery."""

    def __init__(self):
        self._session: Optional[object] = None

    async def search_movies(
        self,
        query: str = "popular",
        genres: Optional[list[int]] = None,
        limit: int = 5,
    ) -> list[MovieRecommendation]:
        """Search for movies matching the given mood query.

        Falls back to dummy data when TMDB API key is not configured.
        """
        if not settings.tmdb_api_key:
            logger.info("TMDB API key not configured, returning dummy movies")
            return self._dummy_movies(query, limit)

        import aiohttp

        base = "https://api.themoviedb.org/3"
        headers = {"Authorization": f"Bearer {settings.tmdb_api_key}"}

        params = {"query": query, "include_adult": False, "language": "en-US", "page": 1}
        if genres:
            params["with_genres"] = ",".join(str(g) for g in genres)

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{base}/search/movie", params=params) as resp:
                if resp.status != 200:
                    logger.error(f"TMDB API error: {resp.status}")
                    return self._dummy_movies(query, limit)
                data = await resp.json()
                results = data.get("results", [])[:limit]

                return [
                    MovieRecommendation(
                        title=item.get("title", "Unknown"),
                        year=int(item.get("release_date", "2000")[:4]) if item.get("release_date") else 2000,
                        overview=item.get("overview", "")[:500],
                        poster_url=f"https://image.tmdb.org/t/p/w500{item['poster_path']}" if item.get("poster_path") else "",
                        tmdb_id=item.get("id", 0),
                        media_type="movie",
                        genre_ids=item.get("genre_ids", []),
                        vote_average=item.get("vote_average", 0.0),
                    )
                    for item in results
                ]

    def _dummy_movies(self, query: str, limit: int) -> list[MovieRecommendation]:
        """Return dummy movie data for development without TMDB credentials."""
        dummy_pool = [
            MovieRecommendation(
                title="The Great Escape",
                year=2024,
                overview=f"A captivating journey through {query} — a story that resonates with your current mood.",
                poster_url="",
                tmdb_id=1,
                genre_ids=[12, 18],
                vote_average=8.2,
            ),
            MovieRecommendation(
                title="Echoes of Tomorrow",
                year=2023,
                overview=f"An emotional exploration of {query} themes that will leave you inspired.",
                poster_url="",
                tmdb_id=2,
                genre_ids=[18, 10749],
                vote_average=7.9,
            ),
            MovieRecommendation(
                title="Midnight in Paradise",
                year=2024,
                overview=f"A visually stunning {query} film that perfectly matches your evening vibes.",
                poster_url="",
                tmdb_id=3,
                genre_ids=[35, 18],
                vote_average=8.5,
            ),
            MovieRecommendation(
                title="The Last Horizon",
                year=2023,
                overview=f"An award-winning {query} drama with breathtaking cinematography.",
                poster_url="",
                tmdb_id=4,
                genre_ids=[28, 12],
                vote_average=8.0,
            ),
            MovieRecommendation(
                title="Whispers of the Heart",
                year=2024,
                overview=f"A touching {query} story about connection, growth, and finding beauty in everyday moments.",
                poster_url="",
                tmdb_id=5,
                genre_ids=[18, 10751],
                vote_average=8.7,
            ),
        ]
        return dummy_pool[:limit]

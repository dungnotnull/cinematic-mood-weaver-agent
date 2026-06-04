"""Spotify Web API wrapper — playlist discovery and mood-based music search.

Uses spotipy to search playlists by seed genres, tempo range, and valence target.
"""

from __future__ import annotations

import logging
from typing import Optional

from cinematic_mood_weaver.config import settings
from cinematic_mood_weaver.types.models import PlaylistRecommendation

logger = logging.getLogger(__name__)


class SpotifyClient:
    """Wraps the Spotify Web API for mood-based playlist discovery."""

    def __init__(self):
        self._client: Optional[object] = None

    def _ensure_client(self):
        if self._client is None:
            import spotipy
            from spotipy.oauth2 import SpotifyClientCredentials
            auth = SpotifyClientCredentials(
                client_id=settings.spotify_client_id,
                client_secret=settings.spotify_client_secret,
            )
            self._client = spotipy.Spotify(auth_manager=auth)

    async def search_playlists(
        self,
        seed_genres: str = "mood",
        tempo_range: tuple[int, int] = (80, 120),
        valence_target: float = 0.5,
        limit: int = 5,
    ) -> list[PlaylistRecommendation]:
        """Search for Spotify playlists matching the given mood parameters.

        Falls back to a simple query search when spotipy isn't configured.
        """
        if not settings.spotify_client_id or not settings.spotify_client_secret:
            logger.info("Spotify credentials not configured, returning dummy playlists")
            return self._dummy_playlists(seed_genres, limit)

        self._ensure_client()
        assert self._client is not None

        query = f"{seed_genres} playlist"
        results = self._client.search(q=query, type="playlist", limit=limit)

        playlists = []
        for item in results.get("playlists", {}).get("items", []):
            if not item:
                continue
            playlists.append(
                PlaylistRecommendation(
                    name=item["name"],
                    spotify_id=item["id"],
                    url=item["external_urls"]["spotify"],
                    track_count=item.get("tracks", {}).get("total", 0),
                    tempo_range=tempo_range,
                    valence_target=valence_target,
                    image_url=item.get("images", [{}])[0].get("url") if item.get("images") else None,
                )
            )

        return playlists

    def _dummy_playlists(self, seed_genres: str, limit: int) -> list[PlaylistRecommendation]:
        """Return dummy playlist data for development without Spotify credentials."""
        dummy_names = {
            "happy upbeat pop": ["Happy Vibes", "Feel Good Hits", "Upbeat Morning"],
            "ambient chill lo-fi": ["Deep Focus", "Lo-Fi Beats", "Calm Waters"],
            "acoustic singer songwriter": ["Acoustic Covers", "Singer Songwriter", "Quiet Moments"],
            "rock metal high energy": ["Rock Workout", "Metal Mayhem", "High Energy"],
        }
        names = dummy_names.get(seed_genres, [f"Mood: {seed_genres}", "Curated Mix", "Discover Weekly"])
        return [
            PlaylistRecommendation(
                name=names[i] if i < len(names) else f"Playlist {i + 1}",
                spotify_id=f"dummy_{i}",
                url=f"https://open.spotify.com/playlist/dummy_{i}",
                track_count=50,
                tempo_range=(80, 120),
                valence_target=0.5,
            )
            for i in range(min(limit, len(names)))
        ]


class SpotipyMock(SpotifyClient):
    pass

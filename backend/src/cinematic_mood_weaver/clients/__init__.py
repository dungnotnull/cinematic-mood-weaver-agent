"""External API clients: Spotify, TMDB, and smart lighting."""

from cinematic_mood_weaver.clients.lighting_client import LightingClient
from cinematic_mood_weaver.clients.spotify_client import SpotifyClient
from cinematic_mood_weaver.clients.tmdb_client import TMDBClient

__all__ = ["LightingClient", "SpotifyClient", "TMDBClient"]

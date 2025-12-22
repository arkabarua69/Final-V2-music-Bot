import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from core.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

spotify = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
)

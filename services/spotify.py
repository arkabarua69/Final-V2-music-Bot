import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from core.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

# ============================================================
# VALIDATE CREDENTIALS
# ============================================================
if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    spotify = None
    print("⚠️ Spotify credentials not found. Spotify features disabled.")
else:
    spotify = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
        ),
        requests_timeout=10,
        retries=3,
    )


# ============================================================
# SAFE SEARCH WRAPPER
# ============================================================
def spotify_search(*args, **kwargs):
    """
    Safe Spotify API wrapper to prevent bot crash
    """
    if not spotify:
        return None

    try:
        return spotify.search(*args, **kwargs)
    except Exception as e:
        print("[SPOTIFY ERROR]", e)
        return None

import lyricsgenius
from core.config import GENIUS_TOKEN

# ============================================================
# GENIUS CLIENT (PRODUCTION SAFE)
# ============================================================

if not GENIUS_TOKEN:
    genius = None
    print("⚠️ GENIUS_TOKEN not set. Lyrics feature disabled.")
else:
    genius = lyricsgenius.Genius(
        GENIUS_TOKEN,
        skip_non_songs=True,
        excluded_terms=["(Remix)", "(Live)"],
        timeout=10,  # prevent hanging requests
        retries=2,  # retry on network issues
        remove_section_headers=True,
        verbose=False,
    )

# ============================================================
# SAFE SEARCH WRAPPER
# ============================================================


def search_lyrics(title: str, artist: str):
    """
    Safe Genius lyrics search wrapper
    Returns None on failure instead of crashing the bot
    """
    if not genius:
        return None

    try:
        return genius.search_song(title, artist)
    except Exception as e:
        print("[GENIUS ERROR]", e)
        return None

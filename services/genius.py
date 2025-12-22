import lyricsgenius
from core.config import GENIUS_TOKEN

genius = lyricsgenius.Genius(
    GENIUS_TOKEN,
    skip_non_songs=True,
    excluded_terms=["(Remix)", "(Live)"]
)

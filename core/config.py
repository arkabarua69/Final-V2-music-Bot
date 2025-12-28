import os
from dotenv import load_dotenv

# ============================================================
# LOAD ENV (PRODUCTION SAFE)
# ============================================================
load_dotenv()  # .env should be in project root

# ============================================================
# DISCORD
# ============================================================
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN is not set in environment variables")

# ============================================================
# SPOTIFY
# ============================================================
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# ============================================================
# GENIUS
# ============================================================
GENIUS_TOKEN = os.getenv("GENIUS_TOKEN")

# ============================================================
# LAVALINK
# ============================================================
LAVALINK_HOST = os.getenv("LAVALINK_HOST", "127.0.0.1")
LAVALINK_PORT = int(os.getenv("LAVALINK_PORT", 2333))
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")
LAVALINK_SECURE = os.getenv("LAVALINK_SECURE", "false").lower() == "true"

LAVALINK_NODES = [
    {
        "uri": f"{'https' if LAVALINK_SECURE else 'http'}://{LAVALINK_HOST}:{LAVALINK_PORT}",
        "password": LAVALINK_PASSWORD,
        "secure": LAVALINK_SECURE,
    }
]

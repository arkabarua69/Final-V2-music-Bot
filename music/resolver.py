import wavelink
from services.spotify import spotify_search

MAX_PLAYLIST_TRACKS = 50  # Lavalink safety limit


async def resolve_tracks(query: str, requester):
    """
    Resolve user query into playable Wavelink tracks.
    Supports:
    - Spotify playlists
    - YouTube / YouTube Music search
    - Safe requester metadata injection
    """

    tracks = []

    # ============================================================
    # SPOTIFY PLAYLIST
    # ============================================================
    if "spotify.com/playlist" in query:
        pid = query.split("/")[-1].split("?")[0]

        data = spotify_search(
            playlist_id=pid,
            limit=MAX_PLAYLIST_TRACKS,
        )

        if not data or "items" not in data:
            return []

        for item in data["items"][:MAX_PLAYLIST_TRACKS]:
            track_data = item.get("track")
            if not track_data:
                continue

            search = f"{track_data['name']} {track_data['artists'][0]['name']}"

            try:
                results = await wavelink.Playable.search(
                    f"ytmsearch:{search}"
                )
            except Exception as e:
                print("[LAVALINK SEARCH ERROR]", e)
                continue

            if not results:
                continue

            track = results[0]
            _inject_requester(track, requester)
            tracks.append(track)

        return tracks

    # ============================================================
    # NORMAL SEARCH (YT / YTM)
    # ============================================================
    try:
        results = await wavelink.Playable.search(
            f"ytmsearch:{query}"
        )
    except Exception as e:
        print("[SEARCH ERROR]", e)
        return []

    if not results:
        return []

    track = results[0]
    _inject_requester(track, requester, autocorrected=True)

    return [track]


# ============================================================
# REQUESTER METADATA (SAFE)
# ============================================================
def _inject_requester(track: wavelink.Playable, requester, autocorrected=False):
    """
    Safely attach requester metadata to Wavelink track
    """

    if not hasattr(track, "extras") or not track.extras:
        track.extras = {}

    track.extras.requester_name = requester.display_name
    track.extras.requester_tag = requester.discriminator
    track.extras.requester_id = requester.id
    track.extras.requester_avatar = requester.display_avatar.url
    track.extras.autocorrected = autocorrected

import wavelink
from services.spotify import spotify


async def resolve_tracks(query: str, requester):
    tracks = []

    # ---------- SPOTIFY PLAYLIST ----------
    if "spotify.com/playlist" in query:
        pid = query.split("/")[-1].split("?")[0]
        items = spotify.playlist_items(pid)["items"]

        for item in items:
            track_data = item.get("track")
            if not track_data:
                continue

            search = f"{track_data['name']} {track_data['artists'][0]['name']}"
            results = await wavelink.Playable.search(f"ytsearch:{search}")

            if results:
                t = results[0]

                # requester info (Wavelink 3.x SAFE)
                t.extras.requester_name = requester.display_name
                t.extras.requester_tag = requester.discriminator
                t.extras.requester_id = requester.id
                t.extras.requester_avatar = requester.display_avatar.url

                tracks.append(t)

        return tracks

    # ---------- NORMAL SEARCH ----------
    results = await wavelink.Playable.search(f"ytsearch:{query}")

    if results:
        t = results[0]

        t.extras.requester_name = requester.display_name
        t.extras.requester_tag = requester.discriminator
        t.extras.requester_id = requester.id
        t.extras.requester_avatar = requester.display_avatar.url

        return [t]

    return []

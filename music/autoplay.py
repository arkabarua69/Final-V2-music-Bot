import random
import wavelink


async def get_autoplay_track(state):
    """
    Smart autoplay:
    1. Use current/seed track
    2. Search similar tracks via YouTube Music
    3. Fallback to artist name search
    """

    seed = state.autoplay_seed or state.current
    if not seed:
        return None

    # Try similar song search
    query = f"{seed.title} {seed.author}"
    results = await wavelink.Playable.search(
        f"ytmsearch:{query}"
    )

    if results:
        pick = random.choice(results[:5])
        pick.extras = {"autoplay": True}
        return pick

    # Fallback: artist only
    results = await wavelink.Playable.search(
        f"ytmsearch:{seed.author}"
    )

    if results:
        pick = random.choice(results[:5])
        pick.extras = {"autoplay": True}
        return pick

    return None

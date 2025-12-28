import random
import wavelink


async def get_autoplay_track(state):
    """
    Production-grade autoplay system

    Flow:
    1. Use autoplay_seed (last actually played track) or current
    2. Search similar tracks via YouTube Music
    3. Fallback to artist-only search
    4. Never repeat the same track
    5. Rotate seed so autoplay continues naturally
    """

    # --------------------------------------------------
    # 1. SEED SELECTION
    # --------------------------------------------------
    seed = state.autoplay_seed or state.current
    if not seed:
        return None

    queries = [
        f"{seed.title} {seed.author}",  # similar song
        f"{seed.author}",  # artist fallback
    ]

    # --------------------------------------------------
    # 2. SEARCH STRATEGY
    # --------------------------------------------------
    for query in queries:
        try:
            results = await wavelink.Playable.search(
                f"ytmsearch:{query}"
            )
        except Exception as e:
            print("[AUTOPLAY SEARCH ERROR]", e)
            continue

        if not results:
            continue

        # --------------------------------------------------
        # 3. AVOID REPEATING CURRENT TRACK
        # --------------------------------------------------
        filtered = [
            track for track in results
            if track.title.lower() != seed.title.lower()
        ]

        candidates = filtered[:5] if filtered else results[:5]
        pick = random.choice(candidates)

        # --------------------------------------------------
        # 4. SAFE EXTRAS HANDLING (Wavelink v2/v3)
        # --------------------------------------------------
        if not hasattr(pick, "extras") or not pick.extras:
            pick.extras = {}

        pick.extras.autoplay = True

        # --------------------------------------------------
        # 5. ROTATE SEED (CRITICAL)
        # --------------------------------------------------
        state.autoplay_seed = pick

        return pick

    return None

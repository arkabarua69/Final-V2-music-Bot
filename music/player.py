import wavelink
from music.autoplay import get_autoplay_track
from music.state import music_states
from music.embed import build_player_embed
from music.controls import MusicControlView


async def play_next(player: wavelink.Player, guild_id: int):
    """
    Unified next-track handler
    Priority:
    1. Loop
    2. Queue
    3. Autoplay
    4. Cleanup
    """

    if not player or not player.guild:
        return

    state = music_states.get(guild_id)
    if not state:
        return

    # ============================================================
    # LOOP
    # ============================================================
    if state.loop and state.current:
        await player.play(state.current)
        return

    # ============================================================
    # QUEUE
    # ============================================================
    if state.queue:
        state.previous = state.current
        state.current = state.queue.pop(0)
        state.autoplay_seed = state.current

        await player.play(state.current)
        await _update_ui(state, player)
        return

    # ============================================================
    # AUTOPLAY
    # ============================================================
    if state.autoplay:
        try:
            next_track = await get_autoplay_track(state)
        except Exception as e:
            print("[AUTOPLAY ERROR]", e)
            next_track = None

        if next_track:
            state.previous = state.current
            state.current = next_track
            state.autoplay_seed = next_track

            await player.play(next_track)
            await _update_ui(state, player)
            return

    # ============================================================
    # CLEANUP (END OF SESSION)
    # ============================================================
    await _cleanup(player, state, guild_id)


# ============================================================
# UI UPDATE (SAFE)
# ============================================================
async def _update_ui(state, player):
    if not state.message:
        return

    try:
        await state.message.edit(
            embed=build_player_embed(state),
            view=MusicControlView(player, player.guild.id),
        )
    except Exception:
        pass


# ============================================================
# CLEANUP (SAFE)
# ============================================================
async def _cleanup(player, state, guild_id):
    try:
        if player.is_connected():
            await player.disconnect(force=True)
    except Exception:
        pass

    if state.message:
        try:
            await state.message.edit(
                embed=None,
                view=None,
            )
        except Exception:
            pass

    state.reset()
    music_states.pop(guild_id, None)

from music.autoplay import get_autoplay_track
from music.state import music_states


async def play_next(player, gid, spotify):
    state = music_states.get(gid)
    if not state:
        return

    if state.loop and state.current:
        await player.play(state.current)
        return

    if state.queue:
        state.previous = state.current
        state.current = state.queue.pop(0)
        state.autoplay_seed = state.current
        await player.play(state.current)
        return

    if state.autoplay:
        next_track = await get_autoplay_track(state, gid)
        if next_track:
            state.previous = state.current
            state.current = next_track
            state.autoplay_seed = next_track
            await player.play(next_track)
            return


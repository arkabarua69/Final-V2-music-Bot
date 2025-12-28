import os
import asyncio
import signal
import discord
import wavelink

from core.bot import bot, tree
from core.config import TOKEN
from core.lavalink import connect_lavalink
from web.keep_alive import run_server

import commands.play
import commands.basic
import commands.info

from music.state import music_states
from music.embed import build_player_embed
from music.controls import MusicControlView
from music.autoplay import get_autoplay_track


# ============================================================
# WAVELINK TRACK END HANDLER (PRODUCTION SAFE)
# ============================================================
@bot.listen("on_wavelink_track_end")
async def on_wavelink_track_end(payload: wavelink.TrackEndEventPayload):
    player: wavelink.Player = payload.player
    guild = getattr(player, "guild", None)

    if not player or not guild:
        return

    guild_id = guild.id
    state = music_states.get(guild_id)
    if not state:
        return

    # --------------------------------------------------
    # 🔁 LOOP MODE
    # --------------------------------------------------
    if state.loop and state.current:
        await player.play(state.current)
        return

    # --------------------------------------------------
    # 📜 QUEUE MODE
    # --------------------------------------------------
    if state.queue:
        state.previous = state.current
        state.current = state.queue.pop(0)
        state.autoplay_seed = state.current
        state.manual_action = None

        await player.play(state.current)
        await _update_panel(state, player, guild_id)
        return

    # --------------------------------------------------
    # 🔄 AUTOPLAY MODE
    # --------------------------------------------------
    if state.autoplay:
        if state.manual_action == "back":
            # ⏮ back was one-time only → resume autoplay next
            state.manual_action = None
        else:
            next_track = await get_autoplay_track(state)
            if next_track:
                state.previous = state.current
                state.current = next_track
                state.autoplay_seed = next_track

                await player.play(next_track)
                await _update_panel(state, player, guild_id)
                return

    # --------------------------------------------------
    # 🧹 CLEANUP (REAL END ONLY)
    # --------------------------------------------------
    if state.manual_action:
        state.manual_action = None
        return

    await cleanup_player(player, state, guild_id)


# ============================================================
# UPDATE CONTROL PANEL
# ============================================================
async def _update_panel(state, player, guild_id):
    if state.message:
        try:
            await state.message.edit(
                embed=build_player_embed(state),
                view=MusicControlView(player, guild_id),
            )
        except Exception:
            pass


# ============================================================
# CLEANUP PLAYER
# ============================================================
async def cleanup_player(player: wavelink.Player, state, guild_id: int):
    try:
        await player.disconnect(force=True)
    except Exception:
        pass

    if state.message:
        try:
            await state.message.edit(
                embed=discord.Embed(
                    title="Playback Finished",
                    description="Queue ended. Playback stopped.",
                    color=discord.Color.red(),
                ),
                view=None,
            )
        except Exception:
            pass

    music_states.pop(guild_id, None)


# ============================================================
# BOT READY
# ============================================================
@bot.event
async def on_ready():
    print("🔌 Connecting Lavalink...")
    await connect_lavalink(bot)

    commands.play.setup(tree)
    commands.basic.setup(tree)
    commands.info.setup(tree)

    if not getattr(bot, "_synced", False):
        await tree.sync()
        bot._synced = True

    print(f"✅ Logged in as {bot.user}")


# ============================================================
# GRACEFUL SHUTDOWN
# ============================================================
async def shutdown():
    print("🛑 Shutting down bot...")

    for guild_id in list(music_states.keys()):
        try:
            guild = bot.get_guild(guild_id)
            if guild and guild.voice_client:
                await guild.voice_client.disconnect(force=True)
        except Exception:
            pass

    await bot.close()


def handle_exit():
    asyncio.get_event_loop().create_task(shutdown())


# ============================================================
# MAIN ENTRY POINT
# ============================================================
if __name__ == "__main__":
    # Start keep-alive only for hosting platforms
    if os.getenv("RENDER") or os.getenv("RAILWAY"):
        run_server()

    signal.signal(signal.SIGTERM, lambda *_: handle_exit())
    signal.signal(signal.SIGINT, lambda *_: handle_exit())

    bot.run(TOKEN)

import asyncio
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


# ================= WAVELINK TRACK END (SAFE) =================
@bot.listen("on_wavelink_track_end")
async def on_track_end(payload: wavelink.TrackEndEventPayload):
    player = payload.player
    guild = getattr(player, "guild", None)

    if not player or not guild:
        return

    state = music_states.get(guild.id)
    if not state:
        return

    # 🔁 LOOP
    if state.loop and state.current:
        await player.play(state.current)
        return

    # 📜 QUEUE
    if state.queue:
        state.previous = state.current
        state.current = state.queue.pop(0)
        await player.play(state.current)

    # 🔄 AUTOPLAY
    elif state.autoplay and state.autoplay_seed:
        from music.autoplay import get_autoplay_track

        next_track = await get_autoplay_track(state)
        if next_track:
            state.previous = state.current
            state.current = next_track
            await player.play(next_track)
        else:
            await cleanup_player(player, state)
            return
    else:
        await cleanup_player(player, state)
        return

    # 🔄 UPDATE UI
    if state.message:
        try:
            await state.message.edit(
                embed=build_player_embed(state),
                view=MusicControlView(player, guild.id),
            )
        except Exception as e:
            print("[UI UPDATE ERROR]", e)


# ================= CLEANUP =================
async def cleanup_player(player, state):
    guild_id = getattr(player.guild, "id", None)

    try:
        await player.disconnect()
    except Exception:
        pass

    if state.message:
        try:
            await state.message.edit(
                embed=discord.Embed(
                    title="Playback Finished",
                    description="Queue ended. Bot disconnected.",
                    color=discord.Color.red(),
                ),
                view=None,
            )
        except Exception:
            pass

    if guild_id:
        music_states.pop(guild_id, None)


# ================= BOT READY =================
@bot.event
async def on_ready():
    await connect_lavalink(bot)

    commands.play.setup(tree)
    commands.basic.setup(tree)
    commands.info.setup(tree)

    await tree.sync()
    print(f"Logged in as {bot.user}")


# ================= AUTO RESTART SYSTEM =================
async def start_bot():
    while True:
        try:
            await bot.start(TOKEN)
        except Exception as e:
            print("🔥 BOT CRASHED:", e)
            print("♻️ Restarting in 5 seconds...")
            await asyncio.sleep(5)


# ================= START =================
run_server()

asyncio.run(start_bot())

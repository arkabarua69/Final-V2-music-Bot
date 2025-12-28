from discord import Interaction, Embed, Color
import random
import wavelink

from music.state import music_states
from music.embed import build_player_embed
from music.controls import MusicControlView


def setup(tree):

    # ------------------ /join ------------------
    @tree.command(name="join", description="Join your voice channel")
    async def join(interaction: Interaction):
        user = interaction.user
        guild = interaction.guild

        if not user.voice or not user.voice.channel:
            return await interaction.response.send_message(
                embed=Embed(
                    title="Voice Channel Required",
                    description="Please join a voice channel first.",
                    color=Color.orange(),
                ),
                ephemeral=True,
            )

        player: wavelink.Player = guild.voice_client
        channel = user.voice.channel

        if not player:
            await channel.connect(cls=wavelink.Player)
        elif player.channel != channel:
            await player.move_to(channel)

        await interaction.response.send_message(
            embed=Embed(
                title="Connected",
                description=f"Joined **{channel.name}**",
                color=Color.green(),
            )
        )

    # ------------------ /leave ------------------
    @tree.command(name="leave", description="Leave the voice channel")
    async def leave(interaction: Interaction):
        guild = interaction.guild
        player: wavelink.Player = guild.voice_client
        state = music_states.get(guild.id)

        if not player:
            return await interaction.response.send_message(
                embed=Embed(
                    title="Not Connected",
                    description="I am not connected to any voice channel.",
                    color=Color.red(),
                ),
                ephemeral=True,
            )

        try:
            await player.disconnect(force=True)
        except Exception:
            pass

        if state:
            if state.message:
                try:
                    await state.message.edit(embed=None, view=None)
                except Exception:
                    pass
            state.reset()
            music_states.pop(guild.id, None)

        await interaction.response.send_message(
            embed=Embed(
                title="Disconnected",
                description="Left the voice channel.",
                color=Color.red(),
            )
        )

    # ------------------ /pause ------------------
    @tree.command(name="pause", description="Pause the current track")
    async def pause(interaction: Interaction):
        player: wavelink.Player = interaction.guild.voice_client
        if not player or not player.playing:
            return await interaction.response.send_message(
                embed=Embed(
                    title="Nothing Playing",
                    description="There is no active playback right now.",
                    color=Color.orange(),
                ),
                ephemeral=True,
            )

        await player.pause(True)
        await interaction.response.send_message(
            embed=Embed(
                title="Playback Paused",
                description="Music playback has been paused.",
                color=Color.blurple(),
            )
        )

    # ------------------ /resume ------------------
    @tree.command(name="resume", description="Resume the paused track")
    async def resume(interaction: Interaction):
        player: wavelink.Player = interaction.guild.voice_client
        if not player or not player.paused:
            return await interaction.response.send_message(
                embed=Embed(
                    title="Not Paused",
                    description="Playback is not paused.",
                    color=Color.orange(),
                ),
                ephemeral=True,
            )

        await player.pause(False)
        await interaction.response.send_message(
            embed=Embed(
                title="Playback Resumed",
                description="Music playback has resumed.",
                color=Color.green(),
            )
        )

    # ------------------ /skip ------------------
    @tree.command(name="skip", description="Skip the current track")
    async def skip(interaction: Interaction):
        player: wavelink.Player = interaction.guild.voice_client
        if not player or not player.playing:
            return await interaction.response.send_message(
                embed=Embed(
                    title="Nothing Playing",
                    description="There is no track to skip.",
                    color=Color.orange(),
                ),
                ephemeral=True,
            )

        await player.stop()
        await interaction.response.send_message(
            embed=Embed(
                title="Track Skipped",
                description="Skipping to the next track.",
                color=Color.blurple(),
            )
        )

    # ------------------ /volume ------------------
    @tree.command(name="volume", description="Set playback volume (1-200)")
    async def volume(interaction: Interaction, level: int):
        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            return await interaction.response.send_message(
                embed=Embed(
                    title="Not Connected",
                    description="The bot is not in a voice channel.",
                    color=Color.red(),
                ),
                ephemeral=True,
            )

        level = max(1, min(200, level))
        await player.set_volume(level)

        await interaction.response.send_message(
            embed=Embed(
                title="Volume Updated",
                description=f"Playback volume set to **{level}%**",
                color=Color.green(),
            )
        )

    # ------------------ /seek ------------------
    @tree.command(name="seek", description="Seek the current track (seconds)")
    async def seek(interaction: Interaction, seconds: int):
        player: wavelink.Player = interaction.guild.voice_client
        state = music_states.get(interaction.guild.id)

        if not player or not player.playing or not state or not state.current:
            return await interaction.response.send_message(
                embed=Embed(
                    title="Nothing Playing",
                    description="There is no active playback.",
                    color=Color.orange(),
                ),
                ephemeral=True,
            )

        max_seconds = (state.current.length or 0) // 1000
        seconds = max(0, min(seconds, max_seconds))

        await player.seek(seconds * 1000)
        await interaction.response.send_message(
            embed=Embed(
                title="Seek Successful",
                description=f"Seeked to **{seconds} seconds**.",
                color=Color.green(),
            )
        )

    # ------------------ /shuffle ------------------
    @tree.command(name="shuffle", description="Shuffle the music queue")
    async def shuffle(interaction: Interaction):
        state = music_states.get(interaction.guild.id)
        if not state or not state.queue:
            return await interaction.response.send_message(
                embed=Embed(
                    title="Queue Empty",
                    description="There are no tracks to shuffle.",
                    color=Color.orange(),
                ),
                ephemeral=True,
            )

        random.shuffle(state.queue)
        await interaction.response.send_message(
            embed=Embed(
                title="Queue Shuffled",
                description="The queue order has been randomized.",
                color=Color.blurple(),
            )
        )

    # ------------------ /loop ------------------
    @tree.command(name="loop", description="Toggle loop mode")
    async def loop(interaction: Interaction):
        state = music_states.get(interaction.guild.id)
        player = interaction.guild.voice_client

        if not state:
            return await interaction.response.send_message(
                embed=Embed(
                    title="No Session",
                    description="No active music session found.",
                    color=Color.red(),
                ),
                ephemeral=True,
            )

        state.loop = not state.loop
        await interaction.response.send_message(
            embed=Embed(
                title="Loop Mode",
                description=f"Loop is now **{'ENABLED' if state.loop else 'DISABLED'}**.",
                color=Color.green() if state.loop else Color.red(),
            )
        )

        if state.message and player:
            await state.message.edit(
                embed=build_player_embed(state),
                view=MusicControlView(player, interaction.guild.id),
            )

    # ------------------ /autoplay ------------------
    @tree.command(name="autoplay", description="Toggle autoplay mode")
    async def autoplay(interaction: Interaction):
        state = music_states.get(interaction.guild.id)
        player = interaction.guild.voice_client

        if not state:
            return await interaction.response.send_message(
                embed=Embed(
                    title="No Session",
                    description="No active music session found.",
                    color=Color.red(),
                ),
                ephemeral=True,
            )

        state.autoplay = not state.autoplay
        if state.autoplay and not state.autoplay_seed and state.current:
            state.autoplay_seed = state.current

        await interaction.response.send_message(
            embed=Embed(
                title="Autoplay",
                description=f"Autoplay is now **{'ENABLED' if state.autoplay else 'DISABLED'}**.",
                color=Color.green() if state.autoplay else Color.red(),
            )
        )

        if state.message and player:
            await state.message.edit(
                embed=build_player_embed(state),
                view=MusicControlView(player, interaction.guild.id),
            )

    # ------------------ /clear ------------------
    @tree.command(name="clear", description="Clear the music queue")
    async def clear(interaction: Interaction):
        state = music_states.get(interaction.guild.id)
        if not state or not state.queue:
            return await interaction.response.send_message(
                embed=Embed(
                    title="Queue Empty",
                    description="The queue is already empty.",
                    color=Color.orange(),
                ),
                ephemeral=True,
            )

        state.queue.clear()
        await interaction.response.send_message(
            embed=Embed(
                title="Queue Cleared",
                description="All tracks have been removed from the queue.",
                color=Color.green(),
            )
        )

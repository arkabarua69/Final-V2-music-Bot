import discord
import wavelink

from core.lavalink import node_ready
from music.state import MusicState, music_states
from music.resolver import resolve_tracks
from music.controls import MusicControlView
from music.embed import build_player_embed


def setup(tree):

    @tree.command(name="play", description="Play a song or playlist")
    async def play(interaction: discord.Interaction, query: str):
        await interaction.response.defer(thinking=True)

        # ==================================================
        # LAVALINK CHECK
        # ==================================================
        if not node_ready():
            embed = discord.Embed(
                title="❌ Music Service Unavailable",
                description=(
                    "The music backend (**Lavalink**) is currently **offline or unreachable**.\n\n"
                    "Please try again later or contact the bot administrator."
                ),
                color=discord.Color.red(),
            )
            embed.set_footer(text="System Status • Lavalink")
            return await interaction.followup.send(embed=embed, ephemeral=True)

        # ==================================================
        # VOICE CHANNEL CHECK
        # ==================================================
        if not interaction.user.voice or not interaction.user.voice.channel:
            embed = discord.Embed(
                title="🔊 Voice Channel Required",
                description="You must **join a voice channel** before using music commands.",
                color=discord.Color.orange(),
            )
            embed.set_footer(text="User Action Required")
            return await interaction.followup.send(embed=embed, ephemeral=True)

        channel = interaction.user.voice.channel

        # ==================================================
        # CONNECT / GET PLAYER
        # ==================================================
        player: wavelink.Player = interaction.guild.voice_client

        if not player:
            player = await channel.connect(cls=wavelink.Player)
        elif player.channel != channel:
            await player.move_to(channel)

        # ==================================================
        # MUSIC STATE
        # ==================================================
        state: MusicState = music_states.setdefault(
            interaction.guild.id, MusicState()
        )

        # ==================================================
        # RESOLVE TRACKS (AUTO-CORRECT ENABLED)
        # ==================================================
        tracks = await resolve_tracks(query, interaction.user)

        if not tracks:
            embed = discord.Embed(
                title="❌ No Results Found",
                description=(
                    "Could not find any playable tracks for your query.\n\n"
                    "Please check spelling or try another song."
                ),
                color=discord.Color.red(),
            )
            embed.set_footer(text="Search Failed • Music System")
            return await interaction.followup.send(embed=embed, ephemeral=True)

        # ==================================================
        # PLAY / QUEUE LOGIC
        # ==================================================
        started_playback = False
        queued_only = True

        for track in tracks:
            if not player.playing and not started_playback:
                state.previous = state.current
                state.current = track
                state.autoplay_seed = track

                await player.play(track)

                started_playback = True
                queued_only = False
            else:
                state.queue.append(track)

        # ==================================================
        # CONTROL PANEL (ALWAYS UPDATE)
        # ==================================================
        embed = build_player_embed(state)
        view = MusicControlView(player, interaction.guild.id)

        if not state.message:
            state.message = await interaction.followup.send(
                embed=embed,
                view=view,
            )
        else:
            await state.message.edit(
                embed=embed,
                view=view,
            )

        # ==================================================
        # AUTO-CORRECT NOTICE
        # ==================================================
        if started_playback and state.current.extras.get("autocorrected"):
            notice = discord.Embed(
                title="🔎 Auto-Correct Applied",
                description=(
                    "Your search contained spelling errors.\n"
                    "The closest matching track is now playing:\n\n"
                    f"🎵 **{state.current.title}**"
                ),
                color=discord.Color.green(),
            )
            notice.set_footer(text="Smart Search • Music System")
            await interaction.followup.send(embed=notice, ephemeral=True)

        # ==================================================
        # QUEUE CONFIRMATION
        # ==================================================
        if queued_only:
            embed = discord.Embed(
                title="📥 Track Queued",
                description=(
                    "Your requested track has been **successfully added to the queue**.\n\n"
                    "Playback will begin automatically when the current track finishes."
                ),
                color=discord.Color.blurple(),
            )
            embed.set_footer(text="Queue Update • Music System")
            await interaction.followup.send(embed=embed, ephemeral=True)

import discord
import wavelink

from core.lavalink import node_ready
from music.state import MusicState, music_states
from music.resolver import resolve_tracks
from music.controls import MusicControlView
from music.embed import build_player_embed


def setup(tree):

    @tree.command(
        name="play",
        description="Play a song or playlist (queue-safe, back-safe)",
    )
    async def play(interaction: discord.Interaction, query: str):
        # ==================================================
        # INITIAL DEFER
        # ==================================================
        await interaction.response.defer(thinking=True)

        guild = interaction.guild
        user = interaction.user

        # ==================================================
        # LAVALINK CHECK
        # ==================================================
        if not node_ready():
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Music Service Offline",
                    description=(
                        "The music backend (**Lavalink**) is currently unavailable.\n\n"
                        "Please try again later."
                    ),
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        # ==================================================
        # VOICE CHANNEL CHECK
        # ==================================================
        if not user.voice or not user.voice.channel:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="🔊 Voice Channel Required",
                    description="Please **join a voice channel** before playing music.",
                    color=discord.Color.orange(),
                ),
                ephemeral=True,
            )

        channel = user.voice.channel

        # ==================================================
        # CONNECT / FETCH PLAYER (SAFE)
        # ==================================================
        player: wavelink.Player = guild.voice_client

        if not player:
            try:
                player = await channel.connect(cls=wavelink.Player)
            except Exception:
                player = guild.voice_client

        elif player.channel != channel:
            await player.move_to(channel)

        # ==================================================
        # MUSIC STATE (ONE PER GUILD)
        # ==================================================
        state: MusicState = music_states.setdefault(
            guild.id,
            MusicState(),
        )
        state.player = player

        # Reset manual flag on new /play
        state.manual_action = False

        # ==================================================
        # RESOLVE TRACKS (SAFE)
        # ==================================================
        try:
            tracks = await resolve_tracks(query, user)
        except Exception as e:
            print("[RESOLVE ERROR]", e)
            tracks = None

        if not tracks:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ No Results Found",
                    description=(
                        "No playable tracks were found for your query.\n\n"
                        "Try another song name or URL."
                    ),
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        # ==================================================
        # PLAY / QUEUE LOGIC (BACK + AUTOPLAY SAFE)
        # ==================================================
        player_is_playing = bool(player.playing or player.paused)

        started_playback = False
        queued_only = True

        for track in tracks:

            # ▶ CASE 1: PLAYER IDLE → PLAY IMMEDIATELY
            if not player_is_playing and not started_playback:
                # Update previous safely
                state.previous = state.current
                state.current = track

                await player.play(track)

                # Autoplay seed ONLY for actually played track
                state.autoplay_seed = track

                started_playback = True
                queued_only = False

            # 📥 CASE 2: PLAYER ACTIVE → QUEUE ONLY
            else:
                state.queue.append(track)

        # ==================================================
        # CONTROL PANEL UPDATE (UNIFIED)
        # ==================================================
        embed = build_player_embed(state)
        view = MusicControlView(player, guild.id)

        try:
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
        except Exception:
            state.message = await interaction.followup.send(
                embed=embed,
                view=view,
            )

        # ==================================================
        # AUTO-CORRECT NOTICE (OPTIONAL)
        # ==================================================
        autocorrected = False
        if state.current and hasattr(state.current, "extras"):
            autocorrected = getattr(
                state.current.extras,
                "autocorrected",
                False,
            )

        if started_playback and autocorrected:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="🔎 Auto-Correct Applied",
                    description=(
                        "Your search contained spelling issues.\n\n"
                        f"Now playing:\n🎵 **{state.current.title}**"
                    ),
                    color=discord.Color.green(),
                ),
                ephemeral=True,
            )

        # ==================================================
        # QUEUE CONFIRMATION (IF APPLICABLE)
        # ==================================================
        if queued_only:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="📥 Track Queued",
                    description=(
                        "Your requested track has been **added to the queue**.\n\n"
                        "It will play automatically after the current song."
                    ),
                    color=discord.Color.blurple(),
                ),
                ephemeral=True,
            )

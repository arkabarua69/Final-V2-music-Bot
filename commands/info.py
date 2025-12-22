from discord import app_commands, Interaction, Embed
from music.state import music_states
from services.genius import genius


def setup(tree):

    # ==================================================
    # /nowplaying
    # ==================================================
    @tree.command(name="nowplaying", description="Show current playing song")
    async def nowplaying(interaction: Interaction):
        state = music_states.get(interaction.guild.id)
        player = interaction.guild.voice_client

        if not state or not state.current or not player:
            embed = Embed(
                title="❌ No Music Playing",
                description="There is currently **no song playing** in this server.",
                color=0xED4245,
            )
            embed.set_footer(text="Now Playing • Music System")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        track = state.current

        embed = Embed(
            title="🎶 Now Playing",
            description=f"[{track.title}]({track.uri})",
            color=0x2F3136,
        )
        embed.add_field(name="Artist", value=track.author, inline=True)
        embed.add_field(name="Volume", value=f"{player.volume}%", inline=True)
        embed.add_field(
            name="Autoplay",
            value="ON ✅" if state.autoplay else "OFF ❌",
            inline=True,
        )

        if track.artwork:
            embed.set_thumbnail(url=track.artwork)

        embed.set_footer(text=f"Requested in {interaction.guild.name}")

        await interaction.response.send_message(embed=embed)

    # ==================================================
    # /queue
    # ==================================================
    @tree.command(name="queue", description="Show music queue")
    async def queue(interaction: Interaction):
        state = music_states.get(interaction.guild.id)

        if not state or not state.queue:
            embed = Embed(
                title="📭 Queue Empty",
                description="There are **no tracks** in the queue.",
                color=0xED4245,
            )
            embed.set_footer(text="Queue • Music System")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        description = "\n".join(
            f"`{i+1}.` **{t.title}** — {t.author}"
            for i, t in enumerate(state.queue[:10])
        )

        embed = Embed(
            title="🎵 Music Queue",
            description=description,
            color=0x5865F2,
        )

        if len(state.queue) > 10:
            embed.set_footer(
                text=f"And {len(state.queue) - 10} more tracks in queue..."
            )
        else:
            embed.set_footer(text="Queue • Music System")

        await interaction.response.send_message(embed=embed)

    # ==================================================
    # /history
    # ==================================================
    @tree.command(name="history", description="Show recently played tracks")
    async def history(interaction: Interaction):
        state = music_states.get(interaction.guild.id)

        if not state or not state.history:
            embed = Embed(
                title="📭 No History Found",
                description="No previously played tracks are available.",
                color=0xED4245,
            )
            embed.set_footer(text="History • Music System")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        embed = Embed(
            title="🕒 Recently Played",
            description="\n".join(
                f"`{i+1}.` **{t.title}** — {t.author}"
                for i, t in enumerate(state.history[-10:])
            ),
            color=0x57F287,
        )

        embed.set_footer(text="History • Music System")

        await interaction.response.send_message(embed=embed)

    # ==================================================
    # /favorites
    # ==================================================
    @tree.command(name="favorites", description="Show favorite tracks")
    async def favorites(interaction: Interaction):
        state = music_states.get(interaction.guild.id)

        if not state or not state.favorites:
            embed = Embed(
                title="⭐ No Favorites",
                description="You have not added any favorite tracks yet.",
                color=0xED4245,
            )
            embed.set_footer(text="Favorites • Music System")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        embed = Embed(
            title="⭐ Favorite Songs",
            description="\n".join(
                f"`{i+1}.` **{t.title}** — {t.author}"
                for i, t in enumerate(state.favorites[:10])
            ),
            color=0xFEE75C,
        )

        embed.set_footer(text="Favorites • Music System")

        await interaction.response.send_message(embed=embed)

    # ==================================================
    # /lyrics
    # ==================================================
    @tree.command(name="lyrics", description="Get lyrics of current song")
    async def lyrics(interaction: Interaction):

        # ⏳ Lyrics API is slow
        await interaction.response.defer(thinking=True)

        state = music_states.get(interaction.guild.id)

        if not state or not state.current:
            embed = Embed(
                title="❌ No Music Playing",
                description="There is **no song currently playing**.",
                color=0xED4245,
            )
            embed.set_footer(text="Lyrics • Music System")
            return await interaction.followup.send(embed=embed, ephemeral=True)

        song = genius.search_song(
            state.current.title,
            state.current.author,
        )

        if not song or not song.lyrics:
            embed = Embed(
                title="❌ Lyrics Not Found",
                description=(
                    "Lyrics could not be found for the current track.\n\n"
                    "This may be due to missing data or API limitations."
                ),
                color=0xFAA61A,
            )
            embed.set_footer(text="Lyrics Search Failed")
            return await interaction.followup.send(embed=embed, ephemeral=True)

        # ✂️ Discord embed limit safety
        lyrics_text = song.lyrics
        if len(lyrics_text) > 4096:
            lyrics_text = lyrics_text[:4090] + "\n…"

        embed = Embed(
            title=f"🎤 {song.title}",
            description=lyrics_text,
            color=0x5865F2,
        )

        embed.set_footer(
            text=f"Requested in {interaction.guild.name}"
        )

        await interaction.followup.send(embed=embed)

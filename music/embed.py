import discord
from music.state import MusicState

SYSTEM_ICON = "https://media.discordapp.net/attachments/1420115492580098272/1452709148344062106/Mikey.png?ex=694acc52&is=69497ad2&hm=22b482987bea03204bab414b2eb2e489d644d4bc9585c9702d879b5b6d47ff24&=&format=webp&quality=lossless"


def build_player_embed(state: MusicState) -> discord.Embed:
    """
    Advanced unified music control panel embed.
    Safe, scalable, and future-ready.
    """

    track = state.current

    # ================= EMBED BASE =================
    embed = discord.Embed(
        title="🎵 Music Control Panel",
        description=(
            "Control playback using the buttons below.\n"
            "Queue, autoplay, and loop status are shown at the footer."
        ),
        color=discord.Color.blurple(),
    )

    # ================= AUTHOR (ALWAYS SHOW) =================
    if track and track.extras and hasattr(track.extras, "requester_name"):
        requester_name = track.extras.requester_name
        requester_avatar = getattr(track.extras, "requester_avatar", SYSTEM_ICON)
    else:
        requester_name = "Music System"
        requester_avatar = SYSTEM_ICON

    embed.set_author(
        name=f"Requested by {requester_name}",
        icon_url=requester_avatar,
    )

    # ================= NOW PLAYING =================
    if track:
        embed.add_field(
            name="🎶 Music Now Playing",
            value=f"[{track.title}]({track.uri})",
            inline=False,
        )

        # ---------- REQUESTED BY (INLINE) ----------
        embed.add_field(
            name="🎧 Requested By",
            value=(
                f"{requester_name} "
                f"#{getattr(track.extras, 'requester_tag', '0000')}"
                if track and track.extras and hasattr(track.extras, "requester_name")
                else "Music System"
            ),
            inline=True,
        )

        # ---------- DURATION ----------
        duration = (
            f"{track.length // 60000}:{(track.length // 1000) % 60:02d}"
            if track.length and track.length > 0
            else "Live"
        )

        embed.add_field(
            name="⏱ Duration",
            value=duration,
            inline=True,
        )

        # ---------- ARTIST ----------
        embed.add_field(
            name="✍ Artist",
            value=track.author or "Unknown Artist",
            inline=True,
        )

        # ---------- THUMBNAIL ----------
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)

    else:
        embed.add_field(
            name="🎶 Player Status",
            value="Nothing is playing right now.\nUse `/play` to start music.",
            inline=False,
        )

    # ================= FOOTER =================
    embed.set_footer(
        text=(
            f"Autoplay: {'ON' if state.autoplay else 'OFF'} • "
            f"Loop: {'ON' if state.loop else 'OFF'} • "
            f"Queue: {len(state.queue)}\n"
            "© 2025 Mac GunJon • Music System"
        ),
        icon_url=requester_avatar,
    )

    return embed

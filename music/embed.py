import discord
from music.state import MusicState

SYSTEM_ICON = (
    "https://media.discordapp.net/attachments/1420115492580098272/"
    "1452709148344062106/Mikey.png"
)
SYSTEM_ICON = "https://media.discordapp.net/attachments/1420115492580098272/1452709148344062106/Mikey.png?ex=694acc52&is=69497ad2&hm=22b482987bea03204bab414b2eb2e489d644d4bc9585c9702d879b5b6d47ff24&=&format=webp&quality=lossless"


def build_player_embed(state: MusicState) -> discord.Embed:
    """
    Unified production-grade music control embed
    Compatible with Wavelink v3+
    """

    track = state.current if state else None

    # ============================================================
    # EMBED BASE
    # ============================================================
    embed = discord.Embed(
        title="🎵 Music Control Panel",
        description=(
            "Use the buttons below to control playback.\n"
            "Autoplay, loop, and queue status are shown in the footer."
        ),
        color=discord.Color.blurple(),
    )

    # ============================================================
    # REQUESTER INFO (SAFE)
    # ============================================================
    requester_name = "Music System"
    requester_avatar = SYSTEM_ICON
    requester_tag = ""

    if track and hasattr(track, "extras") and track.extras:
        requester_name = getattr(track.extras, "requester_name", requester_name)
        requester_avatar = getattr(track.extras, "requester_avatar", requester_avatar)
        requester_tag = getattr(track.extras, "requester_tag", "")

    embed.set_author(
        name=f"Requested by {requester_name}",
        icon_url=requester_avatar,
    )

    # ============================================================
    # NOW PLAYING
    # ============================================================
    if track:
        embed.add_field(
            name="🎶 Now Playing",
            value=f"[{track.title}]({track.uri})" if track.uri else track.title,
            inline=False,
        )

        embed.add_field(
            name="🎧 Requested By",
            value=f"{requester_name}#{requester_tag}" if requester_tag else requester_name,
            inline=True,
        )

        # Duration (safe for live streams)
        if getattr(track, "length", 0):
            minutes = track.length // 60000
            seconds = (track.length // 1000) % 60
            duration = f"{minutes}:{seconds:02d}"
        else:
            duration = "Live"

        embed.add_field(
            name="⏱ Duration",
            value=duration,
            inline=True,
        )

        embed.add_field(
            name="✍ Artist",
            value=track.author or "Unknown Artist",
            inline=True,
        )

        # Thumbnail (safe)
        if getattr(track, "artwork", None):
            embed.set_thumbnail(url=track.artwork)

    else:
        embed.add_field(
            name="🎶 Player Status",
            value="Nothing is playing right now.\nUse `/play` to start music.",
            inline=False,
        )

    # ============================================================
    # FOOTER (SAFE)
    # ============================================================
    queue_size = len(state.queue) if state and state.queue else 0

    embed.set_footer(
        text=(
            f"Autoplay: {'ON' if state.autoplay else 'OFF'} • "
            f"Loop: {'ON' if state.loop else 'OFF'} • "
            f"Queue: {queue_size}\n"
            "© 2025 Mac GunJon • Music System"
        ),
        icon_url=requester_avatar,
    )

    return embed

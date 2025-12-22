import asyncio
import random
import discord
import wavelink
from discord.ui import View
from music.state import music_states
from music.embed import build_player_embed


# ================= CONTROLS =================
class MusicControlView(View):

    def __init__(self, player: wavelink.Player, guild_id: int):
        super().__init__(timeout=None)
        self.player = player
        self.guild_id = guild_id
        self._sync_buttons()

    # ------------------ USER CHECK ------------------
    async def _check_user(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.voice or interaction.user.voice.channel != self.player.channel:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="Access Restricted",
                        description="To use this control, please join the same voice channel as the bot.",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
            return False
        return True

    # ------------------ BUTTON STATE SYNC ------------------
    def _sync_buttons(self):
        state = music_states.get(self.guild_id)

        # ✅ FIX: Wavelink compatible connection check
        has_player = bool(self.player and self.player.channel)
        has_queue = bool(state and state.queue)
        has_previous = bool(state and state.previous)

        for item in self.children:
            if item.label in ("🔉 Down", "🔊 Up"):
                item.disabled = not has_player

            elif item.label == "⏮ Back":
                item.disabled = not has_previous

            elif item.label in ("⏸ Pause", "▶ Resume"):
                item.disabled = not has_player

            elif item.label == "⏭ Skip":
                item.disabled = not has_player

            elif item.label == "🔀 Shuffle":
                item.disabled = not has_queue

            elif item.label == "🔁 Loop":
                item.disabled = not has_player

            elif item.label == "🔄 Autoplay":
                item.disabled = not has_player

            elif item.label == "⏹ Stop":
                item.disabled = not has_player

    # ------------------ VOLUME DOWN ------------------
    @discord.ui.button(label="🔉 Down", style=discord.ButtonStyle.secondary)
    async def volume_down(self, interaction: discord.Interaction, _):
        if not await self._check_user(interaction):
            return

        new_volume = max(1, self.player.volume - 10)
        await self.player.set_volume(new_volume)

        self._sync_buttons()
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Audio Level Changed",
                description=f"Playback volume successfully adjusted to **{new_volume}%**.",
                color=discord.Color.blurple(),
            ),
            ephemeral=True,
        )

    # ------------------ VOLUME UP ------------------
    @discord.ui.button(label="🔊 Up", style=discord.ButtonStyle.secondary)
    async def volume_up(self, interaction: discord.Interaction, _):
        if not await self._check_user(interaction):
            return

        new_volume = min(1000, self.player.volume + 10)
        await self.player.set_volume(new_volume)

        self._sync_buttons()
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Audio Level Changed",
                description=f"Playback volume successfully adjusted to **{new_volume}%**.",
                color=discord.Color.blurple(),
            ),
            ephemeral=True,
        )

    # ------------------ BACK ------------------
    @discord.ui.button(label="⏮ Back", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, _):
        if not await self._check_user(interaction):
            return

        state = music_states.get(self.guild_id)
        if not state or not state.previous:
            embed = discord.Embed(
                title="⏮ Playback Reverted",
                description="No previously played track is available.",
                color=discord.Color.red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # 🔒 Disable autoplay temporarily
        state.autoplay_enabled = False

        # ⛔ DO NOT push current track into queue
        state.current = state.previous
        state.previous = None
        state.autoplay_seed = state.current

        # ✅ Force replace current track (prevents loop)
        await self.player.play(state.current, replace=True)

        self._sync_buttons()

        embed = discord.Embed(
            title="⏮ Playback Reverted",
            description=f"Now playing:\n🎵 **{state.current.title}**",
            color=discord.Color.green(),
        )
        embed.set_footer(text="Manual Control • Back")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ------------------ PAUSE / RESUME ------------------
    @discord.ui.button(label="⏸ Pause", style=discord.ButtonStyle.primary)
    async def pause_resume(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not await self._check_user(interaction):
            return

        if self.player.paused:
            await self.player.pause(False)
            button.label = "⏸ Pause"
        else:
            await self.player.pause(True)
            button.label = "▶ Resume"

        self._sync_buttons()
        await interaction.response.edit_message(view=self)

    # ------------------ SKIP ------------------
    @discord.ui.button(label="⏭ Skip", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, _):
        if not await self._check_user(interaction):
            return

        await self.player.stop()

        self._sync_buttons()
        await interaction.response.send_message(
            embed=discord.Embed(
                title="⏭ Track Skipped",
                description="The current track has been skipped successfully.",
                color=discord.Color.blurple(),
            ),
            ephemeral=True,
        )

    # ------------------ SHUFFLE ------------------
    @discord.ui.button(label="🔀 Shuffle", style=discord.ButtonStyle.secondary)
    async def shuffle(self, interaction: discord.Interaction, _):
        if not await self._check_user(interaction):
            return

        state = music_states.get(self.guild_id)
        if not state or not state.queue:
            return

        random.shuffle(state.queue)

        self._sync_buttons()
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🔀 Queue Shuffled",
                description="Tracks in the queue have been shuffled.",
                color=discord.Color.blurple(),
            ),
            ephemeral=True,
        )

    # ------------------ LOOP ------------------
    @discord.ui.button(label="🔁 Loop", style=discord.ButtonStyle.secondary)
    async def loop(self, interaction: discord.Interaction, _):
        if not await self._check_user(interaction):
            return

        state = music_states.get(self.guild_id)
        if not state:
            return

        state.loop = not state.loop

        self._sync_buttons()
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🔁 Playback Loop",
                description=f"Continuous playback is now **{'active' if state.loop else 'inactive'}**.",
                color=discord.Color.green() if state.loop else discord.Color.red(),
            ),
            ephemeral=True,
        )

    # ------------------ AUTOPLAY ------------------
    @discord.ui.button(label="🔄 Autoplay", style=discord.ButtonStyle.secondary)
    async def autoplay(self, interaction: discord.Interaction, _):
        if not await self._check_user(interaction):
            return

        state = music_states.get(self.guild_id)
        if not state:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Music Error",
                    description="Music state not found. Please start playback using **/play**.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
            return

        # 🔁 Toggle autoplay
        state.autoplay = not state.autoplay

        if state.autoplay and not state.autoplay_seed and state.current:
            state.autoplay_seed = state.current

        # 🔄 Sync buttons
        self._sync_buttons()

        # 🔥 UPDATE MAIN CONTROL PANEL EMBED
        if state.message:
            await state.message.edit(
                embed=build_player_embed(state),
                view=self
            )

        # 🔔 Ephemeral confirmation
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🔄 Autoplay",
                description=(
                    "Smart autoplay is now **ENABLED**."
                    if state.autoplay
                    else "Smart autoplay is now **DISABLED**."
                ),
                color=discord.Color.green() if state.autoplay else discord.Color.red(),
            ),
            ephemeral=True,
        )

    # ------------------ STOP ------------------
    @discord.ui.button(label="⏹ Stop", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, _):
        if not await self._check_user(interaction):
            return

        await self.player.disconnect()
        music_states.pop(self.guild_id, None)

        self._sync_buttons()
        await interaction.response.edit_message(view=None)
        await interaction.followup.send(
            embed=discord.Embed(
                title="Music Stopped",
                description="Playback has ended and the bot has left the voice channel.",
                color=discord.Color.red(),
            ),
            ephemeral=True,
        )

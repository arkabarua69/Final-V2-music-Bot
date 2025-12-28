import random
import discord
import wavelink
from discord.ui import View, button

from music.state import music_states
from music.embed import build_player_embed
from music.cooldown import cooldown_manager


class MusicControlView(View):
    """
    Unified production-grade music control panel
    Handles:
    - Back / Skip / Stop safely
    - Autoplay conflict prevention
    - Cooldown & anti-spam
    """

    def __init__(self, player: wavelink.Player, guild_id: int):
        super().__init__(timeout=None)
        self.player = player
        self.guild_id = guild_id
        self._sync_buttons()

    # ==================================================
    # COMMON HELPERS
    # ==================================================
    async def _defer(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

    async def _cooldown(self, interaction, key: str, seconds: float) -> bool:
        remaining = cooldown_manager.check(interaction.user.id, key, seconds)
        if remaining is not None:
            await self._defer(interaction)
            await interaction.followup.send(
                embed=discord.Embed(
                    title="⏳ Cooldown Active",
                    description=f"Please wait **{remaining:.1f}s** before using this control again.",
                    color=discord.Color.orange(),
                ),
                ephemeral=True,
            )
            return True
        return False

    async def _check_user(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.voice or not self.player or not self.player.channel:
            await self._defer(interaction)
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Access Denied",
                    description="You must be connected to a voice channel.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
            return False

        if interaction.user.voice.channel != self.player.channel:
            await self._defer(interaction)
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Access Denied",
                    description="You must be in the **same voice channel** as the bot.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
            return False

        return True

    def _sync_buttons(self):
        state = music_states.get(self.guild_id)

        has_player = bool(self.player and self.player.channel)
        has_queue = bool(state and state.queue)
        has_previous = bool(state and state.previous)

        for item in self.children:
            if item.label in ("🔉 Down", "🔊 Up"):
                item.disabled = not has_player
            elif item.label == "⏮ Back":
                item.disabled = not has_previous
            elif item.label in ("⏸ Pause", "▶ Resume", "⏭ Skip", "🔁 Loop", "🔄 Autoplay", "⏹ Stop"):
                item.disabled = not has_player
            elif item.label == "🔀 Shuffle":
                item.disabled = not has_queue

    async def _update_panel(self):
        state = music_states.get(self.guild_id)
        if state and state.message:
            try:
                await state.message.edit(
                    embed=build_player_embed(state),
                    view=self,
                )
            except Exception:
                pass

    # ==================================================
    # VOLUME DOWN
    # ==================================================
    @button(label="🔉 Down", style=discord.ButtonStyle.secondary)
    async def volume_down(self, interaction: discord.Interaction, _):
        if not await self._check_user(interaction):
            return
        if await self._cooldown(interaction, "volume", 1.5):
            return

        await self._defer(interaction)

        new_volume = max(1, getattr(self.player, "volume", 100) - 10)
        await self.player.set_volume(new_volume)

        await interaction.followup.send(
            embed=discord.Embed(
                title="🔉 Volume Changed",
                description=f"Volume set to **{new_volume}%**",
                color=discord.Color.blurple(),
            ),
            ephemeral=True,
        )

    # ==================================================
    # VOLUME UP
    # ==================================================
    @button(label="🔊 Up", style=discord.ButtonStyle.secondary)
    async def volume_up(self, interaction: discord.Interaction, _):
        if not await self._check_user(interaction):
            return
        if await self._cooldown(interaction, "volume", 1.5):
            return

        await self._defer(interaction)

        new_volume = min(200, getattr(self.player, "volume", 100) + 10)
        await self.player.set_volume(new_volume)

        await interaction.followup.send(
            embed=discord.Embed(
                title="🔊 Volume Changed",
                description=f"Volume set to **{new_volume}%**",
                color=discord.Color.blurple(),
            ),
            ephemeral=True,
        )

    # ==================================================
    # BACK
    # ==================================================
    @button(label="⏮ Back", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, _):
        if not await self._check_user(interaction):
            return
        if await self._cooldown(interaction, "back", 3):
            return

        await self._defer(interaction)

        state = music_states.get(self.guild_id)
        if not state or not state.previous:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="⏮ No Previous Track",
                    description="There is no previously played track.",
                    color=discord.Color.orange(),
                ),
                ephemeral=True,
            )

        # 🔒 ONE-TIME BACK (ANTI-LOOP)
        state.manual_action = "back"

        back_track = state.previous

        # ❗ CRITICAL FIX
        state.previous = None  # 🚫 prevents loop
        state.current = back_track
        state.autoplay_seed = back_track

        await self.player.play(back_track, replace=True)
        await self._update_panel()

        await interaction.followup.send(
            embed=discord.Embed(
                title="⏮ Playing Previous Track",
                description=f"Now playing **{back_track.title}**",
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )

    # ==================================================
    # PAUSE / RESUME
    # ==================================================
    @button(label="⏸ Pause", style=discord.ButtonStyle.primary)
    async def pause_resume(self, interaction: discord.Interaction, button):
        if not await self._check_user(interaction):
            return
        if await self._cooldown(interaction, "pause", 2):
            return

        await self._defer(interaction)

        state = music_states.get(self.guild_id)
        if state:
            state.manual_action = True

        if self.player.paused:
            await self.player.pause(False)
            button.label = "⏸ Pause"
            msg = "▶ Playback resumed."
        else:
            await self.player.pause(True)
            button.label = "▶ Resume"
            msg = "⏸ Playback paused."

        await interaction.message.edit(view=self)

        await interaction.followup.send(
            embed=discord.Embed(
                title="Playback Control",
                description=msg,
                color=discord.Color.blurple(),
            ),
            ephemeral=True,
        )

    # ==================================================
    # SKIP
    # ==================================================
    @button(label="⏭ Skip", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, _):
        if not await self._check_user(interaction):
            return
        if await self._cooldown(interaction, "skip", 3):
            return

        await self._defer(interaction)

        state = music_states.get(self.guild_id)

        # 🔓 SKIP = NOT manual (autoplay allowed)
        if state:
            state.manual_action = False

        await self.player.stop()

        await interaction.followup.send(
            embed=discord.Embed(
                title="⏭ Track Skipped",
                description="Skipping to the next track.",
                color=discord.Color.blurple(),
            ),
            ephemeral=True,
        )

    # ==================================================
    # SHUFFLE
    # ==================================================
    @button(label="🔀 Shuffle", style=discord.ButtonStyle.secondary)
    async def shuffle(self, interaction: discord.Interaction, _):
        if not await self._check_user(interaction):
            return
        if await self._cooldown(interaction, "shuffle", 3):
            return

        await self._defer(interaction)

        state = music_states.get(self.guild_id)
        if not state or not state.queue:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Queue Empty",
                    description="There are no tracks to shuffle.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        random.shuffle(state.queue)

        await interaction.followup.send(
            embed=discord.Embed(
                title="🔀 Queue Shuffled",
                description="The queue order has been randomized.",
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )

    # ==================================================
    # LOOP
    # ==================================================
    @button(label="🔁 Loop", style=discord.ButtonStyle.secondary)
    async def loop(self, interaction: discord.Interaction, _):
        if not await self._check_user(interaction):
            return
        if await self._cooldown(interaction, "loop", 3):
            return

        await self._defer(interaction)

        state = music_states.get(self.guild_id)
        state.loop = not state.loop

        await self._update_panel()

        await interaction.followup.send(
            embed=discord.Embed(
                title="🔁 Loop Mode",
                description=f"Loop is now **{'ENABLED' if state.loop else 'DISABLED'}**",
                color=discord.Color.green() if state.loop else discord.Color.red(),
            ),
            ephemeral=True,
        )

    # ==================================================
    # AUTOPLAY
    # ==================================================
    @button(label="🔄 Autoplay", style=discord.ButtonStyle.secondary)
    async def autoplay(self, interaction: discord.Interaction, _):
        if not await self._check_user(interaction):
            return
        if await self._cooldown(interaction, "autoplay", 3):
            return

        await self._defer(interaction)

        state = music_states.get(self.guild_id)
        state.autoplay = not state.autoplay

        if state.autoplay and not state.autoplay_seed and state.current:
            state.autoplay_seed = state.current

        await self._update_panel()

        await interaction.followup.send(
            embed=discord.Embed(
                title="🔄 Autoplay",
                description=f"Autoplay is now **{'ENABLED' if state.autoplay else 'DISABLED'}**",
                color=discord.Color.green() if state.autoplay else discord.Color.red(),
            ),
            ephemeral=True,
        )

    # ==================================================
    # STOP
    # ==================================================
    @button(label="⏹ Stop", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, _):
        if not await self._check_user(interaction):
            return
        if await self._cooldown(interaction, "stop", 5):
            return

        await self._defer(interaction)

        state = music_states.get(self.guild_id)
        if state:
            state.manual_action = True

        try:
            await self.player.disconnect(force=True)
        except Exception:
            pass

        music_states.pop(self.guild_id, None)

        try:
            await interaction.message.edit(view=None)
        except Exception:
            pass

        await interaction.followup.send(
            embed=discord.Embed(
                title="⏹ Music Stopped",
                description="Playback stopped and the bot has left the voice channel.",
                color=discord.Color.red(),
            ),
            ephemeral=True,
        )

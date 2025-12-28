from typing import List, Optional
import wavelink


class MusicState:
    """
    Production-grade music state container
    One instance per guild
    """

    __slots__ = (
        "player",
        "queue",
        "current",
        "previous",
        "loop",
        "autoplay",
        "autoplay_seed",
        "message",

        # 🔥 REQUIRED FOR BACK / MANUAL ACTION FIX
        "manual_action",
    )

    def __init__(self):
        self.player: Optional[wavelink.Player] = None
        self.queue: List[wavelink.Playable] = []

        self.current: Optional[wavelink.Playable] = None
        self.previous: Optional[wavelink.Playable] = None

        self.loop: bool = False
        self.autoplay: bool = False
        self.autoplay_seed: Optional[wavelink.Playable] = None

        # Unified control panel message
        self.message = None

        # 🔥 MANUAL ACTION FLAG
        # Used to prevent autoplay after Back / Skip / Stop
        self.manual_action: bool = False

    # ============================================================
    # STATE HELPERS
    # ============================================================
    def reset(self):
        """Fully reset state (used on disconnect / stop)"""
        self.queue.clear()
        self.previous = None
        self.current = None
        self.autoplay_seed = None
        self.loop = False
        self.autoplay = False
        self.manual_action = None

    def is_playing(self) -> bool:
        return self.player is not None and self.player.playing

    def has_queue(self) -> bool:
        return bool(self.queue)


# ============================================================
# GLOBAL MUSIC STATE REGISTRY
# ============================================================
music_states: dict[int, MusicState] = {}

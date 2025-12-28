import time
from collections import defaultdict


class ButtonCooldown:
    """
    Per-user per-button cooldown system
    Prevents button spam safely
    """

    def __init__(self):
        self._cooldowns = defaultdict(dict)

    def check(self, user_id: int, action: str, cooldown: float):
        """
        Returns remaining cooldown time if blocked
        Returns None if allowed
        """
        now = time.monotonic()
        last_used = self._cooldowns[user_id].get(action)

        if last_used and (now - last_used) < cooldown:
            return round(cooldown - (now - last_used), 1)

        self._cooldowns[user_id][action] = now
        return None


# GLOBAL INSTANCE
cooldown_manager = ButtonCooldown()

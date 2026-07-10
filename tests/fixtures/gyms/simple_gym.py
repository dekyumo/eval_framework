class CounterGym:
    def __init__(self, config):
        self.remaining = int(config.get("steps", 2))

    def decrement(self, amount: int = 1) -> str:
        """Decrease the remaining step counter by amount."""
        self.remaining -= amount
        return f"remaining={self.remaining}"

    def is_done(self) -> bool:
        """Return True when no steps remain."""
        return self.remaining <= 0

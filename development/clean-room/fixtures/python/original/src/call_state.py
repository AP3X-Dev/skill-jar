"""Per-call SOP state — rebuilds matched types per chunk (not accumulated)."""


class CallSopState:
    def __init__(self):
        self.matched_trade_types = []
        self.matched_fee_tiers = []
        self.membership_tier = None

    def apply_alerts(self, chunk) -> None:
        # Rebuild per chunk — NOT accumulated.
        self.matched_trade_types = [a.trade for a in chunk.alerts if a.trade]
        self.matched_fee_tiers = [a.fee for a in chunk.alerts if a.fee]
        # membership_tier: latest-wins
        for a in chunk.alerts:
            if a.tier:
                self.membership_tier = a.tier

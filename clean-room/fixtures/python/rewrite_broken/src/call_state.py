"""Per-call SOP state — BROKEN: appends instead of rebuilds (B pattern)."""


class CallSopState:
    def __init__(self):
        self.matched_trade_types = []
        self.matched_fee_tiers = []
        self.membership_tier = None

    def apply_alerts(self, chunk) -> None:
        # BROKEN: accumulates across chunks instead of rebuilding per-chunk.
        for a in chunk.alerts:
            if a.trade:
                self.matched_trade_types.append(a.trade)
            if a.fee:
                self.matched_fee_tiers.append(a.fee)
            if a.tier:
                self.membership_tier = a.tier

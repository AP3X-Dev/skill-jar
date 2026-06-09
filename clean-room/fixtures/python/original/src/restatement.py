"""Restatement check — relies on private _word_overlap helper."""

WORD_OVERLAP_THRESHOLD = 0.7


def _word_overlap(a: str, b: str) -> float:
    # Private helper (C pattern — encodes the 70% threshold behavior).
    sa = set(a.lower().split())
    sb = set(b.lower().split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / max(len(sa), len(sb))


def check_restatement(prev: str, curr: str) -> bool:
    return _word_overlap(prev, curr) >= WORD_OVERLAP_THRESHOLD

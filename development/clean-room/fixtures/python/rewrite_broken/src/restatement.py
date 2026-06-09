"""Restatement check — BROKEN: _word_overlap helper removed (C pattern)."""


def check_restatement(prev: str, curr: str) -> bool:
    # Naive stub — lost the 70% word-overlap threshold behavior.
    return prev.strip() == curr.strip()

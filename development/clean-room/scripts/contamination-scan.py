#!/usr/bin/env python3
"""Scan the rewrite for verbatim terms from the original (clean-room firewall audit).

The fingerprint file is produced by a research subagent that reads the target
and extracts terms that would be suspicious if they appeared verbatim in the
rewrite. Good fingerprint entries:
  - Rare, distinctive identifiers (internal class/function names unlikely to
    be re-invented by chance)
  - Distinctive error message phrasings
  - Unique comment phrasings (if comments were in the original)
  - Hand-picked magic numbers or string constants

Skip fingerprint entries that are genuinely part of the public contract (those
are SUPPOSED to match). The research subagent should exclude those.

Exit codes:
  0 = no hits
  1 = hits found (contamination suspected)
  2 = usage error

Usage:
  contamination-scan.py <fingerprint.txt> <rewrite-root>
"""
import re
import sys
from pathlib import Path

IGNORED_DIRS = {
    ".git", "node_modules", "target", "dist", "build", "out",
    "__pycache__", "clean-room", ".venv", "venv", ".next", ".nuxt",
    ".turbo", "coverage", ".pytest_cache", ".mypy_cache", ".tox",
}
TEXT_EXTS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".go", ".rs", ".java", ".kt", ".swift", ".scala",
    ".c", ".cc", ".cpp", ".h", ".hpp", ".cs", ".m", ".mm",
    ".rb", ".php", ".ex", ".exs", ".erl", ".hs", ".ml",
    ".md", ".txt", ".yaml", ".yml", ".toml", ".json", ".ini", ".cfg",
    ".sh", ".bash", ".zsh", ".fish", ".ps1",
    ".sql", ".graphql", ".proto",
}


def load_fingerprint(path: Path) -> list[str]:
    terms = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        terms.append(s)
    return terms


def walk(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in TEXT_EXTS:
            continue
        if any(part in IGNORED_DIRS for part in p.parts):
            continue
        yield p


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: contamination-scan.py <fingerprint.txt> <rewrite-root>", file=sys.stderr)
        return 2

    fp_path = Path(sys.argv[1])
    root = Path(sys.argv[2])
    if not fp_path.is_file():
        print(f"fingerprint not found: {fp_path}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"rewrite root not a directory: {root}", file=sys.stderr)
        return 2

    terms = load_fingerprint(fp_path)
    if not terms:
        print("fingerprint is empty — nothing to scan for", file=sys.stderr)
        return 2

    patterns = [(t, re.compile(r"\b" + re.escape(t) + r"\b")) for t in terms]
    hits = 0

    for f in walk(root):
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for lineno, line in enumerate(content.splitlines(), 1):
            for term, pat in patterns:
                if pat.search(line):
                    snippet = line.strip()
                    if len(snippet) > 140:
                        snippet = snippet[:140] + "..."
                    print(f"{f}:{lineno}: {term!r} :: {snippet}")
                    hits += 1

    if hits:
        print(f"\n{hits} contamination hit(s) found across {len(terms)} tracked term(s)", file=sys.stderr)
        return 1
    print(f"no contamination detected ({len(terms)} term(s) checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

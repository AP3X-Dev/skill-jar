#!/usr/bin/env python3
"""Read-only inventory aid for guardrail-forge discovery.

The output is deterministic evidence hints, not architecture policy. The script
does not read secret files, install dependencies, or modify the target unless an
explicit --output path is supplied.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


SKIP_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", "node_modules", "vendor",
    "dist", "build", "target", "coverage", ".next", ".cache", "__pycache__",
    ".venv", "venv", ".tox", ".mypy_cache", ".pytest_cache",
}
SECRET_NAMES = {
    ".env", "credentials.json", "serviceaccountkey.json", "id_rsa", "id_ed25519",
}
LANGUAGE_BY_EXT = {
    ".c": "C", ".cc": "C++", ".cpp": "C++", ".cs": "C#", ".css": "CSS",
    ".ex": "Elixir", ".exs": "Elixir", ".go": "Go", ".h": "C/C++ Header",
    ".hpp": "C++ Header", ".html": "HTML", ".java": "Java", ".js": "JavaScript",
    ".jsx": "JavaScript", ".kt": "Kotlin", ".kts": "Kotlin", ".php": "PHP",
    ".py": "Python", ".rb": "Ruby", ".rs": "Rust", ".scala": "Scala",
    ".sql": "SQL", ".swift": "Swift", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".vue": "Vue", ".svelte": "Svelte",
}
MANIFEST_NAMES = {
    "package.json", "pnpm-workspace.yaml", "yarn.lock", "package-lock.json",
    "pnpm-lock.yaml", "pyproject.toml", "requirements.txt", "poetry.lock",
    "Pipfile", "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
    "build.gradle.kts", "composer.json", "Gemfile", "mix.exs", "Makefile",
}
ENTRYPOINT_NAMES = {
    "main.py", "app.py", "server.py", "manage.py", "main.go", "main.rs",
    "main.ts", "main.js", "index.ts", "index.js", "Program.cs", "Application.java",
}
DB_NAMES = {
    "schema.prisma", "alembic.ini", "sequelize.config.js", "knexfile.js",
    "drizzle.config.ts", "database.yml", "ormconfig.json",
}
ARCH_TOKENS = ("architecture", "architectural", "adr", "decision", "design", "boundary")
AUTH_TOKENS = ("auth", "permission", "rbac", "tenant", "session", "policy")


def rel(path, root):
    return path.relative_to(root).as_posix()


def link_like(path):
    """Treat POSIX symlinks and Windows directory junctions as links."""
    return path.is_symlink() or (
        hasattr(path, "is_junction") and path.is_junction()
    )


def contained_entry(root, path, require_file):
    """Reject linked ancestors and entries that resolve outside the inventory root."""
    root = root.resolve()
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if link_like(cursor):
            return False
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        return False
    if root not in resolved.parents:
        return False
    return resolved.is_file() if require_file else resolved.is_dir()


def walk_files(root, max_files):
    files = []
    truncated = False
    for current, dirnames, filenames in os.walk(str(root), followlinks=False):
        current_path = Path(current)
        dirnames[:] = sorted(
            name for name in dirnames
            if name not in SKIP_DIRS
            and contained_entry(root, current_path / name, require_file=False)
        )
        for name in sorted(filenames):
            lowered = name.lower()
            if lowered in SECRET_NAMES or lowered.startswith(".env"):
                continue
            path = current_path / name
            if not contained_entry(root, path, require_file=True):
                continue
            files.append(path)
            if len(files) >= max_files:
                truncated = True
                return files, truncated
    return files, truncated


def git_value(root, args):
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def package_json_info(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"path": path.name, "parse_error": True}
    scripts = data.get("scripts") if isinstance(data.get("scripts"), dict) else {}
    dependency_names = set()
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        values = data.get(key)
        if isinstance(values, dict):
            dependency_names.update(values)
    framework_markers = {
        "next", "react", "vue", "nuxt", "svelte", "@sveltejs/kit", "express",
        "fastify", "nestjs", "@nestjs/core", "electron", "prisma", "@prisma/client",
        "trpc", "@trpc/server", "angular", "@angular/core",
    }
    return {
        "path": path.name,
        "package_name": data.get("name"),
        "private": data.get("private"),
        "workspaces": data.get("workspaces"),
        "scripts": {key: scripts[key] for key in sorted(scripts)},
        "framework_hints": sorted(dependency_names.intersection(framework_markers)),
    }


def likely_commands(root, files):
    commands = []
    for path in files:
        name = path.name
        if name == "package.json":
            info = package_json_info(path)
            scripts = info.get("scripts", {})
            for script_name in ("test", "lint", "typecheck", "check", "build"):
                if script_name in scripts:
                    commands.append("npm run %s" % script_name)
        elif name == "pyproject.toml":
            commands.extend(["python -m pytest", "python -m mypy .", "ruff check ."])
        elif name == "Cargo.toml":
            commands.extend(["cargo test", "cargo clippy --all-targets", "cargo build"])
        elif name == "go.mod":
            commands.extend(["go test ./...", "go vet ./..."])
        elif name == "Makefile":
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for target in re.findall(r"^([A-Za-z0-9_.-]+):(?:\s|$)", text, flags=re.M):
                if target in {"test", "lint", "check", "typecheck", "build", "verify"}:
                    commands.append("make %s" % target)
    return sorted(set(commands))


def inspect(root, max_files=200000):
    root = root.resolve()
    files, truncated = walk_files(root, max_files)
    languages = Counter()
    manifests = []
    entrypoints = []
    instructions = []
    architecture_docs = []
    ci_files = []
    database_files = []
    auth_candidates = []
    package_jsons = []

    for path in files:
        relative = rel(path, root)
        suffix = path.suffix.lower()
        if suffix in LANGUAGE_BY_EXT:
            languages[LANGUAGE_BY_EXT[suffix]] += 1
        if path.name in MANIFEST_NAMES:
            manifests.append(relative)
        if path.name in ENTRYPOINT_NAMES or relative.startswith(("src/app/", "app/")) and path.name in {"route.ts", "page.tsx"}:
            entrypoints.append(relative)
        if path.name in {"AGENTS.md", "CLAUDE.md"}:
            instructions.append(relative)
        lowered = relative.lower()
        if path.suffix.lower() in {".md", ".txt", ".rst"} and any(token in lowered for token in ARCH_TOKENS):
            architecture_docs.append(relative)
        if relative.startswith((".github/workflows/", ".gitlab-ci")) or path.name in {"Jenkinsfile", "azure-pipelines.yml"}:
            ci_files.append(relative)
        if path.name in DB_NAMES or "/migrations/" in "/%s/" % lowered:
            database_files.append(relative)
        if any(token in path.stem.lower() for token in AUTH_TOKENS):
            auth_candidates.append(relative)
        if path.name == "package.json":
            info = package_json_info(path)
            info["path"] = relative
            package_jsons.append(info)

    branch = git_value(root, ["branch", "--show-current"])
    head = git_value(root, ["rev-parse", "HEAD"])
    status = git_value(root, ["status", "--porcelain"])
    recent = git_value(root, ["log", "-n", "20", "--pretty=format:%h %s"])
    return {
        "schema": "guardrail-forge-inventory-v1",
        "notice": "Inventory hints only. Observed files and commands are not approved architecture policy.",
        "root": str(root),
        "scan": {"file_count": len(files), "truncated": truncated, "max_files": max_files},
        "git": {
            "branch": branch,
            "head": head,
            "dirty": bool(status),
            "recent_commit_subjects": recent.splitlines() if recent else [],
        },
        "languages_by_file_count": dict(sorted(languages.items(), key=lambda item: (-item[1], item[0]))),
        "manifests": sorted(manifests),
        "package_json": sorted(package_jsons, key=lambda item: item["path"]),
        "candidate_commands_unverified": likely_commands(root, files),
        "runtime_entrypoint_candidates": sorted(entrypoints)[:200],
        "instruction_files": sorted(instructions),
        "architecture_document_candidates": sorted(architecture_docs)[:200],
        "ci_files": sorted(ci_files),
        "database_and_migration_candidates": sorted(database_files)[:200],
        "auth_tenancy_policy_candidates": sorted(auth_candidates)[:200],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only inventory for guardrail-forge discovery.")
    parser.add_argument("--root", default=".", help="target repository root")
    parser.add_argument("--max-files", type=int, default=200000)
    parser.add_argument("--output", help="optional JSON output path; stdout when omitted")
    args = parser.parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print("inventory error: root is not a directory: %s" % root, file=sys.stderr)
        return 2
    if args.max_files < 1:
        print("inventory error: --max-files must be positive", file=sys.stderr)
        return 2
    report = inspect(root, args.max_files)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print("wrote inventory: %s" % output)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

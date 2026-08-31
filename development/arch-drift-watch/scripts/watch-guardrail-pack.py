#!/usr/bin/env python3
"""Fail-closed operational adapter for a guardrail-forge policy pack."""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath


SHA_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
GLOB_CHARS = set("*?[]{}")
CURSOR_RELATIVE = "agent-state/architecture-guardrail/watch-cursor.json"
sys.dont_write_bytecode = True


class DuplicateKeyError(ValueError):
    pass


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError("duplicate mapping key: %s" % key)
        result[key] = value
    return result


def strict_json(text):
    return json.loads(text, object_pairs_hook=unique_object)


def canonical_sha256(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def link_like(path):
    return path.is_symlink() or (
        hasattr(path, "is_junction") and path.is_junction()
    )


def safe_relative_path(value):
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(character in value for character in GLOB_CHARS)
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or ":" in value
    ):
        return False
    normalized = value.replace("\\", "/")
    posix = PurePosixPath(normalized)
    windows = PureWindowsPath(value)
    return not (
        posix.is_absolute()
        or windows.is_absolute()
        or windows.drive
        or windows.root
        or ".." in posix.parts
        or "." in posix.parts
    )


def contained_file(root, relative):
    if not safe_relative_path(relative):
        return None
    root = root.resolve()
    parts = PurePosixPath(relative.replace("\\", "/")).parts
    cursor = root
    for part in parts:
        cursor = cursor / part
        if link_like(cursor):
            return None
    try:
        resolved = (root / Path(*parts)).resolve(strict=True)
    except OSError:
        return None
    if root not in resolved.parents or not resolved.is_file():
        return None
    return resolved


def run(command, root):
    try:
        environment = {
            key: value for key, value in os.environ.items()
            if not key.upper().startswith("GIT_")
        }
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONHASHSEED"] = "0"
        return subprocess.run(
            command, cwd=str(root), capture_output=True, check=False,
            env=environment,
        )
    except OSError as exc:
        return None, str(exc)


def is_git_worktree_root(root):
    """Require sanitized Git itself to identify this exact target root."""
    result = run(["git", "rev-parse", "--show-toplevel"], root)
    if isinstance(result, tuple) or result.returncode != 0:
        return False
    try:
        return Path(result.stdout.decode("utf-8").strip()).resolve() == root.resolve()
    except (OSError, UnicodeError):
        return False


def committed_file_matches(root, relative, normalize_platform_eol=False):
    """Compare working bytes with raw HEAD bytes without invoking clean filters."""
    path = contained_file(root, relative)
    if path is None:
        return False
    head = run(["git", "show", "HEAD:%s" % relative], root)
    if isinstance(head, tuple) or head.returncode != 0:
        return False
    try:
        working = path.read_bytes()
        committed = head.stdout
        if normalize_platform_eol:
            working = working.replace(b"\r\n", b"\n")
            committed = committed.replace(b"\r\n", b"\n")
        return working == committed
    except OSError:
        return False
def working_tree_files(root):
    """Enumerate real repository files without trusting Git index visibility hints."""
    root = root.resolve()
    files = []
    for current, dirnames, filenames in os.walk(str(root), followlinks=False):
        current_path = Path(current)
        kept_directories = []
        for name in sorted(dirnames):
            if name == ".git":
                continue
            candidate = current_path / name
            if link_like(candidate):
                return None, "working-tree snapshot directory is symlinked or junctioned: %s" % (
                    candidate.relative_to(root).as_posix()
                )
            try:
                resolved = candidate.resolve(strict=True)
            except OSError:
                return None, "working-tree snapshot directory is missing: %s" % (
                    candidate.relative_to(root).as_posix()
                )
            if root not in resolved.parents or not resolved.is_dir():
                return None, "working-tree snapshot directory escaped repository: %s" % (
                    candidate.relative_to(root).as_posix()
                )
            kept_directories.append(name)
        dirnames[:] = kept_directories
        for name in sorted(filenames):
            if name == ".git":
                continue
            candidate = current_path / name
            relative = candidate.relative_to(root).as_posix()
            if not safe_relative_path(relative):
                return None, "unsafe working-tree path during snapshot: %r" % relative
            contained = contained_file(root, relative)
            if contained is None:
                return None, "working-tree snapshot path is missing, non-file, or symlinked: %s" % relative
            files.append((os.fsencode(relative), contained))
    return files, None


def repository_snapshot(root):
    """Hash commit, Git state, and actual working-tree file bytes around a scan."""
    commands = [
        ["git", "rev-parse", "HEAD"],
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        ["git", "diff", "--no-ext-diff", "--binary", "HEAD", "--"],
    ]
    outputs = []
    for command in commands:
        result = run(command, root)
        if isinstance(result, tuple):
            return None, "git command failed to start: %s" % result[1]
        if result.returncode != 0:
            return None, "git snapshot command failed: %s" % " ".join(command)
        outputs.append(result.stdout)
    digest = hashlib.sha256()
    for output in outputs[:3]:
        digest.update(output)
        digest.update(b"\0")
    working_files, error = working_tree_files(root)
    if error:
        return None, error
    for raw_name, candidate in sorted(working_files, key=lambda item: item[0]):
        name = os.fsdecode(raw_name)
        digest.update(raw_name)
        digest.update(b"\0")
        try:
            digest.update(candidate.read_bytes())
        except OSError as exc:
            return None, "cannot hash working-tree snapshot path %s: %s" % (name, exc)
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest(), None


def validate_verifier_envelope(data, exit_code):
    errors = []
    if not isinstance(data, dict) or data.get("schema") != "guardrail-verification-v1":
        return ["verifier schema must be guardrail-verification-v1"]
    if data.get("complete") is not True:
        errors.append("verifier did not attest to a complete scan")
    if type(data.get("rules_run")) is not int or data.get("rules_run") < 1:
        errors.append("verifier must run at least one enforced rule")
    if not isinstance(data.get("authority_sha256"), str) or not SHA_RE.match(data.get("authority_sha256", "")):
        errors.append("verifier authority_sha256 is invalid")
    findings = data.get("findings")
    if not isinstance(findings, list):
        errors.append("verifier findings must be a list")
        findings = []
    seen = set()
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            errors.append("finding %d must be a mapping" % index)
            continue
        fingerprint = finding.get("fingerprint")
        if not isinstance(fingerprint, str) or not SHA_RE.match(fingerprint):
            errors.append("finding %d has invalid fingerprint" % index)
        elif fingerprint in seen:
            errors.append("finding %d duplicates fingerprint %s" % (index, fingerprint))
        else:
            seen.add(fingerprint)
        if not safe_relative_path(finding.get("path")):
            errors.append("finding %d has unsafe path" % index)
        for key in ("rule_id", "message", "kind", "owner", "remediation"):
            if not isinstance(finding.get(key), str) or not finding.get(key).strip():
                errors.append("finding %d needs %s" % (index, key))
    if data.get("errors") != []:
        errors.append("complete verifier output must contain an empty errors list")
    status = data.get("status")
    if exit_code == 0 and (status != "pass" or findings):
        errors.append("exit 0 requires pass status and no findings")
    elif exit_code == 1 and (status != "violation" or not findings):
        errors.append("exit 1 requires violation status and findings")
    elif exit_code not in {0, 1}:
        errors.append("verifier exit %d is blocked/indeterminate" % exit_code)
    return errors


def scan_once(root):
    before, error = repository_snapshot(root)
    if error:
        return None, error
    result = run(
        [sys.executable, "scripts/architecture/verify.py", "--repo-only", "--format", "json"],
        root,
    )
    if isinstance(result, tuple):
        return None, "verifier failed to start: %s" % result[1]
    after, error = repository_snapshot(root)
    if error:
        return None, error
    if before != after:
        return None, "repository changed during architecture scan"
    try:
        data = strict_json(result.stdout.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        return None, "verifier output is malformed JSON: %s" % str(exc).splitlines()[0]
    errors = validate_verifier_envelope(data, result.returncode)
    if errors:
        return None, "; ".join(errors)
    return data, None


def stable_scan(root):
    first, error = scan_once(root)
    if not error or error != "repository changed during architecture scan":
        return first, error
    return scan_once(root)


def load_cursor(path):
    try:
        data = strict_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        return None, "cursor cannot be read: %s" % str(exc).splitlines()[0]
    if not isinstance(data, dict) or data.get("version") != 1 or data.get("mode") != "guardrail-pack":
        return None, "cursor must be version 1 in guardrail-pack mode"
    authority = data.get("authority_sha256")
    if authority and (not isinstance(authority, str) or not SHA_RE.match(authority)):
        return None, "cursor authority_sha256 is invalid"
    observed = data.get("observed_fingerprints")
    if not isinstance(observed, list) or any(not isinstance(item, str) or not SHA_RE.match(item) for item in observed):
        return None, "cursor observed_fingerprints is invalid"
    if len(observed) != len(set(observed)):
        return None, "cursor observed_fingerprints contains duplicates"
    if authority:
        handoff = data.get("handoff")
        if not isinstance(handoff, dict):
            return None, "initialized cursor requires a committed handoff record"
        for key in ("decision_id", "approved_by", "approved_at"):
            if not isinstance(handoff.get(key), str) or not handoff.get(key).strip():
                return None, "cursor handoff.%s is missing" % key
    return data, None


def effective_authority(root, verifier_authority):
    tool_hashes = {}
    for relative in (
        "scripts/architecture/verify.py",
        "scripts/architecture/validate_policy.py",
        "scripts/architecture/watch_guardrail.py",
        ".githooks/pre-commit",
        ".github/workflows/architecture-guardrail.yml",
    ):
        path = contained_file(root, relative)
        if path is None:
            return None, "canonical tool is missing or symlinked: %s" % relative
        try:
            tool_hashes[relative] = file_sha256(path)
        except OSError as exc:
            return None, "cannot hash canonical tool %s: %s" % (relative, exc)
    return canonical_sha256({
        "verifier_authority_sha256": verifier_authority,
        "canonical_tools": tool_hashes,
    }), None


def approved_handoff(root, decision_id, approved_by, authority):
    path = contained_file(root, ".architecture/decisions.json")
    if path is None:
        return None, "committed handoff decisions are missing, unsafe, or symlinked"
    try:
        data = strict_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        return None, "cannot read committed handoff decisions: %s" % str(exc).splitlines()[0]
    working_entries = data.get("decisions") if isinstance(data, dict) else None
    if not isinstance(working_entries, list):
        return None, "decisions.json decisions must be a list"
    committed = run(["git", "show", "HEAD:.architecture/decisions.json"], root)
    if isinstance(committed, tuple) or committed.returncode != 0:
        return None, "handoff decisions must be tracked and committed in HEAD"
    try:
        committed_data = strict_json(committed.stdout.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        return None, "committed handoff decisions are invalid JSON: %s" % str(exc).splitlines()[0]
    committed_entries = committed_data.get("decisions") if isinstance(committed_data, dict) else None
    if not isinstance(committed_entries, list):
        return None, "committed decisions.json decisions must be a list"
    matches = [
        entry for entry in committed_entries
        if isinstance(entry, dict) and entry.get("id") == decision_id
    ]
    if len(matches) != 1:
        return None, "handoff decision must reference exactly one committed decision"
    decision = matches[0]
    working_matches = [
        entry for entry in working_entries
        if isinstance(entry, dict) and entry.get("id") == decision_id
    ]
    if working_matches != [decision]:
        return None, "working handoff decision must exactly match committed HEAD"
    expected = {
        "status": "approved",
        "subject_type": "watch-handoff",
        "subject_id": "guardrail-pack",
        "subject_sha256": authority,
        "approved_by": approved_by,
    }
    for key, value in expected.items():
        if decision.get(key) != value:
            return None, "handoff decision %s does not match %s" % (decision_id, key)
    approved_at = decision.get("approved_at")
    if not isinstance(approved_at, str) or not approved_at.strip():
        return None, "handoff decision approved_at is missing"
    return decision, None


def committed_authority_error(root):
    """Require every local file needed to reproduce authority to match HEAD."""
    module_path = contained_file(root, "scripts/architecture/validate_policy.py")
    if module_path is None:
        return "canonical policy validator is missing or unsafe"
    spec = importlib.util.spec_from_file_location("guardrail_watch_validate_policy", module_path)
    if spec is None or spec.loader is None:
        return "cannot load canonical policy validator"
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 - configuration failure must be reported
        return "cannot load canonical policy validator: %s" % str(exc).splitlines()[0]

    fixed = [
        ".architecture/policy.yaml",
        ".architecture/baseline.json",
        ".architecture/exceptions.yaml",
        ".architecture/decisions.json",
        ".architecture/verification.json",
        "scripts/architecture/verify.py",
        "scripts/architecture/validate_policy.py",
        "scripts/architecture/watch_guardrail.py",
        ".githooks/pre-commit",
        ".github/workflows/architecture-guardrail.yml",
    ]
    loaded = {}
    for relative in fixed[:5]:
        data, error = module.load_data(root / relative)
        if error:
            return error
        loaded[relative] = data

    files = set(fixed)

    def add_required(value, label):
        if not module.contained_existing_path(root, value):
            return "%s is missing, unsafe, or symlinked: %s" % (label, value)
        artifact = root / Path(*PurePosixPath(value.replace("\\", "/")).parts)
        if artifact.is_file():
            files.add(value.replace("\\", "/"))
            return None
        children = [child for child in artifact.rglob("*") if child.is_file()]
        if not children:
            return "%s must contain at least one committed file: %s" % (label, value)
        for child in children:
            if link_like(child):
                return "%s contains a symlink: %s" % (label, child.relative_to(root).as_posix())
            files.add(child.relative_to(root).as_posix())
        return None

    policy = loaded[".architecture/policy.yaml"]
    for rule in policy.get("rules", []):
        if not isinstance(rule, dict):
            continue
        for evidence in rule.get("evidence", []):
            if isinstance(evidence, dict) and evidence.get("type") in {"source", "test", "document"}:
                error = add_required(evidence.get("locator"), "policy evidence")
                if error:
                    return error
        if rule.get("state") != "enforced" or not isinstance(rule.get("validator"), dict):
            continue
        validator = rule["validator"]
        error = add_required(validator.get("implementation_root"), "validator implementation root")
        if error:
            return error
        fixtures = validator.get("fixtures", {})
        if isinstance(fixtures, dict):
            for kind in ("positive", "negative"):
                for value in fixtures.get(kind, []):
                    error = add_required(value, "%s fixture" % kind)
                    if error:
                        return error
    for entry in loaded[".architecture/baseline.json"].get("entries", []):
        if isinstance(entry, dict):
            error = add_required(entry.get("path"), "baseline target")
            if error:
                return error
    for entry in loaded[".architecture/exceptions.yaml"].get("exceptions", []):
        target = entry.get("target") if isinstance(entry, dict) else None
        if isinstance(target, dict):
            error = add_required(target.get("path"), "exception target")
            if error:
                return error

    for relative in sorted(files):
        tracked = run(["git", "ls-files", "--error-unmatch", "--", relative], root)
        if isinstance(tracked, tuple) or tracked.returncode != 0:
            return "authority file is not tracked in HEAD: %s" % relative
        exact_raw = relative in {
            ".githooks/pre-commit",
            ".github/workflows/architecture-guardrail.yml",
        }
        if not committed_file_matches(
            root, relative, normalize_platform_eol=not exact_raw
        ):
            return "authority file does not match committed HEAD: %s" % relative
    return None


def atomic_write_bytes(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(".%s.%d.tmp" % (path.name, os.getpid()))
    try:
        with temporary.open("xb") as handle:
            written_identity = os.fstat(handle.fileno())
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(temporary), str(path))
        return written_identity
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def atomic_write_json(path, value):
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return atomic_write_bytes(path, payload), payload


def cursor_matches(path, expected_identity, expected_bytes):
    try:
        return (
            os.path.samestat(path.stat(), expected_identity)
            and path.read_bytes() == expected_bytes
        )
    except OSError:
        return False


def emit_blocked(errors, authority=""):
    print(json.dumps({
        "schema": "guardrail-watch-v1",
        "complete": False,
        "status": "blocked",
        "authority_sha256": authority,
        "findings": [],
        "new_fingerprints": [],
        "persisting_fingerprints": [],
        "resolved_fingerprints": [],
        "errors": errors,
    }, sort_keys=True))
    return 2


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the guardrail-pack drift adapter.")
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--cursor",
        default=CURSOR_RELATIVE,
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--initialize", action="store_true")
    mode.add_argument("--accept-authority-change", action="store_true")
    parser.add_argument("--decision-id")
    parser.add_argument("--approved-by")
    args = parser.parse_args(argv)

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir() or not is_git_worktree_root(root):
        return emit_blocked(["root must be a git repository/worktree"])
    if args.cursor.replace("\\", "/") != CURSOR_RELATIVE:
        return emit_blocked(["cursor must be the dedicated operational state file: %s" % CURSOR_RELATIVE])
    cursor_path = root / Path(*PurePosixPath(CURSOR_RELATIVE).parts)
    cursor_parent = root
    for part in PurePosixPath(CURSOR_RELATIVE).parts:
        cursor_parent = cursor_parent / part
        if link_like(cursor_parent):
            return emit_blocked(["cursor path may not contain symlinks or junctions"])
    try:
        cursor_path.resolve().relative_to(root)
    except (OSError, ValueError):
        return emit_blocked(["cursor must resolve beneath the repository root"])
    cursor, cursor_error = load_cursor(cursor_path)
    if cursor_error:
        return emit_blocked([cursor_error])
    try:
        original_cursor_bytes = cursor_path.read_bytes()
        if strict_json(original_cursor_bytes.decode("utf-8")) != cursor:
            return emit_blocked(["cursor changed while it was being loaded"])
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return emit_blocked(["cursor cannot be captured for rollback: %s" % str(exc).splitlines()[0]])

    scan, scan_error = stable_scan(root)
    if scan_error:
        return emit_blocked([scan_error])
    authority, authority_error = effective_authority(root, scan["authority_sha256"])
    if authority_error:
        return emit_blocked([authority_error])
    initializing = args.initialize or args.accept_authority_change
    if initializing:
        if not args.decision_id or not args.approved_by:
            return emit_blocked(["authority handoff requires --decision-id and --approved-by"], authority)
        if any(
            not re.match(r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$", value)
            for value in (args.decision_id, args.approved_by)
        ):
            return emit_blocked(["handoff IDs must be canonical actor/decision IDs"], authority)
        if args.initialize and cursor.get("authority_sha256"):
            return emit_blocked(["cursor is already initialized"], authority)
        if args.accept_authority_change and not cursor.get("authority_sha256"):
            return emit_blocked(["cannot accept an authority change before initialization"], authority)
        if scan["findings"]:
            return emit_blocked(["authority handoff requires a clean complete scan"], authority)
    elif not cursor.get("authority_sha256"):
        return emit_blocked(["cursor authority is uninitialized; run an approved --initialize handoff"], authority)
    elif cursor.get("authority_sha256") != authority:
        return emit_blocked(["authority digest changed without an approved handoff"], authority)

    if initializing:
        handoff, handoff_error = approved_handoff(
            root, args.decision_id, args.approved_by, authority
        )
    else:
        handoff_data = cursor.get("handoff", {})
        handoff, handoff_error = approved_handoff(
            root, handoff_data.get("decision_id"), handoff_data.get("approved_by"), authority
        )
    if handoff_error:
        return emit_blocked([handoff_error], authority)
    authority_commit_error = committed_authority_error(root)
    if authority_commit_error:
        return emit_blocked([authority_commit_error], authority)

    previous = set(cursor.get("observed_fingerprints", []))
    current = {finding["fingerprint"] for finding in scan["findings"]}
    new = sorted(current - previous)
    persisting = sorted(current & previous)
    resolved = sorted(previous - current)
    classified = []
    for finding in scan["findings"]:
        item = dict(finding)
        item["state"] = "new" if finding["fingerprint"] in new else "persisting"
        classified.append(item)

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if initializing:
        cursor["handoff"] = {
            "decision_id": handoff["id"],
            "approved_by": handoff["approved_by"],
            "approved_at": handoff["approved_at"],
        }
    cursor.update({
        "version": 1,
        "mode": "guardrail-pack",
        "authority_sha256": authority,
        "last_complete_scan": now,
        "observed_fingerprints": sorted(current),
        "last_result_sha256": canonical_sha256({
            "authority_sha256": authority,
            "findings": scan["findings"],
            "completed_at": now,
        }),
    })
    try:
        cursor_identity, expected_cursor_bytes = atomic_write_json(cursor_path, cursor)
    except OSError as exc:
        return emit_blocked(["cursor update failed: %s" % str(exc).splitlines()[0]], authority)
    if not cursor_matches(cursor_path, cursor_identity, expected_cursor_bytes):
        return emit_blocked([
            "cursor custody changed after update; concurrent replacement was preserved"
        ], authority)
    post_scan, post_scan_error = stable_scan(root)
    post_authority = None
    post_authority_error = None
    post_commit_error = None
    if not post_scan_error:
        post_authority, post_authority_error = effective_authority(
            root, post_scan["authority_sha256"]
        )
        post_commit_error = committed_authority_error(root)
    if (
        post_scan_error
        or post_scan != scan
        or post_authority_error
        or post_authority != authority
        or post_commit_error
    ):
        if not cursor_matches(cursor_path, cursor_identity, expected_cursor_bytes):
            return emit_blocked([
                "cursor custody changed during final validation; concurrent replacement was preserved"
            ], authority)
        try:
            atomic_write_bytes(cursor_path, original_cursor_bytes)
        except OSError as exc:
            return emit_blocked([
                "cursor update changed verification and rollback failed: %s"
                % str(exc).splitlines()[0]
            ], authority)
        detail = (
            post_scan_error
            or post_authority_error
            or post_commit_error
            or (
                "effective authority changed after cursor update"
                if post_authority != authority
                else "verification result changed after cursor update"
            )
        )
        return emit_blocked([detail], authority)
    if not cursor_matches(cursor_path, cursor_identity, expected_cursor_bytes):
        return emit_blocked([
            "cursor custody changed before result emission; concurrent replacement was preserved"
        ], authority)

    status = "drift" if classified else "pass"
    print(json.dumps({
        "schema": "guardrail-watch-v1",
        "complete": True,
        "status": status,
        "authority_sha256": authority,
        "rules_run": scan["rules_run"],
        "findings": classified,
        "new_fingerprints": new,
        "persisting_fingerprints": persisting,
        "resolved_fingerprints": resolved,
        "errors": [],
    }, sort_keys=True))
    return 1 if classified else 0


if __name__ == "__main__":
    sys.exit(main())

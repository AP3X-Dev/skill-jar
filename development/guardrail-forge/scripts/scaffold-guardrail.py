#!/usr/bin/env python3
"""Preview or install the generic guardrail-forge project pack.

Conflict-safe and idempotent: the script preflights every destination and never
overwrites a differing file. Preview is the default; --apply performs writes.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath


SKILL_DIR = Path(__file__).resolve().parent.parent
ASSET_ROOT = SKILL_DIR / "assets" / "guardrail-pack"
VALIDATOR_SOURCE = SKILL_DIR / "scripts" / "validate-policy.py"
WATCHER_SOURCE = SKILL_DIR.parent / "arch-drift-watch" / "scripts" / "watch-guardrail-pack.py"
HOST_PREFIXES = {
    "claude": (".codex/",),
    "codex": (".claude/",),
    "generic": (".claude/", ".codex/"),
    "both": (),
}
RECOVERY_RELATIVE = Path(".guardrail-forge-recovery.json")
RECOVERY_COMPLETE_RELATIVE = Path(".guardrail-forge-recovery.complete.json")
RECOVERY_FAILURE_RELATIVE = Path(".guardrail-forge-recovery.failed.json")


def unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate recovery JSON key: %s" % key)
        result[key] = value
    return result


def link_like(path):
    return path.is_symlink() or (
        hasattr(path, "is_junction") and path.is_junction()
    )


def desired_files(repo, host):
    project = repo.name
    display_project = "".join(
        character if 32 <= ord(character) < 127 else "\\u%04x" % ord(character)
        for character in project
    )
    files = {}
    blocked_prefixes = HOST_PREFIXES[host]
    sources = (
        path for path in ASSET_ROOT.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    )
    for source in sorted(sources):
        relative = source.relative_to(ASSET_ROOT).as_posix()
        if relative.startswith(blocked_prefixes):
            continue
        text = source.read_text(encoding="utf-8")
        if relative == ".architecture/policy.yaml":
            text = text.replace('"__PROJECT__"', json.dumps(project, ensure_ascii=True))
        else:
            text = text.replace("__PROJECT__", display_project)
        files[Path(relative)] = text
    files[Path("scripts/architecture/validate_policy.py")] = VALIDATOR_SOURCE.read_text(encoding="utf-8")
    files[Path("scripts/architecture/watch_guardrail.py")] = WATCHER_SOURCE.read_text(encoding="utf-8")
    return files


def safe_destination(repo, destination):
    """Reject symlinked ancestors and any resolved target outside repo."""
    root = repo.resolve()
    try:
        relative = destination.relative_to(repo)
    except ValueError:
        return False
    cursor = repo
    for part in relative.parts:
        cursor = cursor / part
        if cursor.exists() and link_like(cursor):
            return False
    try:
        resolved = destination.resolve()
    except OSError:
        return False
    return resolved == root or root in resolved.parents


def secure_create_posix(repo, relative, content, executable, expected_root):
    """Create through held directory descriptors so ancestor names cannot be swapped."""
    directory_flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    descriptors = []
    try:
        current = os.open(str(repo), directory_flags)
        descriptors.append(current)
        if not os.path.samestat(os.fstat(current), expected_root):
            raise RuntimeError("scaffold repository root identity changed after preflight")
        for part in relative.parent.parts:
            try:
                child = os.open(part, directory_flags, dir_fd=current)
            except FileNotFoundError:
                os.mkdir(part, dir_fd=current)
                child = os.open(part, directory_flags, dir_fd=current)
            descriptors.append(child)
            current = child
        file_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            file_flags |= os.O_NOFOLLOW
        mode = 0o755 if executable else 0o644
        descriptor = None
        created_identity = None
        try:
            descriptor = os.open(relative.name, file_flags, mode, dir_fd=current)
            if executable:
                os.fchmod(descriptor, os.fstat(descriptor).st_mode | 0o111)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                descriptor = None
                created_identity = os.fstat(handle.fileno())
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.fsync(current)
        except Exception:
            if descriptor is not None:
                os.close(descriptor)
            raise
        return created_identity
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def secure_create_windows(repo, relative, content, executable, expected_root):
    """Hold every parent without delete sharing so junction swaps cannot race the write."""
    import ctypes
    from ctypes import wintypes

    create_file = ctypes.windll.kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    close_handle = ctypes.windll.kernel32.CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL
    invalid_handle = ctypes.c_void_p(-1).value
    file_read_attributes = 0x0080
    file_share_read = 0x00000001
    file_share_write = 0x00000002
    open_existing = 3
    open_reparse_point = 0x00200000
    backup_semantics = 0x02000000

    handles = []
    cursor = repo
    try:
        for part in (None,) + relative.parent.parts:
            if part is not None:
                cursor = cursor / part
                cursor.mkdir(exist_ok=True)
            handle = create_file(
                str(cursor), file_read_attributes,
                file_share_read | file_share_write, None, open_existing,
                open_reparse_point | backup_semantics, None,
            )
            if handle == invalid_handle:
                raise OSError(ctypes.get_last_error(), "cannot lock scaffold directory", str(cursor))
            handles.append(handle)
            if link_like(cursor):
                raise RuntimeError("scaffold directory became a symlink or junction: %s" % cursor)
            if part is None and not os.path.samestat(cursor.stat(), expected_root):
                raise RuntimeError("scaffold repository root identity changed after preflight")

        destination = repo / relative
        with destination.open("x", encoding="utf-8", newline="\n") as handle:
            created_identity = os.fstat(handle.fileno())
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if executable:
            try:
                destination.chmod(destination.stat().st_mode | 0o111)
            except OSError:
                pass
        return created_identity
    finally:
        for handle in reversed(handles):
            close_handle(handle)


def secure_create(repo, relative, content, executable=False, expected_root=None):
    if expected_root is None:
        expected_root = repo.stat()
    if os.name == "nt":
        return secure_create_windows(repo, relative, content, executable, expected_root)
    return secure_create_posix(repo, relative, content, executable, expected_root)


def classify(repo, files):
    results = []
    for relative, content in sorted(files.items(), key=lambda item: item[0].as_posix()):
        destination = repo / relative
        if not safe_destination(repo, destination):
            results.append(("conflict", relative, content))
            continue
        if not destination.exists():
            results.append(("create", relative, content))
            continue
        if not destination.is_file():
            results.append(("conflict", relative, content))
            continue
        try:
            existing = destination.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            results.append(("conflict", relative, content))
            continue
        results.append(("skip (identical)" if existing == content else "conflict", relative, content))
    return results


def is_git_worktree_root(repo):
    """Require Git itself to identify this exact directory as a worktree root."""
    environment = {
        key: value for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
    }
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False, env=environment,
        )
    except OSError:
        return False
    if result.returncode != 0:
        return False
    try:
        return Path(result.stdout.strip()).resolve() == repo.resolve()
    except OSError:
        return False


def root_identity_matches(repo, expected_root):
    try:
        current = repo.stat()
        return (
            os.path.samestat(current, expected_root)
            and current.st_ctime_ns == expected_root.st_ctime_ns
        )
    except OSError:
        return False


def valid_recovery_relative(value):
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    if PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute():
        return False
    path = PurePosixPath(value)
    if value != path.as_posix() or any(part in {"", ".", ".."} for part in path.parts):
        return False
    return value not in {
        RECOVERY_RELATIVE.as_posix(), RECOVERY_COMPLETE_RELATIVE.as_posix(),
        RECOVERY_FAILURE_RELATIVE.as_posix(),
    }


def recovery_intent_matches(repo, intent_text, expected_identity):
    path = repo / RECOVERY_RELATIVE
    try:
        return (
            safe_destination(repo, path)
            and path.is_file()
            and not link_like(path)
            and os.path.samestat(path.stat(), expected_identity)
            and path.read_text(encoding="utf-8") == intent_text
        )
    except (OSError, UnicodeError):
        return False


def ensure_recovery_intent(repo, intent_text, expected_identity, expected_root):
    """Revalidate exact marker custody; restore only when the marker is absent."""
    if recovery_intent_matches(repo, intent_text, expected_identity):
        return expected_identity
    path = repo / RECOVERY_RELATIVE
    if path.exists() or link_like(path):
        raise RuntimeError("recovery intent identity or bytes changed during apply")
    restored_identity = secure_create(
        repo, RECOVERY_RELATIVE, intent_text, False, expected_root
    )
    if not recovery_intent_matches(repo, intent_text, restored_identity):
        raise RuntimeError("recovery intent could not be restored during apply")
    return restored_identity


def record_recovery_custody_loss(repo, stage, error, expected_root):
    """Persist a separate fail-closed record without overwriting any state."""
    path = repo / RECOVERY_FAILURE_RELATIVE
    if path.exists() or link_like(path):
        return RECOVERY_FAILURE_RELATIVE.as_posix()
    payload = json.dumps({
        "version": 1,
        "status": "custody-lost-human-review-required",
        "stage": stage,
        "error": str(error).splitlines()[0],
    }, indent=2, sort_keys=True) + "\n"
    secure_create(repo, RECOVERY_FAILURE_RELATIVE, payload, False, expected_root)
    return RECOVERY_FAILURE_RELATIVE.as_posix()


def recovery_state(repo, files=None):
    """Return clear/complete, or fail closed on any incomplete recovery record."""
    failure_path = repo / RECOVERY_FAILURE_RELATIVE
    if failure_path.exists() or link_like(failure_path):
        raise RuntimeError(
            "unresolved scaffold recovery custody loss requires human review: %s"
            % RECOVERY_FAILURE_RELATIVE.as_posix()
        )
    paths = (RECOVERY_RELATIVE, RECOVERY_COMPLETE_RELATIVE)
    present = []
    texts = []
    for relative in paths:
        path = repo / relative
        exists = path.exists() or link_like(path)
        present.append(exists)
        if not exists:
            texts.append(None)
            continue
        if not safe_destination(repo, path) or not path.is_file():
            raise RuntimeError(
                "unresolved scaffold recovery marker requires human review: %s"
                % relative.as_posix()
            )
        try:
            texts.append(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError):
            raise RuntimeError(
                "unresolved scaffold recovery marker requires human review: %s"
                % relative.as_posix()
            )
    if not any(present):
        return "clear"
    if not all(present):
        raise RuntimeError(
            "unresolved scaffold recovery marker requires human review: %s"
            % RECOVERY_RELATIVE.as_posix()
        )
    try:
        intent = json.loads(texts[0], object_pairs_hook=unique_json_object)
        completion = json.loads(texts[1], object_pairs_hook=unique_json_object)
    except (TypeError, ValueError):
        raise RuntimeError("unresolved scaffold recovery marker requires human review")
    intent_digest = "sha256:" + hashlib.sha256(texts[0].encode("utf-8")).hexdigest()
    planned = intent.get("planned_create_paths")
    planned_hashes = intent.get("planned_create_sha256")
    if (
        intent.get("version") != 2
        or intent.get("status") != "apply-in-progress"
        or not isinstance(planned, list)
        or not planned
        or not all(isinstance(value, str) for value in planned)
        or len(planned) != len(set(planned))
        or not all(valid_recovery_relative(value) for value in planned)
        or len({Path(*PurePosixPath(value).parts) for value in planned})
        != len(planned)
        or not isinstance(planned_hashes, dict)
        or set(planned_hashes) != set(planned)
        or not all(
            isinstance(value, str)
            and value.startswith("sha256:")
            and len(value) == 71
            for value in planned_hashes.values()
        )
        or completion != {
            "intent_sha256": intent_digest,
            "status": "apply-complete",
            "version": 2,
        }
    ):
        raise RuntimeError("unresolved scaffold recovery marker requires human review")
    if files is not None:
        for value in planned:
            relative = Path(*PurePosixPath(value).parts)
            if (
                relative not in files
                or planned_hashes[value]
                != "sha256:" + hashlib.sha256(
                    files[relative].encode("utf-8")
                ).hexdigest()
            ):
                raise RuntimeError("unresolved scaffold recovery marker requires human review")
    return "complete"


@contextmanager
def hold_root(repo):
    """Hold the target root across Git validation, preflight, and apply."""
    if os.name != "nt":
        flags = os.O_RDONLY | os.O_DIRECTORY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(str(repo), flags)
        try:
            yield descriptor
        finally:
            os.close(descriptor)
        return

    import ctypes
    from ctypes import wintypes

    create_file = ctypes.windll.kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    close_handle = ctypes.windll.kernel32.CloseHandle
    invalid_handle = ctypes.c_void_p(-1).value
    handle = create_file(
        str(repo), 0x0080, 0x00000001 | 0x00000002, None, 3,
        0x00200000 | 0x02000000, None,
    )
    if handle == invalid_handle:
        raise OSError(ctypes.get_last_error(), "cannot hold scaffold root", str(repo))
    try:
        if link_like(repo):
            raise RuntimeError("scaffold root may not be a symlink or junction")
        yield handle
    finally:
        close_handle(handle)


def scaffold(repo, host="both", apply=False, expected_root=None):
    if expected_root is None:
        expected_root = repo.stat()
    if not root_identity_matches(repo, expected_root):
        raise RuntimeError("scaffold repository root identity changed before preflight")
    files = desired_files(repo, host)
    recovery = recovery_state(repo, files)
    results = classify(repo, files)
    if not root_identity_matches(repo, expected_root):
        raise RuntimeError("scaffold repository root identity changed during preflight")
    conflicts = [item for item in results if item[0] == "conflict"]
    if conflicts or not apply:
        return results
    pending = [item for item in results if item[0] == "create"]
    if not pending:
        return results
    if recovery == "complete":
        raise RuntimeError(
            "a completed scaffold recovery record must be archived by a human "
            "before applying newly introduced files"
        )
    intent = json.dumps({
        "version": 2,
        "status": "apply-in-progress",
        "planned_create_paths": [relative.as_posix() for _, relative, _ in pending],
        "planned_create_sha256": {
            relative.as_posix(): "sha256:" + hashlib.sha256(
                content.encode("utf-8")
            ).hexdigest()
            for _, relative, content in pending
        },
    }, indent=2, sort_keys=True) + "\n"
    try:
        intent_identity = secure_create(
            repo, RECOVERY_RELATIVE, intent, False, expected_root
        )
        intent_identity = ensure_recovery_intent(
            repo, intent, intent_identity, expected_root
        )
    except Exception as error:
        raise RuntimeError(
            "apply did not start because durable recovery intent could not be established: %s"
            % str(error).splitlines()[0]
        ) from error
    created = []
    for action, relative, content in results:
        if action != "create":
            continue
        destination = repo / relative
        try:
            if not safe_destination(repo, destination):
                raise RuntimeError(
                    "destination escaped target repository: %s" % relative
                )
            executable = (
                relative.as_posix() == ".githooks/pre-commit"
                or destination.suffix == ".py"
            )
            secure_create(repo, relative, content, executable, expected_root)
            intent_identity = ensure_recovery_intent(
                repo, intent, intent_identity, expected_root
            )
        except Exception as error:
            completed = ", ".join(path.as_posix() for path in created) or "none"
            try:
                intent_identity = ensure_recovery_intent(
                    repo, intent, intent_identity, expected_root
                )
                marker_status = "retained and reverified"
            except Exception as marker_error:
                try:
                    failure_record = record_recovery_custody_loss(
                        repo, "destination-failure", marker_error, expected_root
                    )
                except Exception as record_error:
                    failure_record = "FAILED TO RECORD (%s)" % str(record_error).splitlines()[0]
                marker_status = "CUSTODY LOST (%s); failure record %s" % (
                    str(marker_error).splitlines()[0], failure_record,
                )
            raise RuntimeError(
                "apply stopped (%s); previously completed paths require review "
                "and were not reverified: %s; current destination may be partial: %s; "
                "recovery marker %s: %s"
                % (
                    str(error).splitlines()[0], completed,
                    relative.as_posix(), marker_status,
                    RECOVERY_RELATIVE.as_posix(),
                )
            ) from error
        created.append(relative)
    completion = json.dumps({
        "version": 2,
        "status": "apply-complete",
        "intent_sha256": "sha256:" + hashlib.sha256(intent.encode("utf-8")).hexdigest(),
    }, indent=2, sort_keys=True) + "\n"
    try:
        intent_identity = ensure_recovery_intent(
            repo, intent, intent_identity, expected_root
        )
        secure_create(
            repo, RECOVERY_COMPLETE_RELATIVE, completion, False, expected_root
        )
        ensure_recovery_intent(repo, intent, intent_identity, expected_root)
    except Exception as error:
        try:
            ensure_recovery_intent(repo, intent, intent_identity, expected_root)
            marker_status = "retained and reverified"
        except Exception as marker_error:
            try:
                failure_record = record_recovery_custody_loss(
                    repo, "completion-failure", marker_error, expected_root
                )
            except Exception as record_error:
                failure_record = "FAILED TO RECORD (%s)" % str(record_error).splitlines()[0]
            marker_status = "CUSTODY LOST (%s); failure record %s" % (
                str(marker_error).splitlines()[0], failure_record,
            )
        raise RuntimeError(
            "apply destinations were written but completion was not durably recorded; "
            "recovery marker %s and requires human review: %s"
            % (marker_status, str(error).splitlines()[0])
        ) from error
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Preview or install the generic guardrail-forge project pack (never overwrites)."
    )
    parser.add_argument("--repo", default=".", help="existing target repository/worktree")
    parser.add_argument("--host", choices=sorted(HOST_PREFIXES), default="both")
    parser.add_argument("--apply", action="store_true", help="write after a conflict-free preflight")
    args = parser.parse_args(argv)

    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        print("scaffold error: target is not a directory: %s" % repo)
        return 2
    try:
        with hold_root(repo):
            expected_root = repo.stat()
            if (
                not is_git_worktree_root(repo)
                or not root_identity_matches(repo, expected_root)
            ):
                print("scaffold error: target is not a git repository/worktree: %s" % repo)
                return 2
            if (
                not ASSET_ROOT.is_dir()
                or not VALIDATOR_SOURCE.is_file()
                or not WATCHER_SOURCE.is_file()
            ):
                print("scaffold error: bundled pack assets are missing")
                return 2
            results = scaffold(repo, args.host, args.apply, expected_root)
    except Exception as error:
        print("scaffold error: %s" % str(error).splitlines()[0])
        return 2
    for action, relative, _content in results:
        print("%-18s %s" % (action, relative.as_posix()))
    conflicts = [item for item in results if item[0] == "conflict"]
    creates = [item for item in results if item[0] == "create"]
    if conflicts:
        print("Refused: %d conflict(s); no files written." % len(conflicts))
        return 2
    if args.apply:
        print("Applied: %d created, %d already identical." % (
            len(creates), len(results) - len(creates)
        ))
    else:
        print("Preview only: %d file(s) would be created. Re-run with --apply after review." % len(creates))
    return 0


if __name__ == "__main__":
    sys.exit(main())

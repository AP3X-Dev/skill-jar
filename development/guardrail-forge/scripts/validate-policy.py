#!/usr/bin/env python3
"""Validate a guardrail-forge policy pack without executing project rules.

Stdlib-only for JSON and JSON-compatible YAML. Conventional YAML is accepted
when PyYAML is already installed. Exit 0 means structurally valid; exit 2 means
configuration/schema/provenance is invalid.
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath, PureWindowsPath


RULE_ID_RE = re.compile(r"^[A-Z][A-Z0-9]*-[0-9]{3}$")
EXCEPTION_ID_RE = re.compile(r"^EXC-[0-9]{3}$")
FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
GLOB_CHARS = set("*?[]{}")
STATES = {"observed", "documented", "verified", "approved", "enforced"}
SEVERITIES = {"info", "warning", "error"}
EVIDENCE_TYPES = {"source", "test", "runtime", "document", "history", "memory", "human"}
CURRENT_EVIDENCE = {"source", "test", "runtime"}
BASELINE_WRITE_TOKENS = {"--write-baseline", "--update-baseline", "write-baseline", "update-baseline"}
BASELINE_MUTATION_VERBS = {"write", "update", "refresh", "regenerate", "reset", "record", "accept"}
DYNAMIC_EXECUTION_TOKENS = {"-c", "-m", "-e", "--eval", "--command", "-command", "/command"}
ALLOWED_RUNTIME_NAMES = {
    "python", "python3", "python.exe", "python3.exe", "node", "node.exe",
    "deno", "deno.exe", "bun", "bun.exe", "ruby", "ruby.exe", "php",
    "php.exe", "java", "java.exe", "dotnet", "dotnet.exe", "bash", "sh",
    "pwsh", "pwsh.exe", "powershell", "powershell.exe",
}
PLACEHOLDER_NAMES = {
    "root", "rule_id", "policy", "baseline", "exceptions", "decisions",
    "verification", "fixture",
}
PLACEHOLDER_TOKEN_RE = re.compile(
    r"^(?:--[A-Za-z0-9][A-Za-z0-9_-]*=)?\{(" + "|".join(sorted(PLACEHOLDER_NAMES)) + r")\}$"
)
ACTOR_ID_RE = re.compile(r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")
COMMAND_LITERAL_RE = re.compile(r"^[A-Za-z0-9_+-]+$")
LONG_OPTION_NAME_RE = re.compile(r"^--[A-Za-z0-9][A-Za-z0-9_-]*$")
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *("COM%d" % value for value in range(1, 10)),
    *("LPT%d" % value for value in range(1, 10)),
}


class DuplicateKeyError(ValueError):
    """Raised when JSON/YAML contains an ambiguous duplicate mapping key."""


def unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError("duplicate mapping key: %s" % key)
        result[key] = value
    return result


def load_data(path):
    """Load a mapping from JSON or YAML; return (value, error)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, "%s: cannot read: %s" % (path, exc)
    try:
        data = json.loads(text, object_pairs_hook=unique_json_object)
    except ValueError as json_error:
        try:
            import yaml  # type: ignore
        except ImportError:
            return None, (
                "%s: not JSON-compatible YAML and PyYAML is unavailable (%s)"
                % (path, str(json_error).splitlines()[0])
            )
        try:
            class UniqueKeyLoader(yaml.SafeLoader):
                pass

            def construct_unique_mapping(loader, node, deep=False):
                mapping = {}
                for key_node, value_node in node.value:
                    key = loader.construct_object(key_node, deep=deep)
                    if key in mapping:
                        raise DuplicateKeyError("duplicate mapping key: %s" % key)
                    mapping[key] = loader.construct_object(value_node, deep=deep)
                return mapping

            UniqueKeyLoader.add_constructor(
                yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                construct_unique_mapping,
            )
            data = yaml.load(text, Loader=UniqueKeyLoader)
        except Exception as exc:  # noqa: BLE001 - report parser failure
            return None, "%s: YAML parse error: %s" % (path, str(exc).splitlines()[0])
    if not isinstance(data, dict):
        return None, "%s: top level must be a mapping" % path
    return data, None


def nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def string_list(value):
    return isinstance(value, list) and all(nonempty_string(item) for item in value)


def valid_timestamp(value):
    if not nonempty_string(value):
        return False
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        datetime.fromisoformat(candidate)
        return True
    except ValueError:
        return False


def exact_relative_path(value):
    if (
        not nonempty_string(value)
        or value != value.strip()
        or any(char in value for char in GLOB_CHARS)
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
        or ":" in value
    ):
        return False
    normalized = value.replace("\\", "/")
    posix_path = PurePosixPath(normalized)
    windows_path = PureWindowsPath(value)
    if posix_path.is_absolute() or windows_path.is_absolute() or windows_path.drive or windows_path.root:
        return False
    if ".." in posix_path.parts or "." in posix_path.parts or normalized in {".", ""}:
        return False
    for part in posix_path.parts:
        if not part or part.endswith((".", " ")):
            return False
        if part.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES:
            return False
    return True


def safe_scope_pattern(value):
    if (
        not nonempty_string(value)
        or value != value.strip()
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
        or ":" in value
    ):
        return False
    normalized = value.replace("\\", "/")
    posix_path = PurePosixPath(normalized)
    windows_path = PureWindowsPath(value)
    if posix_path.is_absolute() or windows_path.is_absolute() or windows_path.drive or windows_path.root:
        return False
    if ".." in posix_path.parts or "." in posix_path.parts or normalized in {".", ""}:
        return False
    for part in posix_path.parts:
        if not part or part.endswith((".", " ")):
            return False
        if not any(character in part for character in GLOB_CHARS):
            if part.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES:
                return False
    return True


def exact_symbol(value):
    return (
        nonempty_string(value)
        and value == value.strip()
        and not any(char in value for char in GLOB_CHARS)
        and not any(ord(char) < 32 or ord(char) == 127 for char in value)
    )


def canonical_actor_id(value):
    return nonempty_string(value) and bool(ACTOR_ID_RE.match(value))


def command_requests_baseline_mutation(command):
    for token in command:
        lowered = token.lower()
        if lowered == "-w" or any(forbidden in lowered for forbidden in BASELINE_WRITE_TOKENS):
            return True
        normalized = re.sub(r"[^a-z0-9]", "", lowered)
        if "baseline" in normalized and any(verb in normalized for verb in BASELINE_MUTATION_VERBS):
            return True
    return False


def safe_placeholder_token(token):
    if "{" not in token and "}" not in token:
        return True
    return bool(PLACEHOLDER_TOKEN_RE.match(token))


def command_repo_path(root, token, require_file=False):
    """Return a canonical repo-relative path token, including ./ and absolute forms."""
    if not nonempty_string(token) or "{" in token or "}" in token:
        return None
    candidate = Path(token)
    if not candidate.is_absolute():
        if not exact_relative_path(token):
            return None
        candidate = root / candidate
    try:
        lexical = candidate.absolute().relative_to(root.absolute()).as_posix()
        if not contained_existing_path(root, lexical, require_file=require_file):
            return None
        resolved = candidate.resolve(strict=True)
        relative = resolved.relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return None
    return relative


def command_path_values(token):
    """Parse one long-option delimiter, then response markers, and stop."""
    value = token
    path_required = False
    if value.startswith("--"):
        delimiters = [index for index in (value.find("="), value.find(":")) if index >= 0]
        if delimiters:
            delimiter = min(delimiters)
            if not LONG_OPTION_NAME_RE.fullmatch(value[:delimiter]):
                return [(token, True)]
            value = value[delimiter + 1:]
            if not value:
                path_required = True
    while value.startswith("@") and len(value) > 1:
        value = value[1:]
        path_required = True
    return [(value, path_required)]


def ambiguous_path_argument(root, value, path_required=False):
    """Allow only exact bound paths, placeholders, or punctuation-free literals."""
    if path_required and not nonempty_string(value):
        return True
    if not nonempty_string(value) or "{" in value or "}" in value:
        return False
    if command_repo_path(root, value):
        return False
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    if candidate.exists() or link_like(candidate):
        return True
    return path_required or not bool(COMMAND_LITERAL_RE.fullmatch(value))


def link_like(path):
    """Treat POSIX symlinks and Windows directory junctions as links."""
    return path.is_symlink() or (
        hasattr(path, "is_junction") and path.is_junction()
    )


def contained_existing_path(root, value, require_file=False):
    """Return True only for a non-symlink path contained beneath root."""
    if not exact_relative_path(value):
        return False
    root = root.resolve()
    relative = PurePosixPath(value.replace("\\", "/"))
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if link_like(cursor):
            return False
    try:
        resolved = (root / Path(*relative.parts)).resolve(strict=True)
    except OSError:
        return False
    if root not in resolved.parents:
        return False
    return resolved.is_file() if require_file else resolved.exists()


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def windows_named_streams(path):
    """Enumerate NTFS named streams; fail closed on unexpected API errors."""
    if sys.platform != "win32":
        return [], None
    import ctypes
    from ctypes import wintypes

    class WIN32_FIND_STREAM_DATA(ctypes.Structure):
        _fields_ = [
            ("StreamSize", ctypes.c_longlong),
            ("cStreamName", wintypes.WCHAR * (260 + 36)),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    find_first = kernel32.FindFirstStreamW
    find_first.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD,
        ctypes.POINTER(WIN32_FIND_STREAM_DATA), wintypes.DWORD,
    ]
    find_first.restype = wintypes.HANDLE
    find_next = kernel32.FindNextStreamW
    find_next.argtypes = [wintypes.HANDLE, ctypes.POINTER(WIN32_FIND_STREAM_DATA)]
    find_next.restype = wintypes.BOOL
    find_close = kernel32.FindClose
    find_close.argtypes = [wintypes.HANDLE]
    find_close.restype = wintypes.BOOL
    invalid_handle = ctypes.c_void_p(-1).value
    no_more_files = 18
    handle_eof = 38
    data = WIN32_FIND_STREAM_DATA()
    handle = find_first(str(path), 0, ctypes.byref(data), 0)
    if handle == invalid_handle:
        error = ctypes.get_last_error()
        if error in {no_more_files, handle_eof}:
            return [], None
        return [], "cannot enumerate NTFS streams for %s (winerror %d)" % (path, error)
    streams = []
    try:
        while True:
            name = data.cStreamName
            if name and name != "::$DATA":
                streams.append(name)
            if not find_next(handle, ctypes.byref(data)):
                error = ctypes.get_last_error()
                if error not in {no_more_files, handle_eof}:
                    return [], "cannot enumerate NTFS streams for %s (winerror %d)" % (
                        path, error,
                    )
                break
    finally:
        find_close(handle)
    return sorted(streams), None


def add_named_stream_hashes(group, relative, path, manifest, errors):
    streams, error = windows_named_streams(path)
    if error:
        errors.append(error)
        return
    for stream in streams:
        try:
            manifest["%s:%s%s" % (group, relative, stream)] = file_sha256(
                Path(str(path) + stream)
            )
        except OSError as exc:
            errors.append("cannot hash NTFS stream %s%s: %s" % (relative, stream, exc))


def validator_artifact_sha256(root, validator):
    """Hash the complete implementation root plus all fixture bytes and paths."""
    manifest = {}
    errors = []
    implementation_root = validator.get("implementation_root")
    groups = [("implementation", [implementation_root] if nonempty_string(implementation_root) else [])]
    fixtures = validator.get("fixtures", {}) if isinstance(validator.get("fixtures"), dict) else {}
    groups.extend(("fixture-%s" % kind, fixtures.get(kind, [])) for kind in ("positive", "negative"))
    root = root.resolve()
    for group, paths in groups:
        if not isinstance(paths, list):
            continue
        for value in paths:
            if not contained_existing_path(root, value):
                errors.append("%s artifact is missing, unsafe, or symlinked: %s" % (group, value))
                continue
            relative = PurePosixPath(value.replace("\\", "/"))
            artifact = root / Path(*relative.parts)
            key = "%s:%s" % (group, relative.as_posix())
            add_named_stream_hashes(
                group, relative.as_posix(), artifact, manifest, errors
            )
            if artifact.is_file():
                manifest[key] = file_sha256(artifact)
                continue
            manifest[key + "/"] = "directory"
            for child in sorted(artifact.rglob("*")):
                if link_like(child):
                    errors.append("%s artifact contains a symlink: %s" % (
                        group, child.relative_to(root).as_posix()
                    ))
                    continue
                child_relative = child.relative_to(root).as_posix()
                add_named_stream_hashes(
                    group, child_relative, child, manifest, errors
                )
                if child.is_dir():
                    manifest["%s:%s/" % (group, child_relative)] = "directory"
                elif child.is_file():
                    manifest["%s:%s" % (group, child_relative)] = file_sha256(child)
    return canonical_sha256(manifest), errors


def canonical_sha256(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def rule_contract(rule):
    return {
        "id": rule.get("id"),
        "statement": rule.get("statement"),
        "scope": rule.get("scope"),
    }


def baseline_contract(entry):
    return {
        "fingerprint": entry.get("fingerprint"),
        "rule_id": entry.get("rule_id"),
        "path": entry.get("path"),
        "reason": entry.get("reason"),
    }


def exception_contract(entry):
    return {
        "id": entry.get("id"),
        "rule_id": entry.get("rule_id"),
        "target": entry.get("target"),
        "reason": entry.get("reason"),
        "owner": entry.get("owner"),
        "expires_at": entry.get("expires_at"),
        "removal_condition": entry.get("removal_condition"),
    }


def require_mapping(value, label, errors):
    if not isinstance(value, dict):
        errors.append("%s must be a mapping" % label)
        return {}
    return value


def validate_approval(approval, label, errors):
    approval = require_mapping(approval, label, errors)
    if not nonempty_string(approval.get("decision_id")):
        errors.append("%s.decision_id must be a non-empty string" % label)
    if not canonical_actor_id(approval.get("approved_by")):
        errors.append("%s.approved_by must be a canonical actor ID" % label)
    if not valid_timestamp(approval.get("approved_at")):
        errors.append("%s.approved_at must be an ISO-8601 timestamp" % label)


def validate_evidence(rule, label, root, errors):
    evidence = rule.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("%s.evidence must contain at least one evidence item" % label)
        return set()
    types = set()
    for index, item in enumerate(evidence):
        item_label = "%s.evidence[%d]" % (label, index)
        item = require_mapping(item, item_label, errors)
        evidence_type = item.get("type")
        if evidence_type not in EVIDENCE_TYPES:
            errors.append("%s.type must be one of %s" % (item_label, sorted(EVIDENCE_TYPES)))
        else:
            types.add(evidence_type)
        locator = item.get("locator")
        if not nonempty_string(locator):
            errors.append("%s.locator must be a non-empty string" % item_label)
        if not nonempty_string(item.get("note")):
            errors.append("%s.note must be a non-empty string" % item_label)
        if evidence_type in {"source", "test", "document"}:
            if not exact_relative_path(locator):
                errors.append("%s.locator must be an exact safe repo-relative path" % item_label)
            elif not contained_existing_path(root, locator, require_file=True):
                errors.append("%s.locator is missing, symlinked, or outside root: %s" % (item_label, locator))
    return types


def validate_rule(rule, index, root, errors):
    label = "policy.rules[%d]" % index
    rule = require_mapping(rule, label, errors)
    rule_id = rule.get("id")
    if not nonempty_string(rule_id) or not RULE_ID_RE.match(rule_id):
        errors.append("%s.id must match %s" % (label, RULE_ID_RE.pattern))
    if not nonempty_string(rule.get("statement")):
        errors.append("%s.statement must be a non-empty string" % label)
    state = rule.get("state")
    if state not in STATES:
        errors.append("%s.state must be one of %s" % (label, sorted(STATES)))
    severity = rule.get("severity")
    if severity not in SEVERITIES:
        errors.append("%s.severity must be one of %s" % (label, sorted(SEVERITIES)))

    scope = require_mapping(rule.get("scope"), "%s.scope" % label, errors)
    if not string_list(scope.get("include")) or not scope.get("include"):
        errors.append("%s.scope.include must contain at least one pattern" % label)
    elif not all(safe_scope_pattern(pattern) for pattern in scope.get("include")):
        errors.append("%s.scope.include contains an unsafe or absolute pattern" % label)
    if not string_list(scope.get("exclude", [])):
        errors.append("%s.scope.exclude must be a list of strings" % label)
    elif not all(safe_scope_pattern(pattern) for pattern in scope.get("exclude", [])):
        errors.append("%s.scope.exclude contains an unsafe or absolute pattern" % label)

    evidence_types = validate_evidence(rule, label, root, errors)
    if state in {"verified", "approved", "enforced"} and not evidence_types.intersection(CURRENT_EVIDENCE):
        errors.append("%s at state %s needs source, test, or runtime evidence" % (label, state))

    provenance = require_mapping(rule.get("provenance"), "%s.provenance" % label, errors)
    if not valid_timestamp(provenance.get("discovered_at")):
        errors.append("%s.provenance.discovered_at must be an ISO-8601 timestamp" % label)
    if not nonempty_string(provenance.get("source_commit")):
        errors.append("%s.provenance.source_commit must be non-empty" % label)
    if not string_list(provenance.get("sources")) or not provenance.get("sources"):
        errors.append("%s.provenance.sources must contain at least one source" % label)

    approval = rule.get("approval")
    if state in {"approved", "enforced"}:
        validate_approval(approval, "%s.approval" % label, errors)
    elif approval is not None:
        errors.append("%s has approval data but state is only %s" % (label, state))

    validator = rule.get("validator")
    if state == "enforced":
        if severity != "error":
            errors.append("%s enforced rules must have severity error" % label)
        validator = require_mapping(validator, "%s.validator" % label, errors)
        command = validator.get("command")
        if not string_list(command) or not command:
            errors.append("%s.validator.command must be a non-empty argv list" % label)
        elif not all(safe_placeholder_token(token) for token in command):
            errors.append(
                "%s.validator.command placeholders must be standalone values or exact --option={placeholder} values"
                % label
            )
        elif command_requests_baseline_mutation(command):
            errors.append("%s.validator.command may not mutate the baseline" % label)
        elif any(token.casefold() in DYNAMIC_EXECUTION_TOKENS for token in command):
            errors.append("%s.validator.command may not use inline/module dynamic execution" % label)
        elif not any("{fixture}" in token for token in command):
            errors.append("%s.validator.command must scan the {fixture} placeholder" % label)
        output_format = validator.get("output_format")
        if output_format != "guardrail-findings-v1":
            errors.append("%s.validator.output_format must be guardrail-findings-v1" % label)
        implementation_root = validator.get("implementation_root")
        if not exact_relative_path(implementation_root) or not contained_existing_path(root, implementation_root):
            errors.append("%s.validator.implementation_root must be one exact contained directory" % label)
        else:
            implementation_path = root / Path(*PurePosixPath(implementation_root.replace("\\", "/")).parts)
            if not implementation_path.is_dir():
                errors.append("%s.validator.implementation_root must be a directory" % label)
        entrypoint = validator.get("entrypoint")
        if not exact_relative_path(entrypoint) or not contained_existing_path(root, entrypoint, require_file=True):
            errors.append("%s.validator.entrypoint must be an exact contained file" % label)
        else:
            normalized_entrypoint = entrypoint.replace("\\", "/")
            command_values = []
            ambiguous_path_values = []
            if isinstance(command, list):
                for token in command[1:]:
                    token_values = command_path_values(token)
                    if token == "-I":
                        token_values = [("", True)]
                    elif (
                        len(token) > 2
                        and token.startswith("-")
                        and not token.startswith("--")
                        and token[1].isalnum()
                        and "=" not in token
                        and ":" not in token
                    ):
                        attached = token[2:]
                        token_values = [(attached, token[1] == "I")]
                    command_values.extend(value for value, _required in token_values)
                    if any(
                        ambiguous_path_argument(root, value, required)
                        for value, required in token_values
                    ):
                        ambiguous_path_values.append(token)
            command_paths = [command_repo_path(root, token) for token in command_values]
            command_paths = [path for path in command_paths if path]
            unsafe_path_values = []
            for value in command_values:
                if not nonempty_string(value) or "{" in value or "}" in value:
                    continue
                candidate = Path(value)
                if not candidate.is_absolute():
                    candidate = root / candidate
                if candidate.exists() or link_like(candidate):
                    try:
                        candidate.resolve(strict=True).relative_to(root.resolve())
                    except (OSError, ValueError):
                        unsafe_path_values.append(value)
            normalized_root = implementation_root.replace("\\", "/") if isinstance(implementation_root, str) else ""
            if not (
                normalized_root
                and normalized_entrypoint.startswith(normalized_root.rstrip("/") + "/")
            ):
                errors.append("%s.validator.entrypoint must be beneath implementation_root" % label)
            runtime_name = Path(command[0]).name.casefold() if isinstance(command, list) and command else ""
            if runtime_name not in ALLOWED_RUNTIME_NAMES:
                errors.append("%s.validator.command[0] must be an approved external runtime" % label)
            elif isinstance(command, list):
                runtime_token = command[0]
                posix_runtime = PurePosixPath(runtime_token.replace("\\", "/"))
                windows_runtime = PureWindowsPath(runtime_token)
                runtime_is_absolute = posix_runtime.is_absolute() or windows_runtime.is_absolute()
                if len(posix_runtime.parts) > 1 and not runtime_is_absolute:
                    errors.append("%s.validator.command[0] may not be a repo-relative runtime" % label)
                shadow_names = {runtime_name}
                if "." not in runtime_name:
                    shadow_names.update(runtime_name + suffix for suffix in (".exe", ".com", ".cmd", ".bat"))
                if any(child.name.casefold() in shadow_names for child in root.iterdir()):
                    errors.append("%s.validator.command[0] is shadowed by a repository-local executable" % label)
                runtime_path = shutil.which(runtime_token)
                if runtime_path is None:
                    errors.append("%s.validator.command[0] must resolve to an available runtime" % label)
                else:
                    # Keep this lexical: Windows Store app-execution aliases are usable
                    # files but strict realpath resolution can fail with WinError 1920.
                    runtime_absolute = Path(runtime_path).absolute()
                    root_absolute = root.absolute()
                    if root_absolute == runtime_absolute or root_absolute in runtime_absolute.parents:
                        errors.append("%s.validator.command[0] must resolve outside the repository" % label)
            if (
                not isinstance(command, list)
                or len(command) < 2
                or command_repo_path(root, command[1], require_file=True) != normalized_entrypoint
            ):
                errors.append("%s.validator.command must be runtime + exact entrypoint + arguments" % label)
            undeclared = [
                path for path in command_paths
                if path != normalized_root
                and not path.startswith(normalized_root.rstrip("/") + "/")
            ]
            if undeclared:
                errors.append("%s.validator.command references repo paths outside implementation_root: %s" % (
                    label, ", ".join(sorted(set(undeclared)))
                ))
            if unsafe_path_values:
                errors.append("%s.validator.command references external or symlinked path arguments: %s" % (
                    label, ", ".join(sorted(set(unsafe_path_values)))
                ))
            if ambiguous_path_values:
                errors.append(
                    "%s.validator.command contains missing, ambiguous, or unsupported path-like arguments: %s"
                    % (label, ", ".join(sorted(set(ambiguous_path_values))))
                )
        fixtures = require_mapping(validator.get("fixtures"), "%s.validator.fixtures" % label, errors)
        for fixture_kind in ("positive", "negative"):
            paths = fixtures.get(fixture_kind)
            if not string_list(paths) or not paths:
                errors.append("%s.validator.fixtures.%s must contain at least one path" % (label, fixture_kind))
                continue
            for path in paths:
                if not contained_existing_path(root, path):
                    errors.append("%s fixture path is missing, unsafe, or symlinked: %s" % (label, path))
        if not nonempty_string(rule.get("remediation")):
            errors.append("%s.remediation is required for enforced rules" % label)

    exception_ids = rule.get("exception_ids", [])
    if not string_list(exception_ids):
        errors.append("%s.exception_ids must be a list of IDs" % label)
    routing = require_mapping(rule.get("routing"), "%s.routing" % label, errors)
    for key in ("kind", "owner"):
        if not nonempty_string(routing.get(key)) or routing.get(key) != routing.get(key, "").strip():
            errors.append("%s.routing.%s must be a canonical non-empty string" % (label, key))
    return rule_id


def validate_baseline(data, rule_ids, root, errors):
    if data.get("version") != 1:
        errors.append("baseline.version must be 1")
    entries = data.get("entries")
    if not isinstance(entries, list):
        errors.append("baseline.entries must be a list")
        return
    if entries and not nonempty_string(data.get("source_commit")):
        errors.append("baseline.source_commit is required when entries exist")
    seen = set()
    for index, entry in enumerate(entries):
        label = "baseline.entries[%d]" % index
        entry = require_mapping(entry, label, errors)
        fingerprint = entry.get("fingerprint")
        if not nonempty_string(fingerprint) or not FINGERPRINT_RE.match(fingerprint):
            errors.append("%s.fingerprint must be sha256:<64 lowercase hex>" % label)
        elif fingerprint in seen:
            errors.append("%s.fingerprint is duplicated" % label)
        else:
            seen.add(fingerprint)
        if entry.get("rule_id") not in rule_ids:
            errors.append("%s.rule_id does not reference a policy rule" % label)
        if not exact_relative_path(entry.get("path")):
            errors.append("%s.path must be an exact safe relative path without globs" % label)
        elif not contained_existing_path(root, entry.get("path"), require_file=True):
            errors.append("%s.path is missing, symlinked, or outside root" % label)
        for key in ("reason", "decision_id"):
            if not nonempty_string(entry.get(key)):
                errors.append("%s.%s must be non-empty" % (label, key))
        if not canonical_actor_id(entry.get("approved_by")):
            errors.append("%s.approved_by must be a canonical actor ID" % label)
        if not valid_timestamp(entry.get("approved_at")):
            errors.append("%s.approved_at must be an ISO-8601 timestamp" % label)
    return entries


def validate_exceptions(data, rules_by_id, root, errors):
    if data.get("version") != 1:
        errors.append("exceptions.version must be 1")
    entries = data.get("exceptions")
    if not isinstance(entries, list):
        errors.append("exceptions.exceptions must be a list")
        return [], set()
    seen = set()
    for index, entry in enumerate(entries):
        label = "exceptions.exceptions[%d]" % index
        entry = require_mapping(entry, label, errors)
        exception_id = entry.get("id")
        if not nonempty_string(exception_id) or not EXCEPTION_ID_RE.match(exception_id):
            errors.append("%s.id must match %s" % (label, EXCEPTION_ID_RE.pattern))
        elif exception_id in seen:
            errors.append("%s.id is duplicated" % label)
        else:
            seen.add(exception_id)
        rule_id = entry.get("rule_id")
        if rule_id not in rules_by_id:
            errors.append("%s.rule_id does not reference a policy rule" % label)
        elif rules_by_id[rule_id].get("state") not in {"approved", "enforced"}:
            errors.append("%s references a rule that is not approved" % label)
        target = require_mapping(entry.get("target"), "%s.target" % label, errors)
        if not exact_relative_path(target.get("path")):
            errors.append("%s.target.path must be exact and contain no globs" % label)
        elif not contained_existing_path(root, target.get("path"), require_file=True):
            errors.append("%s.target.path is missing, symlinked, or outside root" % label)
        if not exact_symbol(target.get("symbol")):
            errors.append("%s.target.symbol must be one required exact symbol without globs/control characters" % label)
        if not nonempty_string(target.get("fingerprint")) or not FINGERPRINT_RE.match(target.get("fingerprint", "")):
            errors.append("%s.target.fingerprint must be one exact sha256 fingerprint" % label)
        for key in ("reason", "owner", "decision_id"):
            if not nonempty_string(entry.get(key)):
                errors.append("%s.%s must be non-empty" % (label, key))
        if not canonical_actor_id(entry.get("approved_by")):
            errors.append("%s.approved_by must be a canonical actor ID" % label)
        if not valid_timestamp(entry.get("approved_at")):
            errors.append("%s.approved_at must be an ISO-8601 timestamp" % label)
        expires = entry.get("expires_at")
        removal = entry.get("removal_condition")
        if not valid_timestamp(expires) and not nonempty_string(removal):
            errors.append("%s needs expires_at or removal_condition" % label)
    return entries, seen


def validate_decisions(data, errors):
    if data.get("version") != 1:
        errors.append("decisions.version must be 1")
    entries = data.get("decisions")
    if not isinstance(entries, list):
        errors.append("decisions.decisions must be a list")
        return {}
    decisions = {}
    for index, entry in enumerate(entries):
        label = "decisions.decisions[%d]" % index
        entry = require_mapping(entry, label, errors)
        decision_id = entry.get("id")
        if not nonempty_string(decision_id):
            errors.append("%s.id must be non-empty" % label)
            continue
        if decision_id in decisions:
            errors.append("%s.id is duplicated" % label)
        decisions[decision_id] = entry
        if entry.get("status") != "approved":
            errors.append("%s.status must be approved" % label)
        if entry.get("subject_type") not in {"rule", "baseline", "exception", "watch-handoff"}:
            errors.append("%s.subject_type must be rule, baseline, exception, or watch-handoff" % label)
        if not nonempty_string(entry.get("subject_id")):
            errors.append("%s.subject_id must be non-empty" % label)
        if not nonempty_string(entry.get("subject_sha256")) or not FINGERPRINT_RE.match(entry.get("subject_sha256", "")):
            errors.append("%s.subject_sha256 must be sha256:<64 lowercase hex>" % label)
        if not canonical_actor_id(entry.get("approved_by")):
            errors.append("%s.approved_by must be a canonical actor ID" % label)
        if not valid_timestamp(entry.get("approved_at")):
            errors.append("%s.approved_at must be an ISO-8601 timestamp" % label)
    return decisions


def bind_decision(decisions, decision_id, subject_type, subject_id, subject_hash,
                  approved_by, approved_at, label, errors):
    decision = decisions.get(decision_id)
    if not decision:
        errors.append("%s decision_id does not reference decisions.json: %s" % (label, decision_id))
        return
    expected = {
        "subject_type": subject_type,
        "subject_id": subject_id,
        "subject_sha256": subject_hash,
        "approved_by": approved_by,
        "approved_at": approved_at,
    }
    for key, value in expected.items():
        if decision.get(key) != value:
            errors.append("%s does not match decision %s field %s" % (label, decision_id, key))


def validate_verification(data, policy, rules_by_id, root, errors):
    if data.get("version") != 1:
        errors.append("verification.version must be 1")
    records = data.get("records")
    if not isinstance(records, list):
        errors.append("verification.records must be a list")
        return
    by_rule = {}
    for index, record in enumerate(records):
        label = "verification.records[%d]" % index
        record = require_mapping(record, label, errors)
        rule_id = record.get("rule_id")
        if not nonempty_string(rule_id):
            errors.append("%s.rule_id must be non-empty" % label)
            continue
        if rule_id in by_rule:
            errors.append("%s has a duplicate rule verification record" % label)
        by_rule[rule_id] = record
        if rule_id not in rules_by_id:
            errors.append("%s.rule_id does not reference a policy rule" % label)
        if record.get("verdict") != "pass":
            errors.append("%s.verdict must be pass" % label)
        identities = [record.get(key) for key in ("maker", "breaker", "verifier")]
        if not all(nonempty_string(identity) for identity in identities):
            errors.append("%s maker, breaker, and verifier must be non-empty" % label)
        elif not all(canonical_actor_id(identity) for identity in identities):
            errors.append("%s maker, breaker, and verifier must be canonical actor IDs" % label)
        elif len({re.sub(r"[^a-z0-9]", "", identity.casefold()) for identity in identities}) != 3:
            errors.append("%s maker, breaker, and verifier must be distinct" % label)
        if not valid_timestamp(record.get("verified_at")):
            errors.append("%s.verified_at must be an ISO-8601 timestamp" % label)
        command = record.get("canonical_command")
        if command != ["python", "scripts/architecture/verify.py"]:
            errors.append("%s.canonical_command must be the canonical verifier argv" % label)

    policy_hash = canonical_sha256(policy)
    for rule_id, rule in rules_by_id.items():
        if rule.get("state") != "enforced":
            continue
        label = "verification for enforced rule %s" % rule_id
        record = by_rule.get(rule_id)
        if not record:
            errors.append("%s is missing" % label)
            continue
        expected = {
            "decision_id": rule.get("approval", {}).get("decision_id"),
            "policy_sha256": policy_hash,
            "validator_sha256": canonical_sha256(rule.get("validator")),
        }
        artifact_hash, artifact_errors = validator_artifact_sha256(root, rule.get("validator", {}))
        errors.extend("%s: %s" % (label, error) for error in artifact_errors)
        expected["artifacts_sha256"] = artifact_hash
        for key, value in expected.items():
            if record.get(key) != value:
                errors.append("%s does not match %s" % (label, key))


def validate_pack(root, policy, baseline, exceptions, decisions=None, verification=None):
    """Return a list of schema/provenance/reference errors."""
    errors = []
    if policy.get("version") != 1:
        errors.append("policy.version must be 1")
    project = policy.get("project")
    if not nonempty_string(project) or project in {"<project-name>", "__PROJECT__"}:
        errors.append("policy.project must name the target project")
    rules = policy.get("rules")
    if not isinstance(rules, list):
        errors.append("policy.rules must be a list")
        rules = []

    rules_by_id = {}
    for index, rule in enumerate(rules):
        rule_id = validate_rule(rule, index, root, errors)
        if nonempty_string(rule_id):
            if rule_id in rules_by_id:
                errors.append("policy rule ID is duplicated: %s" % rule_id)
            else:
                rules_by_id[rule_id] = rule

    baseline_entries = validate_baseline(baseline, set(rules_by_id), root, errors) or []
    exception_entries, exception_ids = validate_exceptions(exceptions, rules_by_id, root, errors)
    decisions_by_id = validate_decisions(decisions or {"version": 1, "decisions": []}, errors)

    for rule_id, rule in rules_by_id.items():
        if rule.get("state") in {"approved", "enforced"}:
            approval = rule.get("approval", {})
            bind_decision(
                decisions_by_id, approval.get("decision_id"), "rule", rule_id,
                canonical_sha256(rule_contract(rule)), approval.get("approved_by"),
                approval.get("approved_at"), "policy rule %s" % rule_id, errors,
            )
    for entry in baseline_entries:
        bind_decision(
            decisions_by_id, entry.get("decision_id"), "baseline", entry.get("fingerprint"),
            canonical_sha256(baseline_contract(entry)), entry.get("approved_by"),
            entry.get("approved_at"), "baseline entry %s" % entry.get("fingerprint"), errors,
        )
    for entry in exception_entries:
        bind_decision(
            decisions_by_id, entry.get("decision_id"), "exception", entry.get("id"),
            canonical_sha256(exception_contract(entry)), entry.get("approved_by"),
            entry.get("approved_at"), "exception %s" % entry.get("id"), errors,
        )

    validate_verification(
        verification or {"version": 1, "records": []}, policy, rules_by_id, root, errors
    )
    for rule_id, rule in rules_by_id.items():
        for exception_id in rule.get("exception_ids", []):
            if exception_id not in exception_ids:
                errors.append("policy rule %s references missing exception %s" % (rule_id, exception_id))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate guardrail-forge policy pack structure.")
    parser.add_argument("--root", default=".", help="target repository root")
    parser.add_argument("--policy", default=".architecture/policy.yaml")
    parser.add_argument("--baseline", default=".architecture/baseline.json")
    parser.add_argument("--exceptions", default=".architecture/exceptions.yaml")
    parser.add_argument("--decisions", default=".architecture/decisions.json")
    parser.add_argument("--verification", default=".architecture/verification.json")
    args = parser.parse_args(argv)

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print("POLICY CONFIG ERROR: root is not a directory: %s" % root)
        return 2
    loaded = []
    for label, value in (
        ("policy", args.policy), ("baseline", args.baseline),
        ("exceptions", args.exceptions), ("decisions", args.decisions),
        ("verification", args.verification),
    ):
        path = Path(value)
        if not path.is_absolute():
            path = root / path
        data, error = load_data(path)
        if error:
            print("POLICY CONFIG ERROR: %s" % error)
            return 2
        loaded.append(data)
    errors = validate_pack(root, loaded[0], loaded[1], loaded[2], loaded[3], loaded[4])
    if errors:
        for error in errors:
            print("POLICY CONFIG ERROR: %s" % error)
        print("Policy pack invalid: %d error(s)." % len(errors))
        return 2
    print("Policy pack valid: %d rule(s)." % len(loaded[0].get("rules", [])))
    return 0


if __name__ == "__main__":
    sys.exit(main())

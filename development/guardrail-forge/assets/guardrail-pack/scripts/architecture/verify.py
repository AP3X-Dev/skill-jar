#!/usr/bin/env python3
"""Canonical read-only architecture verifier for a guardrail-forge pack."""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import validate_policy


PLACEHOLDERS = {
    "root", "rule_id", "policy", "baseline", "exceptions", "decisions",
    "verification", "fixture",
}


def expand_command(command, values):
    expanded = []
    for token in command:
        value = token
        for name in PLACEHOLDERS:
            value = value.replace("{%s}" % name, values[name])
        if "{" in value or "}" in value:
            raise ValueError("unsupported or unexpanded placeholder in %r" % token)
        expanded.append(value)
    return expanded


def run_command(command, cwd, label, quiet=False):
    if not quiet:
        print("RUN [%s] %s" % (label, " ".join(command)))
    try:
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONHASHSEED"] = "0"
        result = subprocess.run(
            command, cwd=str(cwd), text=True, capture_output=True,
            check=False, env=environment,
        )
    except OSError as exc:
        message = "CONFIG [%s] command failed to start: %s" % (label, exc)
        if not quiet:
            print(message)
        return 2, "", message
    if result.stdout and not quiet:
        print(result.stdout.rstrip())
    if result.stderr and not quiet:
        print(result.stderr.rstrip(), file=sys.stderr)
    if not quiet:
        print("EXIT [%s] %d" % (label, result.returncode))
    return result.returncode, result.stdout, result.stderr


def parse_findings(stdout, expected_rule_id, scan_root):
    try:
        data = json.loads(stdout, object_pairs_hook=validate_policy.unique_json_object)
    except ValueError as exc:
        return None, "validator output is not JSON: %s" % str(exc).splitlines()[0]
    if not isinstance(data, dict) or data.get("schema") != "guardrail-findings-v1":
        return None, "validator output schema must be guardrail-findings-v1"
    if data.get("rule_id") != expected_rule_id:
        return None, "validator output rule_id does not match %s" % expected_rule_id
    if data.get("complete") is not True:
        return None, "validator did not attest to a complete scan"
    if data.get("errors", []) != []:
        return None, "validator complete output must contain an empty errors list"
    findings = data.get("findings")
    if not isinstance(findings, list):
        return None, "validator findings must be a list"
    seen_fingerprints = set()
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            return None, "finding %d must be a mapping" % index
        if finding.get("rule_id") != expected_rule_id:
            return None, "finding %d rule_id mismatch" % index
        fingerprint = finding.get("fingerprint")
        if not isinstance(fingerprint, str) or not validate_policy.FINGERPRINT_RE.match(fingerprint):
            return None, "finding %d has invalid fingerprint" % index
        if fingerprint in seen_fingerprints:
            return None, "finding %d duplicates fingerprint %s" % (index, fingerprint)
        seen_fingerprints.add(fingerprint)
        if not validate_policy.contained_existing_path(scan_root, finding.get("path"), require_file=True):
            return None, "finding %d path is missing, unsafe, symlinked, or outside scan root" % index
        if "symbol" in finding and not validate_policy.exact_symbol(finding.get("symbol")):
            return None, "finding %d has an unsafe or non-exact symbol" % index
        if not isinstance(finding.get("message"), str) or not finding.get("message"):
            return None, "finding %d needs a message" % index
    return findings, None


def active_findings_for_rule(findings, rule, baseline, exceptions):
    """Apply exact approved legacy debt and exact approved exceptions centrally."""
    rule_id = rule["id"]
    baseline_keys = {
        (entry.get("fingerprint"), entry.get("path"))
        for entry in baseline.get("entries", [])
        if entry.get("rule_id") == rule_id
    }
    allowed_exception_ids = set(rule.get("exception_ids", []))
    exception_targets = []
    for entry in exceptions.get("exceptions", []):
        if entry.get("id") not in allowed_exception_ids or entry.get("rule_id") != rule_id:
            continue
        target = entry.get("target", {})
        exception_targets.append((
            target.get("path"), target.get("symbol"), target.get("fingerprint")
        ))
    active = []
    for finding in findings:
        if (finding.get("fingerprint"), finding.get("path")) in baseline_keys:
            continue
        suppressed = any(
            finding.get("path") == path
            and finding.get("symbol") == symbol
            and finding.get("fingerprint") == fingerprint
            for path, symbol, fingerprint in exception_targets
        )
        if not suppressed:
            active.append(finding)
    return active


def enforcement_decisions(decisions):
    result = dict(decisions)
    result["decisions"] = [
        entry for entry in decisions.get("decisions", [])
        if not isinstance(entry, dict) or entry.get("subject_type") != "watch-handoff"
    ]
    return result


def compute_authority(root, policy, baseline, exceptions, decisions, verification):
    artifact_hashes = {}
    for rule in policy.get("rules", []):
        if isinstance(rule, dict) and rule.get("state") == "enforced":
            artifact_hashes[rule.get("id", "<missing>")] = validate_policy.validator_artifact_sha256(
                root, rule.get("validator", {}) if isinstance(rule.get("validator"), dict) else {}
            )[0]
    canonical_tools = {}
    for relative in (
        "scripts/architecture/verify.py",
        "scripts/architecture/validate_policy.py",
    ):
        path = root / relative
        canonical_tools[relative] = (
            validate_policy.file_sha256(path)
            if validate_policy.contained_existing_path(root, relative, require_file=True)
            else "missing-or-unsafe"
        )
    return validate_policy.canonical_sha256({
        "policy": policy,
        "baseline": baseline,
        "exceptions": exceptions,
        "decisions": enforcement_decisions(decisions),
        "verification": verification,
        "validator_artifacts": artifact_hashes,
        "canonical_tools": canonical_tools,
    })


def expired_exception_ids(exceptions):
    now = datetime.now(timezone.utc)
    expired = []
    for entry in exceptions.get("exceptions", []):
        value = entry.get("expires_at")
        if not value:
            continue
        candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            when = datetime.fromisoformat(candidate)
        except ValueError:
            continue
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        if when <= now:
            expired.append(entry.get("id", "<unknown>"))
    return expired


def verify(root, fixtures_only=False, policy_only=False, repo_only=False, output_format="text"):
    json_mode = output_format == "json"
    all_findings = []
    errors_out = []
    enforced = []
    authority_sha256 = ""

    def report(message):
        if not json_mode:
            print(message)

    def finish(code, status):
        if json_mode:
            complete = (
                status in {"pass", "violation"}
                and not errors_out
                and (status != "violation" or bool(all_findings))
            )
            print(json.dumps({
                "schema": "guardrail-verification-v1",
                "complete": complete,
                "status": status,
                "rules_run": len(enforced),
                "authority_sha256": authority_sha256,
                "findings": all_findings,
                "errors": errors_out,
            }, sort_keys=True))
        return code

    policy_path = root / ".architecture" / "policy.yaml"
    baseline_path = root / ".architecture" / "baseline.json"
    exceptions_path = root / ".architecture" / "exceptions.yaml"
    decisions_path = root / ".architecture" / "decisions.json"
    verification_path = root / ".architecture" / "verification.json"
    loaded = []
    for path in (policy_path, baseline_path, exceptions_path, decisions_path, verification_path):
        data, error = validate_policy.load_data(path)
        if error:
            errors_out.append(error)
            report("CONFIG: %s" % error)
            return finish(2, "config-error")
        loaded.append(data)
    policy, baseline, exceptions, decisions, verification = loaded
    authority_sha256 = compute_authority(
        root, policy, baseline, exceptions, decisions, verification
    )
    errors = validate_policy.validate_pack(
        root, policy, baseline, exceptions, decisions, verification
    )
    if errors:
        for error in errors:
            errors_out.append(error)
            report("CONFIG: %s" % error)
        return finish(2, "config-error")
    expired = expired_exception_ids(exceptions)
    if expired:
        message = "expired architecture exception(s): %s" % ", ".join(expired)
        errors_out.append(message)
        report("VIOLATION: %s" % message)
        return finish(1, "violation")
    if policy_only:
        report("Architecture policy pack valid.")
        return finish(0, "policy-valid")

    enforced = [rule for rule in policy.get("rules", []) if rule.get("state") == "enforced"]
    if not enforced:
        message = "no enforced architecture rules ran; use --policy-only for Level 1 schema validation"
        errors_out.append(message)
        report("CONFIG: %s" % message)
        return finish(2, "empty-enforcement")
    fixture_failure = False
    config_failure = False
    repo_violation = False
    common = {
        "root": str(root),
        "policy": str(policy_path),
        "baseline": str(baseline_path),
        "exceptions": str(exceptions_path),
        "decisions": str(decisions_path),
        "verification": str(verification_path),
    }
    for rule in enforced:
        rule_id = rule["id"]
        command = rule["validator"]["command"]
        fixtures = rule["validator"]["fixtures"]
        if not repo_only:
            fixture_cases = (("positive", 0), ("negative", 1))
        else:
            fixture_cases = ()
        for kind, expected in fixture_cases:
            for fixture in fixtures[kind]:
                fixture_path = (root / fixture).resolve()
                values = dict(common, rule_id=rule_id, fixture=str(fixture_path))
                try:
                    argv = expand_command(command, values)
                except ValueError as exc:
                    errors_out.append("%s: %s" % (rule_id, exc))
                    report("CONFIG [%s] %s" % (rule_id, exc))
                    config_failure = True
                    continue
                code, stdout, _stderr = run_command(
                    argv, root, "%s fixture %s" % (rule_id, kind), quiet=json_mode
                )
                findings, parse_error = parse_findings(stdout, rule_id, fixture_path)
                if code == 2 or code not in {0, 1}:
                    config_failure = True
                elif parse_error:
                    errors_out.append("%s fixture %s: %s" % (rule_id, kind, parse_error))
                    report("CONFIG [%s fixture %s] %s" % (rule_id, kind, parse_error))
                    config_failure = True
                elif code != expected:
                    fixture_failure = True
                    report("FIXTURE FAIL [%s] %s expected %d, got %d" % (
                        rule_id, fixture, expected, code
                    ))
                elif expected == 0 and findings:
                    fixture_failure = True
                    report("FIXTURE FAIL [%s] positive fixture reported findings" % rule_id)
                elif expected == 1 and not findings:
                    fixture_failure = True
                    report("FIXTURE FAIL [%s] negative fixture reported no finding" % rule_id)
        if fixtures_only and not repo_only:
            continue
        values = dict(common, rule_id=rule_id, fixture=str(root))
        try:
            argv = expand_command(command, values)
        except ValueError as exc:
            errors_out.append("%s: %s" % (rule_id, exc))
            report("CONFIG [%s] %s" % (rule_id, exc))
            config_failure = True
            continue
        code, stdout, _stderr = run_command(
            argv, root, "%s repository" % rule_id, quiet=json_mode
        )
        findings, parse_error = parse_findings(stdout, rule_id, root)
        if parse_error:
            errors_out.append("%s repository: %s" % (rule_id, parse_error))
            report("CONFIG [%s repository] %s" % (rule_id, parse_error))
            config_failure = True
            continue
        raw_findings = findings
        if code == 1 and not raw_findings:
            config_failure = True
            errors_out.append("%s exited 1 without findings" % rule_id)
            continue
        if code == 0 and raw_findings:
            config_failure = True
            errors_out.append("%s exited 0 while reporting findings" % rule_id)
            continue
        if code == 2 or code not in {0, 1}:
            config_failure = True
            continue
        findings = active_findings_for_rule(raw_findings, rule, baseline, exceptions)
        for finding in findings:
            finding.setdefault("remediation", rule.get("remediation"))
            finding["kind"] = rule.get("routing", {}).get("kind")
            finding["owner"] = rule.get("routing", {}).get("owner")
        all_findings.extend(findings)
        if findings:
            repo_violation = True
    reloaded = []
    for path in (policy_path, baseline_path, exceptions_path, decisions_path, verification_path):
        data, error = validate_policy.load_data(path)
        if error:
            message = "authority file changed or became unreadable during verification: %s" % error
            errors_out.append(message)
            report("CONFIG: %s" % message)
            config_failure = True
            break
        reloaded.append(data)
    if len(reloaded) == 5:
        if reloaded != loaded:
            message = "architecture pack content changed during verification"
            errors_out.append(message)
            report("CONFIG: %s" % message)
            config_failure = True
        final_authority = compute_authority(root, *reloaded)
        if final_authority != authority_sha256:
            message = "policy, validator, fixture, or canonical-tool authority changed during verification"
            errors_out.append(message)
            report("CONFIG: %s" % message)
            config_failure = True
    if config_failure:
        report("Architecture verification failed: configuration/tool/incomplete scan.")
        return finish(2, "config-error")
    if fixture_failure or repo_violation:
        report("Architecture verification failed: violation or fixture contract failure.")
        return finish(1, "violation")
    report("Architecture verification passed: %d enforced rule(s)." % len(enforced))
    return finish(0, "pass")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the canonical architecture guardrail.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--fixtures-only", action="store_true")
    group.add_argument("--policy-only", action="store_true")
    group.add_argument("--repo-only", action="store_true")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print("CONFIG: root is not a directory: %s" % root)
        return 2
    return verify(root, args.fixtures_only, args.policy_only, args.repo_only, args.format)


if __name__ == "__main__":
    sys.exit(main())

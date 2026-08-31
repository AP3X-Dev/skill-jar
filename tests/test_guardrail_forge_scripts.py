"""Focused tests for the guardrail-forge bundled scripts and project pack."""

import importlib.util
import json
import os
import stat
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "development" / "guardrail-forge"
SCRIPTS = SKILL / "scripts"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validate = load("guardrail_validate_policy", "validate-policy.py")
scaffold = load("guardrail_scaffold", "scaffold-guardrail.py")
inspect_project = load("guardrail_inspect_project", "inspect-project.py")


class GuardrailForgeScripts(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="guardrail_forge_test_"))
        (self.tmp / ".git").mkdir()
        self.validator_root = "scripts/architecture/validators/TENANCY-001"
        self.validator_rel = self.validator_root + "/validator.py"

    def tearDown(self):
        def remove_readonly(function, path, _error):
            os.chmod(path, stat.S_IWRITE)
            function(path)

        shutil.rmtree(self.tmp, onerror=remove_readonly)

    def good_policy(self):
        (self.tmp / "src").mkdir(exist_ok=True)
        (self.tmp / "src" / "tenant.py").write_text("TENANT = True\n", encoding="utf-8")
        validator_path = self.tmp / self.validator_rel
        validator_path.parent.mkdir(parents=True, exist_ok=True)
        if not validator_path.exists():
            validator_path.write_text("# test validator\n", encoding="utf-8")
        positive = self.tmp / "scripts" / "architecture" / "fixtures" / "TENANCY-001" / "valid"
        negative = self.tmp / "scripts" / "architecture" / "fixtures" / "TENANCY-001" / "invalid"
        positive.mkdir(parents=True, exist_ok=True)
        negative.mkdir(parents=True, exist_ok=True)
        return {
            "version": 1,
            "project": "sample",
            "rules": [{
                "id": "TENANCY-001",
                "statement": "Tenant-owned models carry tenant identity.",
                "state": "enforced",
                "severity": "error",
                "scope": {"include": ["src/**/*.py"], "exclude": []},
                "evidence": [{
                    "type": "source",
                    "locator": "src/tenant.py",
                    "note": "Current tenant context.",
                }],
                "provenance": {
                    "discovered_at": "2026-08-29T18:00:00Z",
                    "source_commit": "0123456789abcdef",
                    "sources": ["repository"],
                },
                "approval": {
                    "decision_id": "ARCH-001",
                    "approved_by": "owner",
                    "approved_at": "2026-08-29T19:00:00Z",
                },
                "validator": {
                    "command": ["python", self.validator_rel, "--root", "{fixture}"],
                    "output_format": "guardrail-findings-v1",
                    "entrypoint": self.validator_rel,
                    "implementation_root": self.validator_root,
                    "fixtures": {
                        "positive": ["scripts/architecture/fixtures/TENANCY-001/valid"],
                        "negative": ["scripts/architecture/fixtures/TENANCY-001/invalid"],
                    },
                },
                "remediation": "Add the tenant identity.",
                "exception_ids": [],
                "routing": {"kind": "tenancy-boundary", "owner": "architecture-owner"},
            }],
        }

    def approvals_for(self, policy):
        rule = policy["rules"][0]
        decisions = {
            "version": 1,
            "decisions": [{
                "id": "ARCH-001",
                "status": "approved",
                "subject_type": "rule",
                "subject_id": rule["id"],
                "subject_sha256": validate.canonical_sha256(validate.rule_contract(rule)),
                "approved_by": "owner",
                "approved_at": "2026-08-29T19:00:00Z",
            }],
        }
        verification = {
            "version": 1,
            "records": [{
                "rule_id": rule["id"],
                "decision_id": "ARCH-001",
                "verdict": "pass",
                "maker": "maker-agent",
                "breaker": "breaker-agent",
                "verifier": "verifier-agent",
                "verified_at": "2026-08-29T20:00:00Z",
                "canonical_command": ["python", "scripts/architecture/verify.py"],
                "policy_sha256": validate.canonical_sha256(policy),
                "validator_sha256": validate.canonical_sha256(rule["validator"]),
                "artifacts_sha256": validate.validator_artifact_sha256(
                    self.tmp, rule["validator"]
                )[0],
            }],
        }
        return decisions, verification

    def test_valid_enforced_rule_requires_real_approval_and_fixtures(self):
        policy = self.good_policy()
        decisions, verification = self.approvals_for(policy)
        errors = validate.validate_pack(
            self.tmp, policy,
            {"version": 1, "source_commit": "", "entries": []},
            {"version": 1, "exceptions": []},
            decisions, verification,
        )
        self.assertEqual(errors, [])

        del policy["rules"][0]["approval"]
        errors = validate.validate_pack(
            self.tmp, policy,
            {"version": 1, "source_commit": "", "entries": []},
            {"version": 1, "exceptions": []},
            decisions, verification,
        )
        self.assertTrue(any("approval" in error for error in errors), errors)

    def test_rejects_baseline_write_commands_and_wildcard_waivers(self):
        policy = self.good_policy()
        decisions, verification = self.approvals_for(policy)
        policy["rules"][0]["validator"]["command"].append("--write-baseline")
        baseline = {
            "version": 1,
            "source_commit": "abc",
            "entries": [{
                "fingerprint": "sha256:" + "a" * 64,
                "rule_id": "TENANCY-001",
                "path": "src/legacy/**",
                "reason": "legacy",
                "decision_id": "ARCH-002",
                "approved_by": "owner",
                "approved_at": "2026-08-29T19:00:00Z",
            }],
        }
        errors = validate.validate_pack(
            self.tmp, policy, baseline,
            {"version": 1, "exceptions": []},
            decisions, verification,
        )
        self.assertTrue(any("may not mutate the baseline" in error for error in errors), errors)
        self.assertTrue(any("without globs" in error for error in errors), errors)
        for token in ("--write_baseline", "--writebaseline", "--baseline-write", "--refresh-baseline", "-w"):
            self.assertTrue(validate.command_requests_baseline_mutation([token]), token)

    def test_rejects_windows_absolute_unc_and_rooted_paths(self):
        unsafe = [
            r"C:\Windows\win.ini", "C:/Windows/win.ini", r"C:relative.txt",
            r"\\server\share\policy.json", r"\rooted\file.py", "/etc/passwd",
            "CON", "src/a:b.py", "src/trailing.", "src/new\nline.py",
        ]
        for value in unsafe:
            self.assertFalse(validate.exact_relative_path(value), value)
        self.assertTrue(validate.exact_relative_path("src/models/tenant.py"))
        for pattern in ("CON/**/*.py", "src/NUL/*.py", "src/trailing./*.py", "src/trailing /x.py"):
            self.assertFalse(validate.safe_scope_pattern(pattern), pattern)

        policy = self.good_policy()
        decisions, verification = self.approvals_for(policy)
        policy["rules"][0]["evidence"][0]["locator"] = r"C:\Windows\win.ini"
        policy["rules"][0]["scope"]["include"] = [r"C:\repo\src\**\*.py"]
        errors = validate.validate_pack(
            self.tmp, policy,
            {"version": 1, "source_commit": "", "entries": []},
            {"version": 1, "exceptions": []}, decisions, verification,
        )
        self.assertTrue(any("locator must be an exact safe" in error for error in errors), errors)
        self.assertTrue(any("scope.include contains an unsafe" in error for error in errors), errors)

    def test_binds_approval_and_distinct_checker_records_to_policy(self):
        policy = self.good_policy()
        decisions, verification = self.approvals_for(policy)
        decisions["decisions"][0]["subject_sha256"] = "sha256:" + "0" * 64
        verification["records"][0]["verifier"] = "maker-agent"
        errors = validate.validate_pack(
            self.tmp, policy,
            {"version": 1, "source_commit": "", "entries": []},
            {"version": 1, "exceptions": []}, decisions, verification,
        )
        self.assertTrue(any("subject_sha256" in error for error in errors), errors)
        self.assertTrue(any("must be distinct" in error for error in errors), errors)

        decoy_root = self.tmp / "scripts" / "architecture" / "validators" / "DECOY"
        decoy_root.mkdir(parents=True, exist_ok=True)
        decoy_path = decoy_root / "validator.py"
        decoy_path.write_text("# decoy\n", encoding="utf-8")
        (self.tmp / "actual.py").write_text("# actual runner\n", encoding="utf-8")
        policy = self.good_policy()
        policy["rules"][0]["validator"]["implementation_root"] = decoy_root.relative_to(self.tmp).as_posix()
        policy["rules"][0]["validator"]["entrypoint"] = decoy_path.relative_to(self.tmp).as_posix()
        policy["rules"][0]["validator"]["command"] = [
            sys.executable, "actual.py", decoy_path.relative_to(self.tmp).as_posix(),
            "--root", "{fixture}"
        ]
        decisions, verification = self.approvals_for(policy)
        errors = validate.validate_pack(
            self.tmp, policy,
            {"version": 1, "source_commit": "", "entries": []},
            {"version": 1, "exceptions": []}, decisions, verification,
        )
        self.assertTrue(any("runtime + exact entrypoint" in error for error in errors), errors)
        self.assertTrue(any("outside implementation_root" in error for error in errors), errors)

    def test_validator_implementation_root_binds_imported_helpers(self):
        policy = self.good_policy()
        decisions, verification = self.approvals_for(policy)
        helper = self.tmp / self.validator_root / "helper.py"
        helper.write_text("VALUE = 1\n", encoding="utf-8")
        errors = validate.validate_pack(
            self.tmp, policy,
            {"version": 1, "source_commit": "", "entries": []},
            {"version": 1, "exceptions": []}, decisions, verification,
        )
        self.assertTrue(any("artifacts_sha256" in error for error in errors), errors)

    def test_validator_implementation_root_binds_empty_directories(self):
        policy = self.good_policy()
        decisions, verification = self.approvals_for(policy)
        (self.tmp / self.validator_root / "behavior-mode").mkdir()
        errors = validate.validate_pack(
            self.tmp, policy,
            {"version": 1, "source_commit": "", "entries": []},
            {"version": 1, "exceptions": []}, decisions, verification,
        )
        self.assertTrue(any("artifacts_sha256" in error for error in errors), errors)

    @unittest.skipUnless(sys.platform == "win32", "NTFS named-stream test")
    def test_validator_implementation_root_binds_ntfs_named_streams(self):
        policy = self.good_policy()
        decisions, verification = self.approvals_for(policy)
        entrypoint = self.tmp / self.validator_rel
        stream = Path(str(entrypoint) + ":behavior-mode")
        try:
            stream.write_text("alternate behavior\n", encoding="utf-8")
        except OSError as error:
            self.skipTest("named streams unavailable: %s" % error)
        errors = validate.validate_pack(
            self.tmp, policy,
            {"version": 1, "source_commit": "", "entries": []},
            {"version": 1, "exceptions": []}, decisions, verification,
        )
        self.assertTrue(any("artifacts_sha256" in error for error in errors), errors)

    def test_validator_command_rejects_symlink_alias_to_bound_entrypoint(self):
        policy = self.good_policy()
        alias = self.tmp / "scripts" / "architecture" / "outside-alias"
        try:
            alias.symlink_to(self.tmp / self.validator_root, target_is_directory=True)
        except OSError as error:
            self.skipTest("directory symlink unavailable: %s" % error)
        policy["rules"][0]["validator"]["command"][1] = (
            "scripts/architecture/outside-alias/validator.py"
        )
        decisions, verification = self.approvals_for(policy)
        errors = validate.validate_pack(
            self.tmp, policy,
            {"version": 1, "source_commit": "", "entries": []},
            {"version": 1, "exceptions": []}, decisions, verification,
        )
        self.assertTrue(
            any(
                "runtime + exact entrypoint" in error
                or "ambiguous, or unsupported path-like" in error
                for error in errors
            ),
            errors,
        )

    def test_validator_command_rejects_punctuation_free_symlink_alias(self):
        self.good_policy()
        bound_config = self.tmp / self.validator_root / "boundconfig"
        bound_config.write_text("bound\n", encoding="utf-8")
        alias = self.tmp / "alias"
        try:
            alias.symlink_to(bound_config)
        except OSError as error:
            self.skipTest("file symlink unavailable: %s" % error)

        for token in ("alias", "--config=alias", "-Xalias"):
            policy = self.good_policy()
            policy["rules"][0]["validator"]["command"].append(token)
            decisions, verification = self.approvals_for(policy)
            errors = validate.validate_pack(
                self.tmp, policy,
                {"version": 1, "source_commit": "", "entries": []},
                {"version": 1, "exceptions": []}, decisions, verification,
            )
            self.assertTrue(
                any("ambiguous, or unsupported path-like" in error for error in errors),
                (token, errors),
            )

    def test_validator_command_binds_directory_arguments(self):
        policy = self.good_policy()
        internal = self.tmp / self.validator_root / "plugins"
        internal.mkdir()
        (internal / "plugin.py").write_text("VALUE = 1\n", encoding="utf-8")
        policy["rules"][0]["validator"]["command"].extend([
            "--plugin-dir", internal.relative_to(self.tmp).as_posix(),
        ])
        decisions, verification = self.approvals_for(policy)
        errors = validate.validate_pack(
            self.tmp, policy,
            {"version": 1, "source_commit": "", "entries": []},
            {"version": 1, "exceptions": []}, decisions, verification,
        )
        self.assertEqual(errors, [])

        policy = self.good_policy()
        policy["rules"][0]["validator"]["command"][2] = "--fixture_path"
        decisions, verification = self.approvals_for(policy)
        errors = validate.validate_pack(
            self.tmp, policy,
            {"version": 1, "source_commit": "", "entries": []},
            {"version": 1, "exceptions": []}, decisions, verification,
        )
        self.assertEqual(errors, [])

        policy = self.good_policy()
        external = self.tmp / "scripts" / "unbound-plugin-dir"
        external.mkdir(parents=True)
        (external / "plugin.py").write_text("VALUE = 1\n", encoding="utf-8")
        policy["rules"][0]["validator"]["command"].append(
            "--plugin-dir=%s" % external.relative_to(self.tmp).as_posix()
        )
        decisions, verification = self.approvals_for(policy)
        errors = validate.validate_pack(
            self.tmp, policy,
            {"version": 1, "source_commit": "", "entries": []},
            {"version": 1, "exceptions": []}, decisions, verification,
        )
        self.assertTrue(any("paths outside implementation_root" in error for error in errors), errors)

        for attached in (
            "--plugin-dir:%s" % external.relative_to(self.tmp).as_posix(),
            "-I%s" % external.relative_to(self.tmp).as_posix(),
        ):
            policy = self.good_policy()
            policy["rules"][0]["validator"]["command"].append(attached)
            decisions, verification = self.approvals_for(policy)
            errors = validate.validate_pack(
                self.tmp, policy,
                {"version": 1, "source_commit": "", "entries": []},
                {"version": 1, "exceptions": []}, decisions, verification,
            )
            self.assertTrue(
                any("paths outside implementation_root" in error for error in errors),
                (attached, errors),
            )

        outside_config = self.tmp / "src" / "outside-config.json"
        outside_config.write_text("{}\n", encoding="utf-8")
        for composite in (
            "--config=@src/outside-config.json",
            "--config:=@@src/outside-config.json",
        ):
            policy = self.good_policy()
            policy["rules"][0]["validator"]["command"].append(composite)
            decisions, verification = self.approvals_for(policy)
            errors = validate.validate_pack(
                self.tmp, policy,
                {"version": 1, "source_commit": "", "entries": []},
                {"version": 1, "exceptions": []}, decisions, verification,
            )
            self.assertTrue(
                any(
                    "paths outside implementation_root" in error
                    or "ambiguous, or unsupported path-like" in error
                    for error in errors
                ),
                (composite, errors),
            )

        for ambiguous in (
            "--plugins=dummy,src/outside-config.json",
            "--config=src/not-created.json",
            "@future.rsp",
            "--config=@future.json",
            "--config=src%2Foutside.json",
            "-I:missing=scripts/architecture/validators/TENANCY-001/validator.py",
            "-Isrc/outside-config.json,%s" % self.validator_rel,
            "-Ifuture",
            "-I",
            "--config=",
            "--config:",
            "--src/outside=mode",
            "--=mode",
            "--:mode",
            "---config=mode",
        ):
            policy = self.good_policy()
            policy["rules"][0]["validator"]["command"].append(ambiguous)
            decisions, verification = self.approvals_for(policy)
            errors = validate.validate_pack(
                self.tmp, policy,
                {"version": 1, "source_commit": "", "entries": []},
                {"version": 1, "exceptions": []}, decisions, verification,
            )
            self.assertTrue(
                any("ambiguous, or unsupported path-like" in error for error in errors),
                (ambiguous, errors),
            )

        bound_config = self.tmp / self.validator_root / "bound-config"
        bound_config.mkdir()
        outside_directory = self.tmp / "src" / "outside-config"
        outside_directory.mkdir()
        (outside_directory / "behavior.json").write_text("{}\n", encoding="utf-8")
        policy = self.good_policy()
        policy["rules"][0]["validator"]["command"].append(
            "--plugin-path=%s:%s" % (
                outside_directory.relative_to(self.tmp).as_posix(),
                bound_config.relative_to(self.tmp).as_posix(),
            )
        )
        decisions, verification = self.approvals_for(policy)
        errors = validate.validate_pack(
            self.tmp, policy,
            {"version": 1, "source_commit": "", "entries": []},
            {"version": 1, "exceptions": []}, decisions, verification,
        )
        self.assertTrue(
            any("ambiguous, or unsupported path-like" in error for error in errors),
            errors,
        )

    def test_validator_rejects_attached_dynamic_execution_and_runtime_shadowing(self):
        policy = self.good_policy()
        policy["rules"][0]["validator"]["command"] = [
            "python", "-cprint('false green')", self.validator_rel,
            "--root", "{fixture}",
        ]
        (self.tmp / "python.exe").write_text("shadow\n", encoding="utf-8")
        decisions, verification = self.approvals_for(policy)
        errors = validate.validate_pack(
            self.tmp, policy,
            {"version": 1, "source_commit": "", "entries": []},
            {"version": 1, "exceptions": []}, decisions, verification,
        )
        self.assertTrue(any("runtime + exact entrypoint" in error for error in errors), errors)
        self.assertTrue(any("shadowed" in error for error in errors), errors)

        policy = self.good_policy()
        (self.tmp / "outside.py").write_text("# unbound helper\n", encoding="utf-8")
        policy["rules"][0]["validator"]["command"] = [
            "python", self.validator_rel, "--scanner", "{root}/outside.py",
            "--root", "{fixture}",
        ]
        decisions, verification = self.approvals_for(policy)
        errors = validate.validate_pack(
            self.tmp, policy,
            {"version": 1, "source_commit": "", "entries": []},
            {"version": 1, "exceptions": []}, decisions, verification,
        )
        self.assertTrue(any("placeholders must be standalone" in error for error in errors), errors)

    def test_scaffold_previews_applies_idempotently_and_refuses_conflicts(self):
        preview = scaffold.scaffold(self.tmp, host="generic", apply=False)
        self.assertTrue(any(action == "create" for action, _path, _content in preview))
        self.assertFalse((self.tmp / ".architecture" / "policy.yaml").exists())

        applied = scaffold.scaffold(self.tmp, host="generic", apply=True)
        self.assertFalse(any(action == "conflict" for action, _path, _content in applied))
        self.assertTrue((self.tmp / "scripts" / "architecture" / "verify.py").exists())
        self.assertFalse((self.tmp / ".claude").exists())
        self.assertFalse((self.tmp / ".codex").exists())

        second = scaffold.scaffold(self.tmp, host="generic", apply=True)
        self.assertTrue(all(action == "skip (identical)" for action, _path, _content in second))

        policy_path = self.tmp / ".architecture" / "policy.yaml"
        policy_path.write_text("different\n", encoding="utf-8")
        conflict = scaffold.scaffold(self.tmp, host="generic", apply=True)
        self.assertTrue(any(action == "conflict" for action, _path, _content in conflict))
        self.assertEqual(policy_path.read_text(encoding="utf-8"), "different\n")

    def test_scaffold_encodes_project_names_for_json_and_single_line_text(self):
        files = scaffold.desired_files(Path('acme"repo\nline'), host="generic")
        policy = json.loads(files[Path(".architecture/policy.yaml")])
        self.assertEqual(policy["project"], 'acme"repo\nline')
        heading = files[Path(".architecture/evidence.md")].splitlines()[0]
        self.assertEqual(heading, '# Architecture guardrail evidence -- acme"repo\\u000aline')

        surrogate_name = "raw-\udcff"
        surrogate_files = scaffold.desired_files(Path(surrogate_name), host="generic")
        for content in surrogate_files.values():
            content.encode("utf-8")
        surrogate_policy = json.loads(surrogate_files[Path(".architecture/policy.yaml")])
        self.assertEqual(surrogate_policy["project"], surrogate_name)

    def test_scaffold_rejects_symlinked_destination_ancestor(self):
        outside = Path(tempfile.mkdtemp(prefix="guardrail_outside_"))
        try:
            try:
                os.symlink(str(outside), str(self.tmp / ".architecture"), target_is_directory=True)
            except OSError as exc:
                self.skipTest("directory symlink unavailable: %s" % exc)
            result = scaffold.scaffold(self.tmp, host="generic", apply=True)
            self.assertTrue(any(
                action == "conflict" and path.as_posix().startswith(".architecture/")
                for action, path, _content in result
            ))
            self.assertFalse((outside / "policy.yaml").exists())
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    @unittest.skipUnless(os.name == "nt" and hasattr(Path, "is_junction"), "Windows junction test")
    def test_scaffold_rejects_junctioned_destination_ancestor(self):
        outside = Path(tempfile.mkdtemp(prefix="guardrail_scaffold_junction_"))
        junction = self.tmp / ".architecture"
        try:
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
                capture_output=True, text=True, check=False,
            )
            if result.returncode != 0:
                self.skipTest("junction creation unavailable: %s" % (result.stdout + result.stderr))
            actions = scaffold.scaffold(self.tmp, host="generic", apply=True)
            self.assertTrue(any(
                action == "conflict" and path.as_posix().startswith(".architecture/")
                for action, path, _content in actions
            ))
            self.assertFalse((outside / "policy.yaml").exists())
        finally:
            if junction.is_junction():
                junction.rmdir()
            shutil.rmtree(outside, ignore_errors=True)

    @unittest.skipUnless(os.name == "nt" and hasattr(Path, "is_junction"), "Windows junction test")
    def test_scaffold_rejects_junction_swap_after_preflight(self):
        outside = Path(tempfile.mkdtemp(prefix="guardrail_scaffold_race_"))
        junction = self.tmp / ".architecture"
        calls = 0

        def race_after_preflight(repo, destination):
            nonlocal calls
            calls += 1
            if calls == 2:
                result = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
                    capture_output=True, text=True, check=False,
                )
                if result.returncode != 0:
                    self.skipTest(
                        "junction creation unavailable: %s" % (result.stdout + result.stderr)
                    )
            return True

        files = {Path(".architecture/policy.yaml"): '{"version": 1}\n'}
        try:
            with (
                mock.patch.object(scaffold, "desired_files", return_value=files),
                mock.patch.object(scaffold, "safe_destination", side_effect=race_after_preflight),
            ):
                with self.assertRaises(RuntimeError):
                    scaffold.scaffold(self.tmp, host="generic", apply=True)
            self.assertFalse((outside / "policy.yaml").exists())
        finally:
            if junction.is_junction():
                junction.rmdir()
            shutil.rmtree(outside, ignore_errors=True)

    def test_scaffold_rejects_repository_root_identity_swap_after_preflight(self):
        original = self.tmp.with_name(self.tmp.name + "_preflighted")
        calls = 0

        def swap_root_after_preflight(repo, destination):
            nonlocal calls
            calls += 1
            if calls == 2:
                self.tmp.rename(original)
                self.tmp.mkdir()
            return True

        files = {Path(".architecture/policy.yaml"): '{"version": 1}\n'}
        try:
            with (
                mock.patch.object(scaffold, "desired_files", return_value=files),
                mock.patch.object(scaffold, "safe_destination", side_effect=swap_root_after_preflight),
            ):
                with self.assertRaisesRegex(RuntimeError, "root identity changed"):
                    scaffold.scaffold(self.tmp, host="generic", apply=True)
            self.assertFalse((self.tmp / ".architecture" / "policy.yaml").exists())
            self.assertFalse((original / ".architecture" / "policy.yaml").exists())
        finally:
            shutil.rmtree(self.tmp, ignore_errors=True)
            if original.exists():
                original.rename(self.tmp)

    def test_scaffold_late_collision_leaves_exact_created_files_for_rerun(self):
        files = {
            Path("a/generated.txt"): "generated first\n",
            Path("b/generated.txt"): "generated second\n",
        }
        real_secure_create = scaffold.secure_create
        calls = 0

        def inject_late_collision(repo, relative, content, executable, expected_root):
            nonlocal calls
            if relative == scaffold.RECOVERY_RELATIVE:
                return real_secure_create(repo, relative, content, executable, expected_root)
            calls += 1
            if calls == 2:
                destination = repo / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text("late collision\n", encoding="utf-8")
            return real_secure_create(repo, relative, content, executable, expected_root)

        with (
            mock.patch.object(scaffold, "desired_files", return_value=files),
            mock.patch.object(scaffold, "secure_create", side_effect=inject_late_collision),
        ):
            with self.assertRaisesRegex(RuntimeError, "previously completed paths require review"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)

        self.assertEqual(
            (self.tmp / "a" / "generated.txt").read_text(encoding="utf-8"),
            "generated first\n",
        )
        self.assertEqual(
            (self.tmp / "b" / "generated.txt").read_text(encoding="utf-8"),
            "late collision\n",
        )

    def test_scaffold_recovery_preserves_same_byte_replacement(self):
        files = {
            Path("a/generated.txt"): "same bytes\n",
            Path("b/generated.txt"): "second\n",
        }
        real_secure_create = scaffold.secure_create
        calls = 0

        def replace_then_fail(repo, relative, content, executable, expected_root):
            nonlocal calls
            if relative == scaffold.RECOVERY_RELATIVE:
                return real_secure_create(repo, relative, content, executable, expected_root)
            calls += 1
            if calls == 1:
                created_identity = real_secure_create(
                    repo, relative, content, executable, expected_root
                )
                destination = repo / relative
                destination.rename(destination.with_name("apply-owned.txt"))
                destination.write_text(content, encoding="utf-8")
                return created_identity
            destination = repo / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text("late collision\n", encoding="utf-8")
            return real_secure_create(repo, relative, content, executable, expected_root)

        with (
            mock.patch.object(scaffold, "desired_files", return_value=files),
            mock.patch.object(scaffold, "secure_create", side_effect=replace_then_fail),
        ):
            with self.assertRaisesRegex(RuntimeError, "previously completed paths require review"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)

        self.assertEqual(
            (self.tmp / "a" / "generated.txt").read_text(encoding="utf-8"),
            "same bytes\n",
        )
        self.assertTrue((self.tmp / "a" / "apply-owned.txt").exists())

    def test_scaffold_recovery_preserves_raw_byte_change(self):
        files = {
            Path("a/generated.txt"): "generated first\n",
            Path("b/generated.txt"): "second\n",
        }
        real_secure_create = scaffold.secure_create
        calls = 0

        def change_newlines_then_fail(repo, relative, content, executable, expected_root):
            nonlocal calls
            if relative == scaffold.RECOVERY_RELATIVE:
                return real_secure_create(repo, relative, content, executable, expected_root)
            calls += 1
            if calls == 1:
                created_identity = real_secure_create(
                    repo, relative, content, executable, expected_root
                )
                (repo / relative).write_bytes(b"generated first\r\n")
                return created_identity
            destination = repo / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text("late collision\n", encoding="utf-8")
            return real_secure_create(repo, relative, content, executable, expected_root)

        with (
            mock.patch.object(scaffold, "desired_files", return_value=files),
            mock.patch.object(scaffold, "secure_create", side_effect=change_newlines_then_fail),
        ):
            with self.assertRaisesRegex(RuntimeError, "previously completed paths require review"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)

        self.assertEqual(
            (self.tmp / "a" / "generated.txt").read_bytes(),
            b"generated first\r\n",
        )

    def test_scaffold_reports_partial_current_destination_for_manual_review(self):
        files = {
            Path("a/generated.txt"): "first\n",
            Path("b/generated.txt"): "second\n",
        }
        real_secure_create = scaffold.secure_create
        calls = 0

        def fail_mid_write(repo, relative, content, executable, expected_root):
            nonlocal calls
            if relative == scaffold.RECOVERY_RELATIVE:
                return real_secure_create(repo, relative, content, executable, expected_root)
            calls += 1
            if calls == 2:
                destination = repo / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(b"part")
                raise OSError("injected write failure")
            return real_secure_create(repo, relative, content, executable, expected_root)

        with (
            mock.patch.object(scaffold, "desired_files", return_value=files),
            mock.patch.object(scaffold, "secure_create", side_effect=fail_mid_write),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "current destination may be partial: b/generated.txt",
            ):
                scaffold.scaffold(self.tmp, host="generic", apply=True)

        recovery = json.loads(
            (self.tmp / scaffold.RECOVERY_RELATIVE).read_text(encoding="utf-8")
        )
        self.assertEqual(recovery["status"], "apply-in-progress")
        self.assertEqual(
            recovery["planned_create_paths"],
            ["a/generated.txt", "b/generated.txt"],
        )
        with mock.patch.object(scaffold, "desired_files", return_value=files):
            with self.assertRaisesRegex(RuntimeError, "recovery marker requires human review"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)

        rerun = scaffold.classify(self.tmp, files)
        actions = {path.as_posix(): action for action, path, _content in rerun}
        self.assertEqual(actions["a/generated.txt"], "skip (identical)")
        self.assertEqual(actions["b/generated.txt"], "conflict")
        self.assertEqual((self.tmp / "b" / "generated.txt").read_bytes(), b"part")

    def test_scaffold_recovery_marker_blocks_full_looking_uncertain_write(self):
        files = {Path("generated.txt"): "complete-looking\n"}
        real_secure_create = scaffold.secure_create

        def write_then_report_failure(repo, relative, content, executable, expected_root):
            if relative == scaffold.RECOVERY_RELATIVE:
                return real_secure_create(repo, relative, content, executable, expected_root)
            real_secure_create(repo, relative, content, executable, expected_root)
            raise OSError("post-write acknowledgement failed")

        with (
            mock.patch.object(scaffold, "desired_files", return_value=files),
            mock.patch.object(
                scaffold, "secure_create", side_effect=write_then_report_failure
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "recovery marker"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)

        self.assertEqual(
            (self.tmp / "generated.txt").read_text(encoding="utf-8"),
            "complete-looking\n",
        )
        with mock.patch.object(scaffold, "desired_files", return_value=files):
            with self.assertRaisesRegex(RuntimeError, "recovery marker requires human review"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)

    def test_scaffold_recovery_intent_precedes_destination_and_blocks_completion_failure(self):
        files = {Path("generated.txt"): "generated\n"}
        real_secure_create = scaffold.secure_create
        destinations_attempted = []

        def fail_intent(repo, relative, content, executable, expected_root):
            if relative == scaffold.RECOVERY_RELATIVE:
                raise OSError("injected intent failure")
            destinations_attempted.append(relative)
            return real_secure_create(repo, relative, content, executable, expected_root)

        with (
            mock.patch.object(scaffold, "desired_files", return_value=files),
            mock.patch.object(scaffold, "secure_create", side_effect=fail_intent),
        ):
            with self.assertRaisesRegex(RuntimeError, "apply did not start"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)
        self.assertEqual(destinations_attempted, [])
        self.assertFalse((self.tmp / "generated.txt").exists())

        def fail_completion(repo, relative, content, executable, expected_root):
            if relative == scaffold.RECOVERY_COMPLETE_RELATIVE:
                (repo / scaffold.RECOVERY_RELATIVE).unlink()
                raise OSError("injected completion failure")
            return real_secure_create(repo, relative, content, executable, expected_root)

        with (
            mock.patch.object(scaffold, "desired_files", return_value=files),
            mock.patch.object(scaffold, "secure_create", side_effect=fail_completion),
        ):
            with self.assertRaisesRegex(RuntimeError, "completion was not durably recorded"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)
        self.assertTrue((self.tmp / scaffold.RECOVERY_RELATIVE).is_file())
        self.assertFalse((self.tmp / scaffold.RECOVERY_COMPLETE_RELATIVE).exists())
        with mock.patch.object(scaffold, "desired_files", return_value=files):
            with self.assertRaisesRegex(RuntimeError, "recovery marker requires human review"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)

    def test_scaffold_recovery_rejects_malformed_completed_intent(self):
        files = {Path("generated.txt"): "generated\n"}
        (self.tmp / "generated.txt").write_text("generated\n", encoding="utf-8")
        intent = json.dumps({
            "version": 2,
            "status": "apply-in-progress",
            "planned_create_paths": [None, 7, "../outside", "../outside"],
        }, indent=2, sort_keys=True) + "\n"
        completion = json.dumps({
            "version": 2,
            "status": "apply-complete",
            "intent_sha256": "sha256:" + scaffold.hashlib.sha256(
                intent.encode("utf-8")
            ).hexdigest(),
        }, indent=2, sort_keys=True) + "\n"
        (self.tmp / scaffold.RECOVERY_RELATIVE).write_text(intent, encoding="utf-8")
        (self.tmp / scaffold.RECOVERY_COMPLETE_RELATIVE).write_text(
            completion, encoding="utf-8"
        )
        with mock.patch.object(scaffold, "desired_files", return_value=files):
            with self.assertRaisesRegex(RuntimeError, "recovery marker requires human review"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)

    def test_scaffold_recovery_rejects_duplicate_json_keys(self):
        files = {Path("generated.txt"): "generated\n"}
        (self.tmp / "generated.txt").write_text("generated\n", encoding="utf-8")
        content_hash = "sha256:" + scaffold.hashlib.sha256(
            files[Path("generated.txt")].encode("utf-8")
        ).hexdigest()
        intent = (
            '{"version":2,"status":"apply-in-progress",'
            '"planned_create_paths":["../outside"],'
            '"planned_create_paths":["generated.txt"],'
            '"planned_create_sha256":{"generated.txt":"%s"}}\n'
            % content_hash
        )
        completion = json.dumps({
            "version": 2,
            "status": "apply-complete",
            "intent_sha256": "sha256:" + scaffold.hashlib.sha256(
                intent.encode("utf-8")
            ).hexdigest(),
        }, sort_keys=True) + "\n"
        (self.tmp / scaffold.RECOVERY_RELATIVE).write_text(intent, encoding="utf-8")
        (self.tmp / scaffold.RECOVERY_COMPLETE_RELATIVE).write_text(
            completion, encoding="utf-8"
        )
        with mock.patch.object(scaffold, "desired_files", return_value=files):
            with self.assertRaisesRegex(RuntimeError, "recovery marker requires human review"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)

    @unittest.skipUnless(sys.platform == "win32", "Windows path-alias test")
    def test_scaffold_recovery_rejects_case_alias_destinations(self):
        files = {Path("generated.txt"): "generated\n"}
        (self.tmp / "generated.txt").write_text("generated\n", encoding="utf-8")
        content_hash = "sha256:" + scaffold.hashlib.sha256(
            files[Path("generated.txt")].encode("utf-8")
        ).hexdigest()
        intent = json.dumps({
            "version": 2,
            "status": "apply-in-progress",
            "planned_create_paths": ["generated.txt", "GENERATED.TXT"],
            "planned_create_sha256": {
                "generated.txt": content_hash,
                "GENERATED.TXT": content_hash,
            },
        }, sort_keys=True) + "\n"
        completion = json.dumps({
            "version": 2,
            "status": "apply-complete",
            "intent_sha256": "sha256:" + scaffold.hashlib.sha256(
                intent.encode("utf-8")
            ).hexdigest(),
        }, sort_keys=True) + "\n"
        (self.tmp / scaffold.RECOVERY_RELATIVE).write_text(intent, encoding="utf-8")
        (self.tmp / scaffold.RECOVERY_COMPLETE_RELATIVE).write_text(
            completion, encoding="utf-8"
        )
        with mock.patch.object(scaffold, "desired_files", return_value=files):
            with self.assertRaisesRegex(RuntimeError, "recovery marker requires human review"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)

    def test_scaffold_restores_deleted_intent_after_destination_failure(self):
        files = {Path("generated.txt"): "complete-looking\n"}
        real_secure_create = scaffold.secure_create
        destination_failed = False

        def delete_intent_then_fail(repo, relative, content, executable, expected_root):
            nonlocal destination_failed
            result = real_secure_create(repo, relative, content, executable, expected_root)
            if relative == Path("generated.txt") and not destination_failed:
                destination_failed = True
                (repo / scaffold.RECOVERY_RELATIVE).unlink()
                raise OSError("post-write acknowledgement failed")
            return result

        with (
            mock.patch.object(scaffold, "desired_files", return_value=files),
            mock.patch.object(
                scaffold, "secure_create", side_effect=delete_intent_then_fail
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "retained and reverified"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)
        self.assertTrue((self.tmp / scaffold.RECOVERY_RELATIVE).is_file())
        self.assertFalse((self.tmp / scaffold.RECOVERY_COMPLETE_RELATIVE).exists())
        with mock.patch.object(scaffold, "desired_files", return_value=files):
            with self.assertRaisesRegex(RuntimeError, "recovery marker requires human review"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)

    def test_scaffold_persists_detected_same_byte_intent_replacement(self):
        files = {Path("generated.txt"): "generated\n"}
        real_secure_create = scaffold.secure_create

        def replace_after_completion(repo, relative, content, executable, expected_root):
            result = real_secure_create(
                repo, relative, content, executable, expected_root
            )
            if relative == scaffold.RECOVERY_COMPLETE_RELATIVE:
                intent = repo / scaffold.RECOVERY_RELATIVE
                exact = intent.read_bytes()
                intent.unlink()
                intent.write_bytes(exact)
            return result

        with (
            mock.patch.object(scaffold, "desired_files", return_value=files),
            mock.patch.object(
                scaffold, "secure_create", side_effect=replace_after_completion
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "CUSTODY LOST"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)
        self.assertTrue((self.tmp / scaffold.RECOVERY_FAILURE_RELATIVE).is_file())
        with mock.patch.object(scaffold, "desired_files", return_value=files):
            with self.assertRaisesRegex(RuntimeError, "custody loss requires human review"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)

    def test_scaffold_safety_race_restores_intent_after_prior_write(self):
        files = {
            Path("a/generated.txt"): "first\n",
            Path("b/generated.txt"): "second\n",
        }
        real_safe_destination = scaffold.safe_destination

        def reject_second_and_delete_intent(repo, destination):
            if (
                destination == repo / "b/generated.txt"
                and (repo / "a/generated.txt").exists()
                and (repo / scaffold.RECOVERY_RELATIVE).exists()
            ):
                (repo / scaffold.RECOVERY_RELATIVE).unlink()
                return False
            return real_safe_destination(repo, destination)

        with (
            mock.patch.object(scaffold, "desired_files", return_value=files),
            mock.patch.object(
                scaffold, "safe_destination", side_effect=reject_second_and_delete_intent
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "retained and reverified"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)
        self.assertTrue((self.tmp / "a/generated.txt").is_file())
        self.assertFalse((self.tmp / "b/generated.txt").exists())
        self.assertTrue((self.tmp / scaffold.RECOVERY_RELATIVE).is_file())
        with mock.patch.object(scaffold, "desired_files", return_value=files):
            with self.assertRaisesRegex(RuntimeError, "recovery marker requires human review"):
                scaffold.scaffold(self.tmp, host="generic", apply=True)

    def test_scaffold_cli_requires_real_exact_git_worktree_root(self):
        script = SCRIPTS / "scaffold-guardrail.py"
        fake = subprocess.run(
            [sys.executable, str(script), "--repo", str(self.tmp)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(fake.returncode, 2, fake.stdout + fake.stderr)
        self.assertIn("not a git repository/worktree", fake.stdout)

        external = Path(tempfile.mkdtemp(prefix="guardrail_git_authority_"))
        try:
            external_init = subprocess.run(
                ["git", "init"], cwd=str(external),
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(
                external_init.returncode, 0,
                external_init.stdout + external_init.stderr,
            )
            poisoned_environment = os.environ.copy()
            poisoned_environment.update({
                "GIT_DIR": str(external / ".git"),
                "GIT_WORK_TREE": str(self.tmp),
            })
            poisoned = subprocess.run(
                [sys.executable, str(script), "--repo", str(self.tmp)],
                capture_output=True, text=True, check=False,
                env=poisoned_environment,
            )
            self.assertEqual(poisoned.returncode, 2, poisoned.stdout + poisoned.stderr)
            self.assertIn("not a git repository/worktree", poisoned.stdout)
        finally:
            shutil.rmtree(external, ignore_errors=True)

        shutil.rmtree(self.tmp / ".git")
        initialized = subprocess.run(
            ["git", "init"], cwd=str(self.tmp),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(initialized.returncode, 0, initialized.stdout + initialized.stderr)
        real = subprocess.run(
            [sys.executable, str(script), "--repo", str(self.tmp)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(real.returncode, 0, real.stdout + real.stderr)
        self.assertIn("Preview only", real.stdout)

    def test_scaffold_cli_binds_git_validation_to_same_root_identity(self):
        shutil.rmtree(self.tmp / ".git")
        initialized = subprocess.run(
            ["git", "init"], cwd=str(self.tmp),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(initialized.returncode, 0, initialized.stdout + initialized.stderr)
        original = self.tmp.with_name(self.tmp.name + "_git_verified")
        real_check = scaffold.is_git_worktree_root

        def validate_then_replace(repo):
            self.assertTrue(real_check(repo))
            repo.rename(original)
            repo.mkdir()
            return True

        files = {Path("generated.txt"): "generated\n"}
        try:
            with (
                mock.patch.object(scaffold, "is_git_worktree_root", side_effect=validate_then_replace),
                mock.patch.object(scaffold, "desired_files", return_value=files),
            ):
                result = scaffold.main([
                    "--repo", str(self.tmp), "--host", "generic", "--apply",
                ])
            self.assertEqual(result, 2)
            self.assertFalse((self.tmp / "generated.txt").exists())
            self.assertFalse((original / "generated.txt").exists())
        finally:
            shutil.rmtree(self.tmp, ignore_errors=True)
            if original.exists():
                original.rename(self.tmp)

    def test_scaffold_cli_rejects_transient_root_swap_and_restore(self):
        shutil.rmtree(self.tmp / ".git")
        initialized = subprocess.run(
            ["git", "init"], cwd=str(self.tmp),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(initialized.returncode, 0, initialized.stdout + initialized.stderr)
        moved = self.tmp.with_name(self.tmp.name + "_transient")
        real_check = scaffold.is_git_worktree_root

        def check_during_swap_attempt(repo):
            accepted = real_check(repo)
            try:
                repo.rename(moved)
            except OSError:
                return accepted
            repo.mkdir()
            repo.rmdir()
            moved.rename(repo)
            return accepted

        with mock.patch.object(
            scaffold, "is_git_worktree_root", side_effect=check_during_swap_attempt
        ):
            result = scaffold.main(["--repo", str(self.tmp), "--apply"])
        if os.name == "nt":
            self.assertEqual(result, 0)
        else:
            self.assertEqual(result, 2)
        self.assertFalse(moved.exists())

    @unittest.skipUnless(os.name == "nt" and hasattr(Path, "is_junction"), "Windows junction test")
    def test_watcher_rejects_junction_cursor_ancestor(self):
        outside = Path(tempfile.mkdtemp(prefix="guardrail_junction_outside_"))
        junction = self.tmp / "agent-state"
        try:
            shutil.rmtree(self.tmp / ".git")
            initialized = subprocess.run(
                ["git", "init"], cwd=str(self.tmp),
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(
                initialized.returncode, 0,
                initialized.stdout + initialized.stderr,
            )
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
                capture_output=True, text=True, check=False,
            )
            if result.returncode != 0:
                self.skipTest("junction creation unavailable: %s" % (result.stdout + result.stderr))
            self.assertTrue(junction.is_junction())
            cursor = outside / "architecture-guardrail" / "watch-cursor.json"
            cursor.parent.mkdir(parents=True, exist_ok=True)
            initial = {
                "version": 1,
                "mode": "guardrail-pack",
                "authority_sha256": "",
                "last_complete_scan": "",
                "observed_fingerprints": [],
                "last_result_sha256": "",
                "handoff": None,
            }
            cursor.write_text(json.dumps(initial), encoding="utf-8")
            watcher = REPO / "development" / "arch-drift-watch" / "scripts" / "watch-guardrail-pack.py"
            watched = subprocess.run(
                [sys.executable, str(watcher), "--root", str(self.tmp)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(watched.returncode, 2, watched.stdout + watched.stderr)
            self.assertIn("junctions", watched.stdout)
            self.assertEqual(json.loads(cursor.read_text(encoding="utf-8")), initial)
        finally:
            if junction.is_junction():
                junction.rmdir()
            shutil.rmtree(outside, ignore_errors=True)

    @unittest.skipUnless(os.name == "nt" and hasattr(Path, "is_junction"), "Windows junction test")
    def test_watcher_snapshot_rejects_untracked_junction_ancestor(self):
        outside = Path(tempfile.mkdtemp(prefix="guardrail_snapshot_junction_"))
        junction = self.tmp / "linked"
        try:
            shutil.rmtree(self.tmp / ".git")
            (self.tmp / "tracked.txt").write_text("tracked\n", encoding="utf-8")
            for command in (
                ["git", "init"],
                ["git", "config", "user.email", "guardrail-test@example.invalid"],
                ["git", "config", "user.name", "Guardrail Test"],
                ["git", "add", "tracked.txt"],
                ["git", "commit", "-m", "test fixture"],
            ):
                result = subprocess.run(
                    command, cwd=str(self.tmp), capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            (outside / "outside.txt").write_text("outside\n", encoding="utf-8")
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
                capture_output=True, text=True, check=False,
            )
            if result.returncode != 0:
                self.skipTest("junction creation unavailable: %s" % (result.stdout + result.stderr))
            self.assertTrue(junction.is_junction())

            untracked = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=str(self.tmp), capture_output=True, text=True, check=False,
            )
            self.assertEqual(untracked.returncode, 0, untracked.stdout + untracked.stderr)
            self.assertIn("linked/outside.txt", untracked.stdout.replace("\\", "/"))

            watcher_path = (
                REPO / "development" / "arch-drift-watch" / "scripts" /
                "watch-guardrail-pack.py"
            )
            spec = importlib.util.spec_from_file_location(
                "guardrail_watch_snapshot_junction", watcher_path
            )
            watcher = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(watcher)

            snapshot, error = watcher.repository_snapshot(self.tmp)
            self.assertIsNone(snapshot)
            self.assertIsNotNone(error)
            self.assertIn("working-tree snapshot", error)
            self.assertTrue(error.replace("\\", "/").endswith(": linked"), error)
        finally:
            if junction.is_junction():
                junction.rmdir()
            shutil.rmtree(outside, ignore_errors=True)

    def test_watcher_snapshot_hashes_git_ignored_file_bytes(self):
        shutil.rmtree(self.tmp / ".git")
        (self.tmp / ".gitignore").write_text("runtime-state/\n", encoding="utf-8")
        for command in (
            ["git", "init"],
            ["git", "config", "user.email", "guardrail-test@example.invalid"],
            ["git", "config", "user.name", "Guardrail Test"],
            ["git", "add", ".gitignore"],
            ["git", "commit", "-m", "test fixture"],
        ):
            result = subprocess.run(
                command, cwd=str(self.tmp), capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        ignored = self.tmp / "runtime-state" / "state.json"
        ignored.parent.mkdir()
        ignored.write_text('{"violating": false}\n', encoding="utf-8")
        status = subprocess.run(
            ["git", "status", "--porcelain=v1"], cwd=str(self.tmp),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
        self.assertEqual(status.stdout, "")

        watcher_path = (
            REPO / "development" / "arch-drift-watch" / "scripts" /
            "watch-guardrail-pack.py"
        )
        spec = importlib.util.spec_from_file_location(
            "guardrail_watch_snapshot_ignored", watcher_path
        )
        watcher = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(watcher)

        before, before_error = watcher.repository_snapshot(self.tmp)
        self.assertIsNone(before_error)
        ignored.write_text('{"violating": true}\n', encoding="utf-8")
        after, after_error = watcher.repository_snapshot(self.tmp)
        self.assertIsNone(after_error)
        self.assertNotEqual(before, after)

    def test_watcher_snapshot_hashes_assume_unchanged_tracked_bytes(self):
        shutil.rmtree(self.tmp / ".git")
        tracked = self.tmp / "tracked.txt"
        tracked.write_text("before\n", encoding="utf-8")
        for command in (
            ["git", "init"],
            ["git", "config", "user.email", "guardrail-test@example.invalid"],
            ["git", "config", "user.name", "Guardrail Test"],
            ["git", "add", "tracked.txt"],
            ["git", "commit", "-m", "test fixture"],
            ["git", "update-index", "--assume-unchanged", "tracked.txt"],
        ):
            result = subprocess.run(
                command, cwd=str(self.tmp), capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        watcher_path = (
            REPO / "development" / "arch-drift-watch" / "scripts" /
            "watch-guardrail-pack.py"
        )
        spec = importlib.util.spec_from_file_location(
            "guardrail_watch_snapshot_assume_unchanged", watcher_path
        )
        watcher = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(watcher)

        before, before_error = watcher.repository_snapshot(self.tmp)
        self.assertIsNone(before_error)
        tracked.write_text("after\n", encoding="utf-8")
        status = subprocess.run(
            ["git", "status", "--porcelain=v1"], cwd=str(self.tmp),
            capture_output=True, text=True, check=False,
        )
        diff = subprocess.run(
            ["git", "diff", "--", "tracked.txt"], cwd=str(self.tmp),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(status.stdout, "")
        self.assertEqual(diff.stdout, "")
        after, after_error = watcher.repository_snapshot(self.tmp)
        self.assertIsNone(after_error)
        self.assertNotEqual(before, after)

    def test_watcher_sanitizes_git_authority_and_requires_exact_root(self):
        shutil.rmtree(self.tmp / ".git")
        initialized = subprocess.run(
            ["git", "init"], cwd=str(self.tmp),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(
            initialized.returncode, 0, initialized.stdout + initialized.stderr
        )
        decoy = Path(tempfile.mkdtemp(prefix="guardrail_watch_git_decoy_"))
        try:
            decoy_init = subprocess.run(
                ["git", "init"], cwd=str(decoy),
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(
                decoy_init.returncode, 0, decoy_init.stdout + decoy_init.stderr
            )
            watcher_path = (
                REPO / "development" / "arch-drift-watch" / "scripts" /
                "watch-guardrail-pack.py"
            )
            spec = importlib.util.spec_from_file_location(
                "guardrail_watch_git_authority", watcher_path
            )
            watcher = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(watcher)
            poisoned = {
                "GIT_DIR": str(decoy / ".git"),
                "GIT_WORK_TREE": str(self.tmp),
            }
            with mock.patch.dict(os.environ, poisoned, clear=False):
                self.assertTrue(watcher.is_git_worktree_root(self.tmp))
                git_dir = watcher.run(["git", "rev-parse", "--git-dir"], self.tmp)
            self.assertFalse(isinstance(git_dir, tuple))
            self.assertEqual(
                (self.tmp / git_dir.stdout.decode("utf-8").strip()).resolve(),
                (self.tmp / ".git").resolve(),
            )
            nested = self.tmp / "nested"
            nested.mkdir()
            self.assertFalse(watcher.is_git_worktree_root(nested))
        finally:
            shutil.rmtree(decoy, ignore_errors=True)

    def test_watcher_compares_raw_committed_bytes_without_clean_filters(self):
        watcher_path = (
            REPO / "development" / "arch-drift-watch" / "scripts" /
            "watch-guardrail-pack.py"
        )
        spec = importlib.util.spec_from_file_location(
            "guardrail_watch_raw_commitment", watcher_path
        )
        watcher = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(watcher)
        hook = self.tmp / ".githooks" / "pre-commit"
        hook.parent.mkdir()
        hook.write_bytes(b"weakened working bytes\n")
        head = subprocess.CompletedProcess(
            ["git", "show"], 0, stdout=b"committed bytes\n", stderr=b""
        )
        with mock.patch.object(watcher, "run", return_value=head):
            self.assertFalse(
                watcher.committed_file_matches(self.tmp, ".githooks/pre-commit")
            )
            hook.write_bytes(b"committed bytes\n")
            self.assertTrue(
                watcher.committed_file_matches(self.tmp, ".githooks/pre-commit")
            )

    def test_policy_rejects_symlinked_evidence_and_fixture_paths(self):
        outside = Path(tempfile.mkdtemp(prefix="guardrail_policy_outside_"))
        try:
            policy = self.good_policy()
            outside_file = outside / "evidence.py"
            outside_file.write_text("outside\n", encoding="utf-8")
            outside_fixture = outside / "fixture"
            outside_fixture.mkdir()
            try:
                os.symlink(str(outside_file), str(self.tmp / "src" / "linked.py"))
                fixture_link = self.tmp / "scripts" / "architecture" / "fixtures" / "linked"
                fixture_link.parent.mkdir(parents=True, exist_ok=True)
                os.symlink(str(outside_fixture), str(fixture_link), target_is_directory=True)
            except OSError as exc:
                self.skipTest("symlink unavailable: %s" % exc)
            policy["rules"][0]["evidence"][0]["locator"] = "src/linked.py"
            policy["rules"][0]["validator"]["fixtures"]["positive"] = [
                "scripts/architecture/fixtures/linked"
            ]
            decisions, verification = self.approvals_for(policy)
            errors = validate.validate_pack(
                self.tmp, policy,
                {"version": 1, "source_commit": "", "entries": []},
                {"version": 1, "exceptions": []}, decisions, verification,
            )
            self.assertTrue(any("symlinked" in error for error in errors), errors)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_rejects_broad_symbol_whitespace_identities_and_duplicate_json(self):
        self.assertFalse(validate.exact_symbol("*"))
        policy_for_exception = self.good_policy()
        exception_errors = []
        validate.validate_exceptions({
            "version": 1,
            "exceptions": [{
                "id": "EXC-001",
                "rule_id": "TENANCY-001",
                "target": {
                    "path": "src/tenant.py",
                    "fingerprint": "sha256:" + "a" * 64,
                },
                "reason": "Temporary exact waiver.",
                "owner": "architecture-owner",
                "decision_id": "ARCH-003",
                "approved_by": "owner",
                "approved_at": "2026-08-29T19:00:00Z",
                "removal_condition": "Migration completes.",
            }],
        }, {"TENANCY-001": policy_for_exception["rules"][0]}, self.tmp, exception_errors)
        self.assertTrue(any("required exact symbol" in error for error in exception_errors), exception_errors)
        policy = self.good_policy()
        decisions, verification = self.approvals_for(policy)
        verification["records"][0].update({
            "maker": "same-agent",
            "breaker": "same-agent ",
            "verifier": "same-agent  ",
        })
        errors = validate.validate_pack(
            self.tmp, policy,
            {"version": 1, "source_commit": "", "entries": []},
            {"version": 1, "exceptions": []}, decisions, verification,
        )
        self.assertTrue(any("canonical actor IDs" in error for error in errors), errors)
        duplicate = self.tmp / "duplicate.json"
        duplicate.write_text('{"version":1,"version":2}\n', encoding="utf-8")
        _data, error = validate.load_data(duplicate)
        self.assertIn("duplicate mapping key", error)

    def test_empty_pack_is_policy_valid_but_not_enforcement_green(self):
        scaffold.scaffold(self.tmp, host="generic", apply=True)
        verifier = self.tmp / "scripts" / "architecture" / "verify.py"
        normal = subprocess.run(
            [sys.executable, str(verifier)], cwd=str(self.tmp),
            capture_output=True, text=True, check=False,
        )
        policy_only = subprocess.run(
            [sys.executable, str(verifier), "--policy-only"], cwd=str(self.tmp),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(normal.returncode, 2, normal.stdout + normal.stderr)
        self.assertIn("no enforced architecture rules", normal.stdout)
        self.assertEqual(policy_only.returncode, 0, policy_only.stdout + policy_only.stderr)

    def test_canonical_verifier_detects_validator_authority_mutation(self):
        scaffold.scaffold(self.tmp, host="generic", apply=True)
        validator_path = self.tmp / self.validator_rel
        validator_path.parent.mkdir(parents=True, exist_ok=True)
        validator_path.write_text(
            "import argparse, json, pathlib, sys\n"
            "p=argparse.ArgumentParser(); p.add_argument('--root'); a=p.parse_args()\n"
            "pack=pathlib.Path.cwd()/'.architecture'/'baseline.json'\n"
            "data=json.loads(pack.read_text()); data['mutated']=True; pack.write_text(json.dumps(data))\n"
            "bad=(pathlib.Path(a.root)/'violation.txt').exists()\n"
            "f='sha256:'+'a'*64\n"
            "print(json.dumps({'schema':'guardrail-findings-v1','rule_id':'TENANCY-001','complete':True,'findings':([{'rule_id':'TENANCY-001','fingerprint':f,'path':'violation.txt','message':'bad'}] if bad else [])}))\n"
            "sys.exit(1 if bad else 0)\n",
            encoding="utf-8",
        )
        policy = self.good_policy()
        policy["rules"][0]["validator"]["command"] = [
            sys.executable, self.validator_rel, "--root", "{fixture}"
        ]
        negative = self.tmp / "scripts" / "architecture" / "fixtures" / "TENANCY-001" / "invalid"
        (negative / "violation.txt").write_text("bad\n", encoding="utf-8")
        positive = self.tmp / "scripts" / "architecture" / "fixtures" / "TENANCY-001" / "valid"
        (positive / "valid.txt").write_text("valid\n", encoding="utf-8")
        decisions, verification = self.approvals_for(policy)
        for relative, value in (
            (".architecture/policy.yaml", policy),
            (".architecture/decisions.json", decisions),
            (".architecture/verification.json", verification),
        ):
            (self.tmp / relative).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(self.tmp / "scripts" / "architecture" / "verify.py")],
            cwd=str(self.tmp), capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("authority changed during verification", result.stdout)

    def test_generated_canonical_verifier_runs_positive_negative_and_repo(self):
        scaffold.scaffold(self.tmp, host="generic", apply=True)
        validator_path = self.tmp / self.validator_rel
        validator_path.parent.mkdir(parents=True, exist_ok=True)
        validator_path.write_text(
            "import argparse, hashlib, json, pathlib, sys\n"
            "p=argparse.ArgumentParser(); p.add_argument('--root'); a=p.parse_args()\n"
            "bad=(pathlib.Path(a.root)/'violation.txt').exists()\n"
            "f='sha256:'+hashlib.sha256(b'violation').hexdigest()\n"
            "d={'schema':'guardrail-findings-v1','rule_id':'TENANCY-001','complete':True,'findings':([{'rule_id':'TENANCY-001','fingerprint':f,'path':'violation.txt','message':'direct access'}] if bad else [])}\n"
            "print(json.dumps(d)); sys.exit(1 if bad else 0)\n",
            encoding="utf-8",
        )
        policy = self.good_policy()
        policy["rules"][0]["validator"]["command"] = [
            sys.executable, self.validator_rel, "--root", "{fixture}"
        ]
        negative = self.tmp / "scripts" / "architecture" / "fixtures" / "TENANCY-001" / "invalid"
        (negative / "violation.txt").write_text("bad\n", encoding="utf-8")
        positive = self.tmp / "scripts" / "architecture" / "fixtures" / "TENANCY-001" / "valid"
        (positive / "valid.txt").write_text("valid\n", encoding="utf-8")
        (self.tmp / ".architecture" / "policy.yaml").write_text(
            json.dumps(policy, indent=2) + "\n", encoding="utf-8"
        )
        decisions, verification = self.approvals_for(policy)
        (self.tmp / ".architecture" / "decisions.json").write_text(
            json.dumps(decisions, indent=2) + "\n", encoding="utf-8"
        )
        (self.tmp / ".architecture" / "verification.json").write_text(
            json.dumps(verification, indent=2) + "\n", encoding="utf-8"
        )
        result = subprocess.run(
            [sys.executable, str(self.tmp / "scripts" / "architecture" / "verify.py")],
            cwd=str(self.tmp), capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1 enforced rule(s)", result.stdout)
        watch = subprocess.run(
            [
                sys.executable,
                str(self.tmp / "scripts" / "architecture" / "verify.py"),
                "--repo-only", "--format", "json",
            ],
            cwd=str(self.tmp), capture_output=True, text=True, check=False,
        )
        self.assertEqual(watch.returncode, 0, watch.stdout + watch.stderr)
        envelope = json.loads(watch.stdout)
        self.assertEqual(envelope["schema"], "guardrail-verification-v1")
        self.assertTrue(envelope["complete"])
        self.assertEqual(envelope["rules_run"], 1)
        self.assertTrue(envelope["authority_sha256"].startswith("sha256:"))
        self.assertEqual(envelope["findings"], [])

        (self.tmp / "violation.txt").write_text("bad\n", encoding="utf-8")
        drift = subprocess.run(
            [
                sys.executable,
                str(self.tmp / "scripts" / "architecture" / "verify.py"),
                "--repo-only", "--format", "json",
            ],
            cwd=str(self.tmp), capture_output=True, text=True, check=False,
        )
        self.assertEqual(drift.returncode, 1, drift.stdout + drift.stderr)
        drift_envelope = json.loads(drift.stdout)
        self.assertTrue(drift_envelope["complete"])
        self.assertEqual(drift_envelope["status"], "violation")
        self.assertEqual(len(drift_envelope["findings"]), 1)

        validator_path.write_text("print('not-json')\n", encoding="utf-8")
        malformed = subprocess.run(
            [
                sys.executable,
                str(self.tmp / "scripts" / "architecture" / "verify.py"),
                "--repo-only", "--format", "json",
            ],
            cwd=str(self.tmp), capture_output=True, text=True, check=False,
        )
        self.assertEqual(malformed.returncode, 2, malformed.stdout + malformed.stderr)
        malformed_envelope = json.loads(malformed.stdout)
        self.assertFalse(malformed_envelope["complete"])
        self.assertEqual(malformed_envelope["status"], "config-error")
        self.assertTrue(malformed_envelope["errors"])

    def test_canonical_verifier_applies_only_exact_approved_baseline_fingerprint(self):
        scaffold.scaffold(self.tmp, host="generic", apply=True)
        validator_path = self.tmp / self.validator_rel
        validator_path.parent.mkdir(parents=True, exist_ok=True)
        fingerprint = "sha256:" + "a" * 64
        validator_path.write_text(
            "import argparse, json, pathlib, sys\n"
            "p=argparse.ArgumentParser(); p.add_argument('--root'); a=p.parse_args()\n"
            "bad=(pathlib.Path(a.root)/'violation.txt').exists()\n"
            "d={'schema':'guardrail-findings-v1','rule_id':'TENANCY-001','complete':True,'findings':([{'rule_id':'TENANCY-001','fingerprint':'%s','path':'violation.txt','message':'direct access'}] if bad else [])}\n"
            "print(json.dumps(d)); sys.exit(1 if bad else 0)\n" % fingerprint,
            encoding="utf-8",
        )
        policy = self.good_policy()
        policy["rules"][0]["validator"]["command"] = [
            sys.executable, self.validator_rel, "--root", "{fixture}"
        ]
        negative = self.tmp / "scripts" / "architecture" / "fixtures" / "TENANCY-001" / "invalid"
        (negative / "violation.txt").write_text("bad\n", encoding="utf-8")
        (self.tmp / "violation.txt").write_text("legacy\n", encoding="utf-8")
        baseline_entry = {
            "fingerprint": fingerprint,
            "rule_id": "TENANCY-001",
            "path": "violation.txt",
            "reason": "Approved legacy debt.",
            "decision_id": "ARCH-002",
            "approved_by": "owner",
            "approved_at": "2026-08-29T19:30:00Z",
        }
        baseline = {
            "version": 1,
            "source_commit": "0123456789abcdef",
            "entries": [baseline_entry],
        }
        decisions, verification = self.approvals_for(policy)
        decisions["decisions"].append({
            "id": "ARCH-002",
            "status": "approved",
            "subject_type": "baseline",
            "subject_id": fingerprint,
            "subject_sha256": validate.canonical_sha256(
                validate.baseline_contract(baseline_entry)
            ),
            "approved_by": "owner",
            "approved_at": "2026-08-29T19:30:00Z",
        })
        for relative, value in (
            (".architecture/policy.yaml", policy),
            (".architecture/baseline.json", baseline),
            (".architecture/decisions.json", decisions),
            (".architecture/verification.json", verification),
        ):
            (self.tmp / relative).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(self.tmp / "scripts" / "architecture" / "verify.py")],
            cwd=str(self.tmp), capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        baseline["entries"][0]["fingerprint"] = "sha256:" + "b" * 64
        decisions["decisions"][1]["subject_id"] = baseline["entries"][0]["fingerprint"]
        decisions["decisions"][1]["subject_sha256"] = validate.canonical_sha256(
            validate.baseline_contract(baseline["entries"][0])
        )
        (self.tmp / ".architecture" / "baseline.json").write_text(
            json.dumps(baseline, indent=2) + "\n", encoding="utf-8"
        )
        (self.tmp / ".architecture" / "decisions.json").write_text(
            json.dumps(decisions, indent=2) + "\n", encoding="utf-8"
        )
        mismatch = subprocess.run(
            [sys.executable, str(self.tmp / "scripts" / "architecture" / "verify.py")],
            cwd=str(self.tmp), capture_output=True, text=True, check=False,
        )
        self.assertEqual(mismatch.returncode, 1, mismatch.stdout + mismatch.stderr)
        self.assertIn("Architecture verification failed", mismatch.stdout)

    def test_watcher_requires_approved_init_classifies_and_never_greens_tampering(self):
        scaffold.scaffold(self.tmp, host="generic", apply=True)
        validator_path = self.tmp / self.validator_rel
        validator_path.parent.mkdir(parents=True, exist_ok=True)
        validator_path.write_text(
            "import argparse, hashlib, json, pathlib, sys\n"
            "p=argparse.ArgumentParser(); p.add_argument('--root'); a=p.parse_args()\n"
            "bad=(pathlib.Path(a.root)/'violation.txt').exists()\n"
            "f='sha256:'+hashlib.sha256(b'violation').hexdigest()\n"
            "d={'schema':'guardrail-findings-v1','rule_id':'TENANCY-001','complete':True,'findings':([{'rule_id':'TENANCY-001','fingerprint':f,'path':'violation.txt','message':'direct access'}] if bad else [])}\n"
            "print(json.dumps(d)); sys.exit(1 if bad else 0)\n",
            encoding="utf-8",
        )
        policy = self.good_policy()
        policy["rules"][0]["validator"]["command"] = [
            sys.executable, self.validator_rel, "--root", "{fixture}"
        ]
        negative = self.tmp / "scripts" / "architecture" / "fixtures" / "TENANCY-001" / "invalid"
        (negative / "violation.txt").write_text("bad\n", encoding="utf-8")
        positive = self.tmp / "scripts" / "architecture" / "fixtures" / "TENANCY-001" / "valid"
        (positive / "valid.txt").write_text("valid\n", encoding="utf-8")
        (self.tmp / ".architecture" / "policy.yaml").write_text(
            json.dumps(policy, indent=2) + "\n", encoding="utf-8"
        )
        decisions, verification = self.approvals_for(policy)
        (self.tmp / ".architecture" / "decisions.json").write_text(
            json.dumps(decisions, indent=2) + "\n", encoding="utf-8"
        )
        (self.tmp / ".architecture" / "verification.json").write_text(
            json.dumps(verification, indent=2) + "\n", encoding="utf-8"
        )

        shutil.rmtree(self.tmp / ".git")
        for command in (
            ["git", "init"],
            ["git", "config", "user.email", "guardrail-test@example.invalid"],
            ["git", "config", "user.name", "Guardrail Test"],
            ["git", "add", "."],
            ["git", "commit", "-m", "test fixture"],
        ):
            result = subprocess.run(command, cwd=str(self.tmp), capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        watcher = self.tmp / "scripts" / "architecture" / "watch_guardrail.py"
        cursor = self.tmp / "agent-state" / "architecture-guardrail" / "watch-cursor.json"
        before = cursor.read_bytes()
        arbitrary_cursor = subprocess.run(
            [sys.executable, str(watcher), "--cursor", "cursor.json"], cwd=str(self.tmp),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(arbitrary_cursor.returncode, 2, arbitrary_cursor.stdout + arbitrary_cursor.stderr)
        self.assertIn("dedicated operational state file", arbitrary_cursor.stdout)
        blocked = subprocess.run(
            [sys.executable, str(watcher)], cwd=str(self.tmp),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(blocked.returncode, 2, blocked.stdout + blocked.stderr)
        self.assertEqual(cursor.read_bytes(), before)
        authority = json.loads(blocked.stdout)["authority_sha256"]

        fabricated = subprocess.run(
            [
                sys.executable, str(watcher), "--initialize",
                "--decision-id", "WATCH-001", "--approved-by", "owner",
            ],
            cwd=str(self.tmp), capture_output=True, text=True, check=False,
        )
        self.assertEqual(fabricated.returncode, 2, fabricated.stdout + fabricated.stderr)
        self.assertEqual(cursor.read_bytes(), before)

        decisions["decisions"].append({
            "id": "WATCH-001",
            "status": "approved",
            "subject_type": "watch-handoff",
            "subject_id": "guardrail-pack",
            "subject_sha256": authority,
            "approved_by": "owner",
            "approved_at": "2026-08-29T21:00:00Z",
        })
        (self.tmp / ".architecture" / "decisions.json").write_text(
            json.dumps(decisions, indent=2) + "\n", encoding="utf-8"
        )

        uncommitted_handoff = subprocess.run(
            [
                sys.executable, str(watcher), "--initialize",
                "--decision-id", "WATCH-001", "--approved-by", "owner",
            ],
            cwd=str(self.tmp), capture_output=True, text=True, check=False,
        )
        self.assertEqual(
            uncommitted_handoff.returncode, 2,
            uncommitted_handoff.stdout + uncommitted_handoff.stderr,
        )
        self.assertEqual(cursor.read_bytes(), before)
        for command in (
            ["git", "add", ".architecture/decisions.json"],
            ["git", "commit", "-m", "approve watch handoff"],
        ):
            result = subprocess.run(command, cwd=str(self.tmp), capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        verification_path = self.tmp / ".architecture" / "verification.json"
        verification_path.write_text(
            json.dumps(verification, indent=2) + "\n\n", encoding="utf-8"
        )
        uncommitted_pack = subprocess.run(
            [
                sys.executable, str(watcher), "--initialize",
                "--decision-id", "WATCH-001", "--approved-by", "owner",
            ],
            cwd=str(self.tmp), capture_output=True, text=True, check=False,
        )
        self.assertEqual(uncommitted_pack.returncode, 2, uncommitted_pack.stdout + uncommitted_pack.stderr)
        self.assertIn("does not match committed HEAD", uncommitted_pack.stdout)
        self.assertEqual(cursor.read_bytes(), before)
        assume_result = subprocess.run(
            ["git", "update-index", "--assume-unchanged", ".architecture/verification.json"],
            cwd=str(self.tmp), capture_output=True, text=True, check=False,
        )
        self.assertEqual(assume_result.returncode, 0, assume_result.stdout + assume_result.stderr)
        hidden_uncommitted_pack = subprocess.run(
            [
                sys.executable, str(watcher), "--initialize",
                "--decision-id", "WATCH-001", "--approved-by", "owner",
            ],
            cwd=str(self.tmp), capture_output=True, text=True, check=False,
        )
        self.assertEqual(
            hidden_uncommitted_pack.returncode, 2,
            hidden_uncommitted_pack.stdout + hidden_uncommitted_pack.stderr,
        )
        self.assertIn("does not match committed HEAD", hidden_uncommitted_pack.stdout)
        clear_assume = subprocess.run(
            ["git", "update-index", "--no-assume-unchanged", ".architecture/verification.json"],
            cwd=str(self.tmp), capture_output=True, text=True, check=False,
        )
        self.assertEqual(clear_assume.returncode, 0, clear_assume.stdout + clear_assume.stderr)
        verification_path.write_text(
            json.dumps(verification, indent=2) + "\n", encoding="utf-8"
        )

        initialized = subprocess.run(
            [
                sys.executable, str(watcher), "--initialize",
                "--decision-id", "WATCH-001", "--approved-by", "owner",
            ],
            cwd=str(self.tmp), capture_output=True, text=True, check=False,
        )
        self.assertEqual(initialized.returncode, 0, initialized.stdout + initialized.stderr)
        self.assertTrue(json.loads(initialized.stdout)["complete"])

        workflow = self.tmp / ".github" / "workflows" / "architecture-guardrail.yml"
        workflow_bytes = workflow.read_bytes()
        workflow.unlink()
        for command in (
            ["git", "add", "-A", ".github/workflows/architecture-guardrail.yml"],
            ["git", "commit", "-m", "remove architecture gate"],
        ):
            result = subprocess.run(command, cwd=str(self.tmp), capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        missing_workflow = subprocess.run(
            [sys.executable, str(watcher)], cwd=str(self.tmp),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(missing_workflow.returncode, 2, missing_workflow.stdout + missing_workflow.stderr)
        self.assertFalse(json.loads(missing_workflow.stdout)["complete"])
        workflow.parent.mkdir(parents=True, exist_ok=True)
        workflow.write_bytes(workflow_bytes)
        for command in (
            ["git", "add", ".github/workflows/architecture-guardrail.yml"],
            ["git", "commit", "-m", "restore architecture gate"],
        ):
            result = subprocess.run(command, cwd=str(self.tmp), capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        hook = self.tmp / ".githooks" / "pre-commit"
        hook_bytes = hook.read_bytes()
        hook.write_bytes(hook_bytes + b"\n# weakened wrapper\n")
        for command in (
            ["git", "add", ".githooks/pre-commit"],
            ["git", "commit", "-m", "change architecture hook"],
        ):
            result = subprocess.run(command, cwd=str(self.tmp), capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        changed_hook = subprocess.run(
            [sys.executable, str(watcher)], cwd=str(self.tmp),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(changed_hook.returncode, 2, changed_hook.stdout + changed_hook.stderr)
        self.assertIn("authority", changed_hook.stdout)
        hook.write_bytes(hook_bytes)
        for command in (
            ["git", "add", ".githooks/pre-commit"],
            ["git", "commit", "-m", "restore architecture hook"],
        ):
            result = subprocess.run(command, cwd=str(self.tmp), capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        (self.tmp / "violation.txt").write_text("bad\n", encoding="utf-8")
        drift = subprocess.run(
            [sys.executable, str(watcher)], cwd=str(self.tmp),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(drift.returncode, 1, drift.stdout + drift.stderr)
        self.assertEqual(json.loads(drift.stdout)["findings"][0]["state"], "new")
        persisting = subprocess.run(
            [sys.executable, str(watcher)], cwd=str(self.tmp),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(persisting.returncode, 1, persisting.stdout + persisting.stderr)
        self.assertEqual(json.loads(persisting.stdout)["findings"][0]["state"], "persisting")

        cursor_before_tamper = cursor.read_bytes()
        validator_path.write_text("print('not-json')\n", encoding="utf-8")
        tampered = subprocess.run(
            [sys.executable, str(watcher)], cwd=str(self.tmp),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(tampered.returncode, 2, tampered.stdout + tampered.stderr)
        self.assertFalse(json.loads(tampered.stdout)["complete"])
        self.assertEqual(cursor.read_bytes(), cursor_before_tamper)

    def test_watcher_rejects_upstream_errors_and_boolean_rule_counts(self):
        watcher_path = REPO / "development" / "arch-drift-watch" / "scripts" / "watch-guardrail-pack.py"
        spec = importlib.util.spec_from_file_location("guardrail_watch_adapter", watcher_path)
        watcher = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(watcher)
        envelope = {
            "schema": "guardrail-verification-v1",
            "complete": True,
            "status": "pass",
            "rules_run": True,
            "authority_sha256": "sha256:" + "a" * 64,
            "findings": [],
            "errors": ["scan failed but claimed complete"],
        }
        errors = watcher.validate_verifier_envelope(envelope, 0)
        self.assertTrue(any("at least one" in error for error in errors), errors)
        self.assertTrue(any("empty errors" in error for error in errors), errors)

    def test_watcher_rolls_back_if_cursor_write_changes_verification(self):
        watcher_path = REPO / "development" / "arch-drift-watch" / "scripts" / "watch-guardrail-pack.py"
        spec = importlib.util.spec_from_file_location("guardrail_watch_cursor_canary", watcher_path)
        watcher = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(watcher)
        shutil.rmtree(self.tmp / ".git")
        initialized = subprocess.run(
            ["git", "init"], cwd=str(self.tmp),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(
            initialized.returncode, 0, initialized.stdout + initialized.stderr
        )
        cursor_path = self.tmp / "agent-state" / "architecture-guardrail" / "watch-cursor.json"
        cursor_path.parent.mkdir(parents=True, exist_ok=True)
        initial_cursor = {
            "version": 1,
            "mode": "guardrail-pack",
            "authority_sha256": "",
            "last_complete_scan": "",
            "observed_fingerprints": [],
            "last_result_sha256": "",
            "handoff": None,
        }
        initial_bytes = (" {\n" + "  \"mode\": \"guardrail-pack\",\n"
                         + "  \"version\": 1,\n"
                         + "  \"authority_sha256\": \"\",\n"
                         + "  \"last_complete_scan\": \"\",\n"
                         + "  \"observed_fingerprints\": [],\n"
                         + "  \"last_result_sha256\": \"\",\n"
                         + "  \"handoff\": null\n}\n").encode("utf-8")
        cursor_path.write_bytes(initial_bytes)
        clean_scan = {
            "schema": "guardrail-verification-v1",
            "complete": True,
            "status": "pass",
            "rules_run": 1,
            "authority_sha256": "sha256:" + "a" * 64,
            "findings": [],
            "errors": [],
        }
        changed_scan = dict(clean_scan, status="violation", findings=[{
            "rule_id": "STATE-001",
            "fingerprint": "sha256:" + "c" * 64,
            "path": "agent-state/architecture-guardrail/watch-cursor.json",
            "message": "cursor introduced drift",
            "kind": "state-boundary",
            "owner": "architecture-owner",
            "remediation": "Exclude operational state.",
        }])
        handoff = {
            "id": "WATCH-001",
            "approved_by": "owner",
            "approved_at": "2026-08-29T21:00:00Z",
        }
        with (
            mock.patch.object(watcher, "stable_scan", side_effect=[(clean_scan, None), (changed_scan, None)]),
            mock.patch.object(watcher, "effective_authority", return_value=("sha256:" + "b" * 64, None)),
            mock.patch.object(watcher, "approved_handoff", return_value=(handoff, None)),
            mock.patch.object(watcher, "committed_authority_error", return_value=None),
            mock.patch("builtins.print"),
        ):
            code = watcher.main([
                "--root", str(self.tmp), "--initialize",
                "--decision-id", "WATCH-001", "--approved-by", "owner",
            ])
        self.assertEqual(code, 2)
        self.assertEqual(cursor_path.read_bytes(), initial_bytes)

        real_atomic_write_json = watcher.atomic_write_json

        def replace_cursor_after_write(path, value):
            result = real_atomic_write_json(path, value)
            path.write_bytes(b"CONCURRENT INVALID CURSOR\n")
            return result

        with (
            mock.patch.object(
                watcher, "stable_scan", return_value=(clean_scan, None)
            ),
            mock.patch.object(
                watcher, "effective_authority",
                return_value=("sha256:" + "b" * 64, None),
            ),
            mock.patch.object(
                watcher, "approved_handoff", return_value=(handoff, None)
            ),
            mock.patch.object(
                watcher, "committed_authority_error", return_value=None
            ),
            mock.patch.object(
                watcher, "atomic_write_json", side_effect=replace_cursor_after_write
            ),
            mock.patch("builtins.print"),
        ):
            code = watcher.main([
                "--root", str(self.tmp), "--initialize",
                "--decision-id", "WATCH-001", "--approved-by", "owner",
            ])
        self.assertEqual(code, 2)
        self.assertEqual(cursor_path.read_bytes(), b"CONCURRENT INVALID CURSOR\n")

        cursor_path.write_bytes(initial_bytes)

        with (
            mock.patch.object(
                watcher, "stable_scan", return_value=(clean_scan, None)
            ),
            mock.patch.object(
                watcher, "effective_authority",
                side_effect=[
                    ("sha256:" + "b" * 64, None),
                    ("sha256:" + "d" * 64, None),
                ],
            ),
            mock.patch.object(
                watcher, "approved_handoff", return_value=(handoff, None)
            ),
            mock.patch.object(
                watcher, "committed_authority_error", return_value=None
            ),
            mock.patch("builtins.print"),
        ):
            code = watcher.main([
                "--root", str(self.tmp), "--initialize",
                "--decision-id", "WATCH-001", "--approved-by", "owner",
            ])
        self.assertEqual(code, 2)
        self.assertEqual(cursor_path.read_bytes(), initial_bytes)

    def test_canonical_parser_rejects_duplicate_finding_fingerprints(self):
        verifier_path = SKILL / "assets" / "guardrail-pack" / "scripts" / "architecture" / "verify.py"
        previous = sys.modules.get("validate_policy")
        sys.modules["validate_policy"] = validate
        try:
            spec = importlib.util.spec_from_file_location("guardrail_canonical_verify", verifier_path)
            verifier = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(verifier)
        finally:
            if previous is None:
                del sys.modules["validate_policy"]
            else:
                sys.modules["validate_policy"] = previous
        (self.tmp / "violation.txt").write_text("bad\n", encoding="utf-8")
        fingerprint = "sha256:" + "a" * 64
        finding = {
            "rule_id": "TENANCY-001",
            "fingerprint": fingerprint,
            "path": "violation.txt",
            "message": "duplicate occurrence",
        }
        stdout = json.dumps({
            "schema": "guardrail-findings-v1",
            "rule_id": "TENANCY-001",
            "complete": True,
            "findings": [finding, dict(finding)],
        })
        _findings, error = verifier.parse_findings(stdout, "TENANCY-001", self.tmp)
        self.assertIn("duplicates fingerprint", error)

        stdout = json.dumps({
            "schema": "guardrail-findings-v1",
            "rule_id": "TENANCY-001",
            "complete": True,
            "findings": [],
            "errors": ["parser failed"],
        })
        _findings, error = verifier.parse_findings(stdout, "TENANCY-001", self.tmp)
        self.assertIn("empty errors list", error)

    def test_inventory_ignores_secret_files_and_marks_commands_unverified(self):
        (self.tmp / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
        (self.tmp / "package.json").write_text(
            json.dumps({"name": "sample", "scripts": {"test": "vitest"}, "dependencies": {"next": "1"}}),
            encoding="utf-8",
        )
        report = inspect_project.inspect(self.tmp)
        self.assertNotIn(".env", report["manifests"])
        self.assertIn("npm run test", report["candidate_commands_unverified"])
        self.assertEqual(report["package_json"][0]["framework_hints"], ["next"])
        self.assertIn("not approved architecture policy", report["notice"])

    @unittest.skipUnless(os.name == "nt" and hasattr(Path, "is_junction"), "Windows junction test")
    def test_inventory_prunes_external_and_cyclic_junctions(self):
        outside = Path(tempfile.mkdtemp(prefix="guardrail_inventory_junction_"))
        linked = self.tmp / "linked"
        back = outside / "back"
        try:
            (self.tmp / "main.py").write_text("print('main')\n", encoding="utf-8")
            for junction, target in ((back, self.tmp), (linked, outside)):
                result = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(junction), str(target)],
                    capture_output=True, text=True, check=False,
                )
                if result.returncode != 0:
                    self.skipTest(
                        "junction creation unavailable: %s" % (result.stdout + result.stderr)
                    )
                self.assertTrue(junction.is_junction())

            report = inspect_project.inspect(self.tmp, max_files=3)
            self.assertEqual(report["runtime_entrypoint_candidates"], ["main.py"])
            self.assertEqual(report["languages_by_file_count"], {"Python": 1})
            self.assertFalse(report["scan"]["truncated"])
        finally:
            if back.is_junction():
                back.rmdir()
            if linked.is_junction():
                linked.rmdir()
            shutil.rmtree(outside, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

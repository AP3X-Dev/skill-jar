#!/usr/bin/env python3
"""Dispatch repo-local lifecycle hooks into Skill Jar state files."""

import argparse

import hooklib
import jarlib


def build_parser():
    parser = argparse.ArgumentParser(description="Dispatch Skill Jar agent hooks.")
    parser.add_argument("--agent", required=True, help="agent role name")
    parser.add_argument("--event", required=True, help="event name to dispatch")
    parser.add_argument("--skill", help="skill name for the event")
    parser.add_argument("--note", default="", help="event summary")
    parser.add_argument("--status", default="", help="tracker status for update hooks")
    parser.add_argument("--clean-runs", default="0/3", help="tracker clean-run count")
    parser.add_argument("--evidence", default="", help="tracker evidence text")
    parser.add_argument("--next-action", default="", help="tracker next action")
    parser.add_argument("--failure-task", default="", help="failed-attempt task")
    parser.add_argument("--failure-what", default="", help="failed-attempt symptom")
    parser.add_argument("--lesson", default="", help="failed-attempt lesson")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    payload = {
        "skill": args.skill,
        "note": args.note,
        "status": args.status,
        "clean_runs": args.clean_runs,
        "evidence": args.evidence,
        "next_action": args.next_action,
        "failure_task": args.failure_task,
        "failure_what": args.failure_what,
        "lesson": args.lesson,
    }
    try:
        hooklib.apply_hooks(jarlib.repo_root(), args.agent, args.event, payload)
    except ValueError as exc:
        print("FAIL: %s" % exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

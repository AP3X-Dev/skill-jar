"""Hook parsing and state updates for Skill Jar loop roles."""

from datetime import datetime
from pathlib import Path
import re


HOOK_LINE_RE = re.compile(
    r"""^- `(?P<event>[^`]+)` -> `(?P<action>[^`]+)`(?: \(`(?P<target>[^`]+)`\))?: (?P<instructions>.+)$"""
)
HOOK_SECTION_RE = re.compile(r"^## Hooks\s*$", re.MULTILINE)
SKILL_LINE_RE = re.compile(r"^Skill:\s*`(?P<skill>[^`]+)`\s*$", re.MULTILINE)
USAGE_TEMPLATE = (
    "# Skill Usage -- skill-jar\n\n"
    "> Append-only log of skill and agent use. Hooks write usage evidence here; "
    "skill-forge turns queued candidates into RED pressure work.\n\n"
    "## Usage Entries\n\n"
    "## Improvement Queue\n"
)
FAILED_ATTEMPTS_TEMPLATE = (
    "# Failed Attempts -- jar-audit\n\n"
    "| ID | Task | What Failed | Lesson |\n"
    "|----|------|-------------|--------|\n"
)
SUPPORTED_ACTIONS = {
    "record_usage",
    "queue_improvement",
    "log_failed_attempt",
    "append_note",
    "update_tracker",
    "append_red_package",
    "strengthen_scenario",
    "advance_or_reopen",
    "record_verdict",
    "record_structure_result",
}
TARGET_APPEND_ACTIONS = {
    "append_note",
    "append_red_package",
    "strengthen_scenario",
    "record_verdict",
    "record_structure_result",
}


def agent_search_dirs(root):
    root = Path(root)
    dirs = [root / ".claude" / "agents"]
    dirs.extend(sorted(root.glob("*/agents/claude")))
    return dirs


def find_agent_file(root, agent_name):
    for base in agent_search_dirs(root):
        path = base / ("%s.md" % agent_name)
        if path.exists():
            return path
    raise ValueError("agent file not found for %s" % agent_name)


def read_text(path, default=None):
    path = Path(path)
    if not path.exists() and default is not None:
        return default
    return path.read_text(encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def markdown_table_cell(value):
    text = re.sub(r"[\t\r\n]+", " ", str(value))
    text = re.sub(r" {2,}", " ", text).strip()
    chars = []
    for char in text:
        if char == "|":
            backslashes = 0
            for existing in reversed(chars):
                if existing != "\\":
                    break
                backslashes += 1
            if backslashes % 2 == 0:
                chars.append("\\")
            chars.append("|")
        else:
            chars.append(char)
    return "".join(chars)


def split_markdown_table_row(row):
    cells = []
    current = []
    escaped = False
    for char in row.strip():
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            current.append(char)
            escaped = True
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells[1:-1]


def load_hooks(root, agent_name):
    text = read_text(find_agent_file(root, agent_name))
    match = HOOK_SECTION_RE.search(text)
    if not match:
        return []
    tail = text[match.end():]
    next_heading = re.search(r"^##\s+", tail, re.MULTILINE)
    block = tail[:next_heading.start()] if next_heading else tail
    hooks = []
    for raw in block.splitlines():
        line = raw.strip()
        if not line.startswith("- "):
            continue
        parsed = HOOK_LINE_RE.match(line)
        if parsed:
            hooks.append(parsed.groupdict())
    return hooks


def load_skill_name(root, agent_name):
    text = read_text(find_agent_file(root, agent_name))
    match = SKILL_LINE_RE.search(text)
    return match.group("skill") if match else agent_name


def ensure_usage_file(root):
    usage = Path(root) / "agent-state" / "skill-usage.md"
    if not usage.exists():
        write_text(usage, USAGE_TEMPLATE)
        return usage
    text = read_text(usage)
    changed = False
    if "## Usage Entries" not in text:
        text = text.rstrip() + "\n\n## Usage Entries\n"
        changed = True
    if "## Improvement Queue" not in text:
        text = text.rstrip() + "\n\n## Improvement Queue\n"
        changed = True
    if changed:
        write_text(usage, text)
    return usage


def append_section_item(path, heading, item):
    path = Path(path)
    text = read_text(path, "# Hook Log\n")
    marker = "## %s\n" % heading
    if marker not in text:
        if not text.endswith("\n"):
            text += "\n"
        text += "\n" + marker
    head, tail = text.split(marker, 1)
    next_heading = tail.find("\n## ")
    if next_heading == -1:
        body = tail
        suffix = ""
    else:
        body = tail[:next_heading]
        suffix = tail[next_heading:]

    row = "- %s" % item
    if row in body.splitlines():
        return
    body = body.rstrip("\n")
    if body:
        body += "\n"
    body += row + "\n"
    write_text(path, head + marker + body + suffix)


def append_failed_attempt(root, task, what_failed, lesson):
    path = Path(root) / "agent-state" / "failed-attempts.md"
    text = read_text(path, FAILED_ATTEMPTS_TEMPLATE)
    task = markdown_table_cell(task)
    what_failed = markdown_table_cell(what_failed)
    lesson = markdown_table_cell(lesson)
    comparable = "| %s | %s | %s |" % (task, what_failed, lesson)
    if comparable in text:
        return
    row = "| FA-%s | %s | %s | %s |" % (
        datetime.now().strftime("%Y-%m-%d-%H%M%S"),
        task,
        what_failed,
        lesson,
    )
    write_text(path, text.rstrip() + "\n" + row + "\n")


def append_usage(root, skill_name, agent_name, event, note):
    usage = ensure_usage_file(root)
    append_section_item(
        usage,
        "Usage Entries",
        "[%s/%s/%s] %s" % (skill_name, agent_name, event, note),
    )


def queue_improvement(root, skill_name, agent_name, event, note):
    usage = ensure_usage_file(root)
    append_section_item(
        usage,
        "Improvement Queue",
        "[%s/%s/%s] review candidate: %s" % (skill_name, agent_name, event, note),
    )


def resolve_target(root, target):
    root = Path(root).resolve()
    path = Path(target)
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    if root != path and root not in path.parents:
        raise ValueError("hook target outside repo: %s" % path)
    return path


def update_tracker(root, skill_name, status, clean_runs, evidence, next_action):
    tracker = Path(root) / "agent-state" / "SKILL_FORGE_TRACKER.md"
    lines = read_text(tracker).splitlines()
    for idx, line in enumerate(lines):
        if not line.startswith("| SF-"):
            continue
        cells = split_markdown_table_row(line)
        if len(cells) >= 9 and cells[1] == skill_name:
            cells[4] = markdown_table_cell(status)
            cells[5] = markdown_table_cell(clean_runs)
            cells[7] = markdown_table_cell(evidence)
            cells[8] = markdown_table_cell(next_action)
            lines[idx] = "| " + " | ".join(cells) + " |"
            write_text(tracker, "\n".join(lines) + "\n")
            return
    raise ValueError("tracker row not found for %s" % skill_name)


def _payload_note(payload, hook):
    return payload.get("note") or hook["instructions"]


def _append_hook_event(root, hook, action, note):
    target = hook.get("target")
    path = resolve_target(root, target) if target else ensure_usage_file(root)
    append_section_item(path, "Hook Events", "[%s] %s" % (action, note))


def apply_hooks(root, agent_name, event, payload):
    hooks = [hook for hook in load_hooks(root, agent_name) if hook["event"] == event]
    skill_name = payload.get("skill") or load_skill_name(root, agent_name)
    for hook in hooks:
        action = hook["action"]
        if action not in SUPPORTED_ACTIONS:
            raise ValueError("unsupported hook action: %s" % action)
        if hook.get("target"):
            resolve_target(root, hook["target"])

        note = _payload_note(payload, hook)
        if action == "record_usage":
            append_usage(root, skill_name, agent_name, event, note)
        elif action == "queue_improvement":
            queue_improvement(root, skill_name, agent_name, event, note)
        elif action == "log_failed_attempt":
            append_failed_attempt(
                root,
                payload.get("failure_task", ""),
                payload.get("failure_what", ""),
                payload.get("lesson", ""),
            )
        elif action in TARGET_APPEND_ACTIONS:
            _append_hook_event(root, hook, action, note)
        elif action in {"update_tracker", "advance_or_reopen"}:
            update_tracker(
                root,
                skill_name,
                payload.get("status", ""),
                payload.get("clean_runs", "0/3"),
                payload.get("evidence", ""),
                payload.get("next_action", ""),
            )

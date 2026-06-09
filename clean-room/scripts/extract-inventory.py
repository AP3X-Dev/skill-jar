#!/usr/bin/env python3
"""AST-based symbol inventory extractor for the clean-room skill (schema v2).

Walks a repo, parses source files with TreeSitter, and emits a deterministic
JSON inventory of every symbol (including private and nested) with Tier-1
tags from scripts/inventory-vocab.json. The inventory feeds Phase 1 Passes
3/4/5/7/9 in Clean-Room mode, Passes A/B/C in Parity Mode, and the new
Pass 4.5 Integration Seams.

v2 adds three passes over the AST:
  E1 — Symbol pass (extended: nested symbols, visibility, content shapes,
       content snapshots with sidecars)
  E2 — Call-edge pass (who calls whom, with argument-binding snapshots)
  E3 — Field-I/O pass (read/write sites per field, with op_detail for
       distinguishing `assign` vs `append` vs `augmented-assign` etc.)

The consuming scripts — diff-inventory.py and generate-wire-ledger.py —
use the three arrays together to detect cross-module wiring gaps that
single-symbol analysis cannot see.

Design principles:
- Deterministic: same repo → byte-identical JSON. All arrays sorted.
- Closed-vocabulary: every tag is validated against inventory-vocab.json.
- No verbatim source in the main inventory file: signature text is truncated
  and normalized; bodies are NOT emitted. Content snapshots for prompt/regex
  symbols live in gitignored sidecar files under clean-room/content/.
- Python gets the full v2 treatment (all three passes). JS/TS/Go/Rust get
  the legacy Pass E1 symbol emission only for this iteration; call_edges
  and field_io for those languages are reserved for follow-up work and
  emit empty arrays. v1 consumers remain compatible.

Usage:
  extract-inventory.py <repo-root> [-o inventory.json]
  extract-inventory.py <repo-root> --languages python,typescript
  extract-inventory.py <repo-root> --exclude '**/vendor/**'
  extract-inventory.py <repo-root> --no-content-sidecar
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from fnmatch import fnmatch
from pathlib import Path

try:
    from tree_sitter_language_pack import get_parser
except ImportError:
    print(
        "tree_sitter_language_pack is required. Install with:\n"
        "  pip install tree-sitter-language-pack",
        file=sys.stderr,
    )
    sys.exit(2)


# ---------- configuration ----------

SCHEMA_VERSION = "2"

SCRIPT_DIR = Path(__file__).resolve().parent
VOCAB_PATH = SCRIPT_DIR / "inventory-vocab.json"

LANGUAGES: dict[str, tuple[str, str]] = {
    ".py": ("python", "python"),
    ".js": ("javascript", "javascript"),
    ".jsx": ("javascript", "javascript"),
    ".mjs": ("javascript", "javascript"),
    ".cjs": ("javascript", "javascript"),
    ".ts": ("typescript", "typescript"),
    ".tsx": ("tsx", "typescript"),
    ".go": ("go", "go"),
    ".rs": ("rust", "rust"),
}

IGNORED_DIRS = {
    ".git", "node_modules", "target", "dist", "build", "out",
    "__pycache__", "clean-room", ".venv", "venv", ".next", ".nuxt",
    ".turbo", "coverage", ".pytest_cache", ".mypy_cache", ".tox",
    "vendor", "third_party", ".idea", ".vscode",
}

TEST_PATH_PATTERNS = re.compile(
    r"(^|/)(tests?|__tests__|spec|specs)(/|$)"
    r"|\.test\.|\.spec\.|_test\.|_spec\."
)
FIXTURE_PATH_PATTERNS = re.compile(r"(^|/)(fixtures?|testdata|__fixtures__)(/|$)")
MIGRATION_PATH_PATTERNS = re.compile(r"(^|/)(migrations?|db/migrate)(/|$)")
BENCH_PATH_PATTERNS = re.compile(r"(^|/)(bench(es|marks?)?)(/|$)|_bench\.|\.bench\.")
EXAMPLE_PATH_PATTERNS = re.compile(r"(^|/)(examples?|samples?)(/|$)")

ERROR_NAME_RE = re.compile(r"(Error|Exception)$")
SIGNATURE_MAX_LEN = 200

# Shape-detection heuristics (shared across languages).
PROMPT_NAME_RE = re.compile(r"(PROMPT|TEMPLATE|SYSTEM|INSTRUCTION)", re.IGNORECASE)
REGEX_NAME_RE = re.compile(r"(REGEX|PATTERN|^RE_|_RE$)", re.IGNORECASE)
THRESHOLD_NAME_RE = re.compile(
    r"(THRESHOLD|CUTOFF|_MIN|_MAX|MIN_|MAX_|RATIO|PERCENT|LIMIT)", re.IGNORECASE
)
CONFIG_NAME_RE = re.compile(r"(CONFIG|DEFAULTS|SETTINGS|OPTIONS)", re.IGNORECASE)

PROMPT_MIN_CHARS = 200
PROMPT_MIN_LINES = 10

# Mutation-method names (language-agnostic heuristic for field_io op_detail).
MUTATION_METHODS = {
    "append", "extend", "insert", "pop", "remove", "clear", "update",
    "add", "discard", "popitem", "setdefault", "push", "unshift",
    "shift", "splice", "sort", "reverse",
}
# Methods whose effect is mostly read (for disambiguation).
READ_ONLY_METHODS = {"get", "keys", "values", "items", "copy", "count", "index"}


# ---------- data model ----------

@dataclass
class Symbol:
    id: str
    name: str
    qualified_name: str
    file: str
    line: int
    end_line: int
    language: str
    signature: str
    kind: str
    modifiers: list[str] = field(default_factory=list)
    shape: list[str] = field(default_factory=list)
    location: str = "source"
    parent: str | None = None          # legacy: parent name (e.g., class name)
    parent_id: str | None = None        # v2: parent symbol id
    enclosing_scope: str | None = None  # v2: enclosing function symbol id (if nested)
    visibility: str = "public"          # v2: public | private | nested
    content_snapshot: dict | None = None  # v2: {sha256, length, line_count, token_count_estimate}
    tier2: dict = field(default_factory=lambda: {"role": [], "concern": [], "risk": []})


@dataclass
class CallEdge:
    id: str
    caller_id: str
    callee_name: str
    receiver_hint: str | None
    file: str
    line: int
    arg_bindings: list[dict] = field(default_factory=list)
    resolution: str = "unresolved"           # resolved | ambiguous | unresolved
    resolved_callee_id: str | None = None
    candidate_ids: list[str] = field(default_factory=list)


@dataclass
class FieldIO:
    id: str
    owner_id: str
    field: str
    op: str                 # read | write | delete
    op_detail: str | None   # assign | append | extend | inplace-op | destructure | augmented-assign | setitem | method-mutation (writes) | None (reads)
    context_symbol_id: str  # the enclosing function/method symbol id
    file: str
    line: int


# ---------- vocab ----------

def load_vocab() -> dict:
    with VOCAB_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_symbol(sym: Symbol, vocab: dict) -> list[str]:
    errors = []
    t1 = vocab["tier1"]
    if sym.kind not in t1["kind"]:
        errors.append(f"{sym.id}: invalid kind {sym.kind!r}")
    for m in sym.modifiers:
        if m not in t1["modifier"]:
            errors.append(f"{sym.id}: invalid modifier {m!r}")
    for s in sym.shape:
        if s not in t1["shape"]:
            errors.append(f"{sym.id}: invalid shape {s!r}")
    if sym.location not in t1["location"]:
        errors.append(f"{sym.id}: invalid location {sym.location!r}")
    vis_allowed = t1.get("visibility", ["public", "private", "nested"])
    if sym.visibility not in vis_allowed:
        errors.append(f"{sym.id}: invalid visibility {sym.visibility!r}")
    return errors


# ---------- helpers ----------

def classify_location(relpath: str) -> str:
    p = relpath.replace("\\", "/")
    if TEST_PATH_PATTERNS.search(p):
        return "test"
    if FIXTURE_PATH_PATTERNS.search(p):
        return "fixture"
    if MIGRATION_PATH_PATTERNS.search(p):
        return "migration"
    if BENCH_PATH_PATTERNS.search(p):
        return "benchmark"
    if EXAMPLE_PATH_PATTERNS.search(p):
        return "example"
    return "source"


def normalize_signature(raw: str) -> str:
    s = re.sub(r"\s+", " ", raw.strip())
    if len(s) > SIGNATURE_MAX_LEN:
        s = s[:SIGNATURE_MAX_LEN] + "..."
    return s


def node_text(node, src: bytes) -> str:
    return src[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def first_line(node, src: bytes) -> str:
    text = node_text(node, src)
    return text.split("\n", 1)[0]


def find_child(node, type_name: str):
    for c in node.children:
        if c.type == type_name:
            return c
    return None


def find_children(node, type_name: str) -> list:
    return [c for c in node.children if c.type == type_name]


def body_has_descendant(node, types: set[str]) -> bool:
    stack = list(node.children)
    while stack:
        n = stack.pop()
        if n.type in types:
            return True
        stack.extend(n.children)
    return False


def unquote_py_string(raw: str) -> str:
    """Strip Python string quoting — handles triple-quoted, f-strings, raw prefixes."""
    s = raw.strip()
    # drop f/r/b/u prefixes
    while s and s[0] in "fFrRbBuU":
        s = s[1:]
    if s.startswith('"""') and s.endswith('"""'):
        return s[3:-3]
    if s.startswith("'''") and s.endswith("'''"):
        return s[3:-3]
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def detect_content_shape(name: str, value_text: str | None, value_is_string: bool,
                          value_is_numeric: bool, value_is_collection: bool) -> list[str]:
    """Classify a module-level constant's content shape based on name + value.

    Returns a list because shapes are multi-select. Empty list = no content shape detected.
    """
    shapes: list[str] = []
    if value_is_string and value_text is not None:
        # prompt-template: long OR multi-line OR name matches
        lines = value_text.count("\n") + 1
        length = len(value_text)
        name_match = bool(PROMPT_NAME_RE.search(name))
        if name_match or length >= PROMPT_MIN_CHARS or lines >= PROMPT_MIN_LINES:
            # bias toward prompt-template unless the name screams regex
            if REGEX_NAME_RE.search(name):
                shapes.append("regex")
            else:
                shapes.append("prompt-template")
        elif REGEX_NAME_RE.search(name):
            shapes.append("regex")
    if value_is_numeric and THRESHOLD_NAME_RE.search(name):
        shapes.append("threshold")
    if value_is_collection and CONFIG_NAME_RE.search(name):
        shapes.append("config-const")
    return shapes


def content_snapshot(raw: str) -> dict:
    sha = hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()
    return {
        "sha256": sha,
        "length": len(raw),
        "line_count": raw.count("\n") + 1,
        "token_count_estimate": (len(raw) + 3) // 4,
    }


def write_content_sidecar(sidecar_dir: Path, snapshot: dict, raw: str) -> None:
    sidecar_dir.mkdir(parents=True, exist_ok=True)
    p = sidecar_dir / f"{snapshot['sha256']}.txt"
    if not p.exists():
        p.write_text(raw, encoding="utf-8")


# ---------- Python extractor (v2 — full treatment) ----------

def extract_python(tree, src: bytes, relpath: str, location: str) -> list[Symbol]:
    """v2 Python extractor: emits top-level, class-level, nested symbols,
    with visibility, content shapes, and content snapshots."""
    out: list[Symbol] = []
    root = tree.root_node

    def make_id(qname: str) -> str:
        return f"{relpath}:{qname}"

    def is_exported(name: str) -> bool:
        return not name.startswith("_")

    def has_throws(body) -> bool:
        return body is not None and body_has_descendant(body, {"raise_statement"})

    def is_async_def(node) -> bool:
        if node.type == "async_function_definition":
            return True
        for c in node.children:
            if c.type == "async":
                return True
        return False

    def decorator_names(node) -> list[str]:
        names = []
        parent = node.parent
        if parent and parent.type == "decorated_definition":
            for d in find_children(parent, "decorator"):
                txt = node_text(d, src).strip().lstrip("@").split("(", 1)[0]
                names.append(txt)
        return names

    def emit_function(node, parent_qname: str | None, parent_sym_id: str | None,
                       enclosing_fn_id: str | None):
        name_node = find_child(node, "identifier")
        if not name_node:
            return None
        name = node_text(name_node, src)
        body = find_child(node, "block")
        sig_end = body.start_byte if body else node.end_byte
        signature = normalize_signature(
            src[node.start_byte:sig_end].decode("utf-8", errors="replace").rstrip(":")
        )
        mods: list[str] = []
        if is_async_def(node):
            mods.append("async")
        if has_throws(body):
            mods.append("throws")
        decos = decorator_names(node)
        shape: list[str] = []
        if any(d in ("staticmethod",) for d in decos):
            mods.append("static")
        if any(d.endswith("deprecated") for d in decos):
            mods.append("deprecated")
        if any(d in ("abstractmethod", "abc.abstractmethod") for d in decos):
            mods.append("abstract")
        if body and body_has_descendant(body, {"yield", "yield_expression", "yield_statement"}):
            mods.append("generator")
        is_method = parent_qname is not None and enclosing_fn_id is None
        if is_exported(name) and enclosing_fn_id is None:
            mods.append("exported")
        if name == "main" and parent_qname is None and enclosing_fn_id is None:
            shape.append("entrypoint")

        qname = f"{parent_qname}.{name}" if parent_qname else name
        sym_id = make_id(qname)
        kind = "method" if is_method else "function"

        if enclosing_fn_id is not None:
            visibility = "nested"
        elif is_exported(name):
            visibility = "public"
        else:
            visibility = "private"

        sym = Symbol(
            id=sym_id,
            name=name,
            qualified_name=qname,
            file=relpath,
            line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            language="python",
            signature=signature,
            kind=kind,
            modifiers=sorted(set(mods)),
            shape=sorted(set(shape)),
            location=location,
            parent=parent_qname,
            parent_id=parent_sym_id,
            enclosing_scope=enclosing_fn_id,
            visibility=visibility,
        )
        out.append(sym)

        # Recurse into body for nested functions and class defs.
        if body:
            for child in body.children:
                if child.type in ("function_definition", "async_function_definition"):
                    emit_function(child, parent_qname=None, parent_sym_id=None,
                                  enclosing_fn_id=sym_id)
                elif child.type == "decorated_definition":
                    inner = find_child(child, "function_definition") or find_child(child, "async_function_definition")
                    if inner:
                        emit_function(inner, parent_qname=None, parent_sym_id=None,
                                      enclosing_fn_id=sym_id)

        return sym

    def emit_class(node, parent_qname: str | None = None,
                   parent_sym_id: str | None = None):
        name_node = find_child(node, "identifier")
        if not name_node:
            return None
        name = node_text(name_node, src)
        superclasses = find_child(node, "argument_list")
        super_text = node_text(superclasses, src) if superclasses else ""
        shape: list[str] = []
        if ERROR_NAME_RE.search(name) or any(
            w in super_text for w in ("Exception", "Error", "BaseException")
        ):
            shape.append("error-type")
        mods: list[str] = []
        if is_exported(name):
            mods.append("exported")
        signature = normalize_signature(f"class {name}{super_text}")

        qname = f"{parent_qname}.{name}" if parent_qname else name
        sym_id = make_id(qname)
        visibility = "public" if is_exported(name) else "private"

        sym = Symbol(
            id=sym_id,
            name=name,
            qualified_name=qname,
            file=relpath,
            line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            language="python",
            signature=signature,
            kind="class",
            modifiers=sorted(set(mods)),
            shape=sorted(set(shape)),
            location=location,
            parent=parent_qname,
            parent_id=parent_sym_id,
            visibility=visibility,
        )
        out.append(sym)

        body = find_child(node, "block")
        if body:
            for child in body.children:
                if child.type in ("function_definition", "async_function_definition"):
                    emit_function(child, parent_qname=qname, parent_sym_id=sym_id,
                                  enclosing_fn_id=None)
                elif child.type == "decorated_definition":
                    inner = find_child(child, "function_definition") or find_child(child, "async_function_definition")
                    if inner:
                        emit_function(inner, parent_qname=qname, parent_sym_id=sym_id,
                                      enclosing_fn_id=None)
                    inner_cls = find_child(child, "class_definition")
                    if inner_cls:
                        emit_class(inner_cls, parent_qname=qname, parent_sym_id=sym_id)
                elif child.type == "class_definition":
                    emit_class(child, parent_qname=qname, parent_sym_id=sym_id)
        return sym

    def emit_assignment(node):
        """Top-level constant/variable assignment — detect content shapes.

        Accepts either an `expression_statement` wrapping an `assignment`, or
        a bare `assignment` node (tree-sitter-python emits the latter at
        module level)."""
        if node.type == "assignment":
            assign = node
        else:
            assign = find_child(node, "assignment")
        if assign is None:
            return
        # LHS identifier
        children = assign.children
        if not children:
            return
        lhs = children[0]
        if lhs.type != "identifier":
            return
        name = node_text(lhs, src)
        # find RHS (right of '=')
        rhs = None
        saw_eq = False
        for c in children:
            if c.type == "=":
                saw_eq = True
                continue
            if saw_eq:
                rhs = c
                break
        if rhs is None:
            return

        value_is_string = rhs.type in ("string", "concatenated_string")
        value_is_numeric = rhs.type in ("integer", "float")
        value_is_collection = rhs.type in ("dictionary", "list", "set", "tuple")

        value_text = None
        if value_is_string:
            raw = node_text(rhs, src)
            value_text = unquote_py_string(raw)

        shapes = detect_content_shape(
            name=name,
            value_text=value_text,
            value_is_string=value_is_string,
            value_is_numeric=value_is_numeric,
            value_is_collection=value_is_collection,
        )
        if not shapes:
            return

        mods = ["exported"] if is_exported(name) else []
        visibility = "public" if is_exported(name) else "private"
        kind = "constant" if name.isupper() or name.replace("_", "").isupper() else "variable"

        snap = None
        if value_text is not None and ("prompt-template" in shapes or "regex" in shapes):
            snap = content_snapshot(value_text)

        sym_id = make_id(name)
        sym = Symbol(
            id=sym_id,
            name=name,
            qualified_name=name,
            file=relpath,
            line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            language="python",
            signature=normalize_signature(node_text(node, src)),
            kind=kind,
            modifiers=sorted(set(mods)),
            shape=sorted(set(shapes)),
            location=location,
            parent=None,
            parent_id=None,
            enclosing_scope=None,
            visibility=visibility,
            content_snapshot=snap,
        )
        # Stash raw value text on the symbol instance so the caller can write the sidecar.
        # We use a weak channel: the content_snapshot already carries the hash, and the
        # caller looks up the raw text from _content_sidecar_pending via sym.id.
        _content_pending[sym_id] = value_text or ""
        out.append(sym)

    _content_pending: dict[str, str] = {}

    # Top-level scan
    for child in root.children:
        if child.type in ("function_definition", "async_function_definition"):
            emit_function(child, parent_qname=None, parent_sym_id=None, enclosing_fn_id=None)
        elif child.type == "decorated_definition":
            inner = find_child(child, "function_definition") or find_child(child, "async_function_definition")
            if inner:
                emit_function(inner, parent_qname=None, parent_sym_id=None, enclosing_fn_id=None)
            inner_class = find_child(child, "class_definition")
            if inner_class:
                emit_class(inner_class)
        elif child.type == "class_definition":
            emit_class(child)
        elif child.type in ("expression_statement", "assignment"):
            emit_assignment(child)
        elif child.type == "if_statement":
            cond = node_text(child, src).split("\n", 1)[0]
            if "__name__" in cond and "__main__" in cond:
                out.append(Symbol(
                    id=f"{relpath}:<module-main>",
                    name="<module-main>",
                    qualified_name="<module-main>",
                    file=relpath,
                    line=child.start_point[0] + 1,
                    end_line=child.end_point[0] + 1,
                    language="python",
                    signature=normalize_signature(cond),
                    kind="module",
                    shape=["entrypoint"],
                    location=location,
                    visibility="public",
                ))

    # Expose pending content for the driver to write sidecars.
    extract_python._pending_content = _content_pending  # type: ignore[attr-defined]
    return out


# ---------- Python call-edge extractor (v2 E2 pass) ----------

def extract_python_call_edges(tree, src: bytes, relpath: str,
                               symbols_by_id: dict[str, Symbol]) -> list[CallEdge]:
    """Walk Call nodes and emit call_edge records.

    Caller is the innermost enclosing function/method symbol. For Python this
    requires walking the AST with a scope stack, keeping track of the current
    enclosing function symbol id.
    """
    edges: list[CallEdge] = []
    root = tree.root_node
    edge_counter = [0]

    # Pre-build: map (file, line-range) -> symbol for enclosing-fn lookup.
    # Keep only functions/methods in this file.
    file_fns = sorted(
        [s for s in symbols_by_id.values()
         if s.file == relpath and s.kind in ("function", "method")],
        key=lambda s: (s.line, -s.end_line),  # outermost first for tie-break
    )

    def enclosing_fn_id(line: int) -> str | None:
        """Find the innermost enclosing function symbol for a given line."""
        candidates = [s for s in file_fns if s.line <= line <= s.end_line]
        if not candidates:
            return None
        # innermost = smallest span
        candidates.sort(key=lambda s: s.end_line - s.line)
        return candidates[0].id

    def literal_kind(arg_node):
        """Classify a single argument node into arg_binding kind + literal_value."""
        t = arg_node.type
        if t == "string":
            raw = node_text(arg_node, src)
            val = unquote_py_string(raw)
            return "literal", (raw, (val if val == "" else None))
        if t in ("integer", "float"):
            raw = node_text(arg_node, src)
            try:
                v = int(raw) if t == "integer" else float(raw)
            except ValueError:
                v = None
            is_empty = v == 0 or v == 0.0
            return "literal", (raw, (0 if is_empty else None))
        if t == "true":
            return "literal", ("True", None)
        if t == "false":
            return "literal", ("False", False)
        if t == "none":
            return "literal", ("None", None)
        if t == "list":
            raw = node_text(arg_node, src)
            is_empty = raw.strip() in ("[]",)
            return "literal", (raw, ([] if is_empty else None))
        if t == "dictionary":
            raw = node_text(arg_node, src)
            is_empty = raw.strip() in ("{}",)
            return "literal", (raw, ({} if is_empty else None))
        if t == "tuple":
            raw = node_text(arg_node, src)
            is_empty = raw.strip() in ("()",)
            return "literal", (raw, (() if is_empty else None))
        if t == "identifier":
            return "variable", (node_text(arg_node, src), None)
        if t == "list_splat" or t == "dictionary_splat":
            return "spread", (node_text(arg_node, src), None)
        if t == "keyword_argument":
            # e.g. `client_sop_text=""`
            value = None
            for c in arg_node.children:
                if c.type == "=":
                    continue
                value = c
            if value is not None:
                kind, (expr, lit) = literal_kind(value)
                return kind, (expr, lit)
            return "complex-expr", (node_text(arg_node, src), None)
        return "complex-expr", (node_text(arg_node, src), None)

    def keyword_name(arg_node) -> str | None:
        if arg_node.type != "keyword_argument":
            return None
        ident = find_child(arg_node, "identifier")
        return node_text(ident, src) if ident else None

    def dissect_call(call_node):
        # callee
        callee_name = None
        receiver_hint = None
        fn_node = None
        for c in call_node.children:
            if c.type in ("identifier", "attribute", "subscript"):
                fn_node = c
                break
        if fn_node is None:
            return
        if fn_node.type == "identifier":
            callee_name = node_text(fn_node, src)
        elif fn_node.type == "attribute":
            # attribute: object . attribute
            ident = None
            for c in fn_node.children:
                if c.type in ("identifier", "attribute"):
                    ident = c
            if ident is not None:
                callee_name_node = None
                for c in fn_node.children:
                    if c.type == "identifier":
                        callee_name_node = c
                if callee_name_node is None:
                    callee_name = node_text(fn_node, src).split(".")[-1]
                else:
                    callee_name = node_text(callee_name_node, src)
            receiver_raw = node_text(fn_node, src).rsplit(".", 1)[0] if "." in node_text(fn_node, src) else None
            receiver_hint = receiver_raw
        else:
            # subscript and other — treat as complex, drop resolution
            return

        if not callee_name:
            return

        args_list = find_child(call_node, "argument_list")
        arg_bindings = []
        positional_index = 0
        if args_list is not None:
            for arg in args_list.children:
                if arg.type in ("(", ")", ","):
                    continue
                kw = keyword_name(arg)
                kind, (expr, lit) = literal_kind(arg)
                binding: dict = {"kind": kind, "expr": expr}
                if kw is not None:
                    binding["param"] = kw
                else:
                    binding["param"] = f"arg{positional_index}"
                    positional_index += 1
                if kind == "literal":
                    # Only emit literal_value for empty-ish literals; others omitted.
                    if lit is not None or expr in ('""', "''", '""""""', "''''''", "None", "False", "[]", "{}", "()"):
                        # Normalize literal_value: empty string, None, 0, False, [], {}, ()
                        if expr in ('""', "''"):
                            binding["literal_value"] = ""
                        elif expr == "None":
                            binding["literal_value"] = None
                        elif expr == "False":
                            binding["literal_value"] = False
                        elif expr == "[]":
                            binding["literal_value"] = []
                        elif expr == "{}":
                            binding["literal_value"] = {}
                        elif expr == "()":
                            binding["literal_value"] = []
                        elif lit is not None:
                            # numeric 0 / float 0.0
                            binding["literal_value"] = lit
                arg_bindings.append(binding)

        caller_id = enclosing_fn_id(call_node.start_point[0] + 1)
        if caller_id is None:
            # module-level call — use a synthetic id so data-flow analysis can still hook in
            caller_id = f"{relpath}:<module>"

        edge_counter[0] += 1
        edges.append(CallEdge(
            id=f"edge:{relpath}:{call_node.start_point[0] + 1}:{edge_counter[0]}",
            caller_id=caller_id,
            callee_name=callee_name,
            receiver_hint=receiver_hint,
            file=relpath,
            line=call_node.start_point[0] + 1,
            arg_bindings=arg_bindings,
        ))

    # Walk all Call nodes in this file.
    stack = list(root.children)
    while stack:
        n = stack.pop()
        if n.type == "call":
            dissect_call(n)
        stack.extend(n.children)

    return edges


# ---------- Python field-I/O extractor (v2 E3 pass) ----------

def extract_python_field_io(tree, src: bytes, relpath: str,
                              symbols_by_id: dict[str, Symbol]) -> list[FieldIO]:
    """Walk attribute and subscript references for self.* and module-level names,
    and emit read/write records with op_detail."""
    ios: list[FieldIO] = []
    root = tree.root_node
    ctr = [0]

    # Enclosing fn lookup (same as call_edges)
    file_fns = sorted(
        [s for s in symbols_by_id.values()
         if s.file == relpath and s.kind in ("function", "method")],
        key=lambda s: (s.line, -s.end_line),
    )

    def enclosing_fn(line: int) -> Symbol | None:
        candidates = [s for s in file_fns if s.line <= line <= s.end_line]
        if not candidates:
            return None
        candidates.sort(key=lambda s: s.end_line - s.line)
        return candidates[0]

    def owner_for(context_sym: Symbol | None) -> str:
        if context_sym is None:
            return f"{relpath}:<module>"
        if context_sym.parent_id is not None:
            return context_sym.parent_id
        return f"{relpath}:<module>"

    def emit(field: str, op: str, op_detail: str | None, line: int,
             context: Symbol | None):
        ctr[0] += 1
        ctx_id = context.id if context is not None else f"{relpath}:<module>"
        ios.append(FieldIO(
            id=f"io:{relpath}:{line}:{op}:{ctr[0]}",
            owner_id=owner_for(context),
            field=field,
            op=op,
            op_detail=op_detail,
            context_symbol_id=ctx_id,
            file=relpath,
            line=line,
        ))

    def attribute_parts(node) -> tuple[str | None, str | None]:
        """For a `self.foo` attribute node, return (receiver_name, attr_name).
        Returns (None, None) if not applicable."""
        if node.type != "attribute":
            return None, None
        parts = [c for c in node.children if c.type != "."]
        if len(parts) < 2:
            return None, None
        base = parts[0]
        attr = parts[-1]
        if base.type == "identifier" and attr.type == "identifier":
            return node_text(base, src), node_text(attr, src)
        return None, None

    def analyze_assignment(assign_node, context: Symbol | None):
        """assign_node is an `assignment` AST node: LHS = RHS."""
        children = [c for c in assign_node.children]
        if len(children) < 3:
            return
        lhs = children[0]
        op = children[1]
        # augmented_assignment has different structure, handled elsewhere
        line = assign_node.start_point[0] + 1

        def write_for_lhs(node, op_detail: str):
            if node.type == "attribute":
                base, attr = attribute_parts(node)
                if base == "self" and attr:
                    emit(attr, "write", op_detail, line, context)
                elif base is None and attr is None:
                    # nested attribute? best effort
                    txt = node_text(node, src)
                    if txt.startswith("self."):
                        emit(txt.split(".", 1)[1].split(".", 1)[0], "write", op_detail, line, context)
            elif node.type == "subscript":
                # self.foo[k] = v  -> setitem on foo
                obj = node.children[0] if node.children else None
                if obj is not None and obj.type == "attribute":
                    base, attr = attribute_parts(obj)
                    if base == "self" and attr:
                        emit(attr, "write", "setitem", line, context)
            elif node.type == "identifier" and context is None:
                # module-level assignment
                emit(node_text(node, src), "write", op_detail, line, context)
            elif node.type in ("tuple_pattern", "list_pattern", "pattern_list"):
                # destructure
                for c in node.children:
                    write_for_lhs(c, "destructure")

        if op.type == "=":
            write_for_lhs(lhs, "assign")
        # augmented assign is its own node type; handled in analyze_node

    def analyze_aug_assign(node, context: Symbol | None):
        # augmented_assignment: lhs (op) rhs, where op is like +=, -=, etc.
        children = [c for c in node.children]
        if len(children) < 3:
            return
        lhs = children[0]
        op_node = children[1]
        line = node.start_point[0] + 1
        op_detail = "inplace-op"
        if op_node.type == "+=":
            op_detail = "extend" if _is_collection_context(lhs) else "inplace-op"
        elif op_node.type in ("-=", "*=", "/=", "%=", "**="):
            op_detail = "inplace-op"
        else:
            op_detail = "augmented-assign"

        if lhs.type == "attribute":
            base, attr = attribute_parts(lhs)
            if base == "self" and attr:
                emit(attr, "write", op_detail, line, context)
        elif lhs.type == "identifier" and context is None:
            emit(node_text(lhs, src), "write", op_detail, line, context)

    def _is_collection_context(node) -> bool:
        return False  # best-effort default — op_detail=inplace-op is fine

    def analyze_call(call_node, context: Symbol | None):
        """Detect mutation-method calls on self.field, e.g. self.matched.append(x)."""
        fn_node = None
        for c in call_node.children:
            if c.type in ("identifier", "attribute"):
                fn_node = c
                break
        if fn_node is None or fn_node.type != "attribute":
            return
        # self.field.method
        parts_text = node_text(fn_node, src)
        m = re.match(r"self\.([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)$", parts_text)
        if not m:
            return
        field_name, method = m.group(1), m.group(2)
        if method in READ_ONLY_METHODS:
            emit(field_name, "read", None, call_node.start_point[0] + 1, context)
            return
        if method in MUTATION_METHODS:
            op_detail = method if method in ("append", "extend") else "method-mutation"
            emit(field_name, "write", op_detail, call_node.start_point[0] + 1, context)

    def analyze_node(node, context: Symbol | None):
        """Recursive walk tracking enclosing function context. Reads are
        emitted for any self.X access that isn't part of a write LHS."""
        t = node.type
        if t in ("function_definition", "async_function_definition"):
            new_ctx = enclosing_fn(node.start_point[0] + 1)
            for c in node.children:
                analyze_node(c, new_ctx)
            return
        if t == "assignment":
            analyze_assignment(node, context)
            # walk RHS for reads
            rhs_seen = False
            for c in node.children:
                if c.type == "=":
                    rhs_seen = True
                    continue
                if rhs_seen:
                    analyze_node(c, context)
            return
        if t == "augmented_assignment":
            analyze_aug_assign(node, context)
            # walk RHS for reads (the lhs also reads in aug-assign but we already counted the write)
            seen_op = False
            for c in node.children:
                if c.type in ("+=", "-=", "*=", "/=", "%=", "**=", "|=", "&=", "^=", ">>=", "<<="):
                    seen_op = True
                    continue
                if seen_op:
                    analyze_node(c, context)
            return
        if t == "call":
            analyze_call(node, context)
            # recurse into args
            for c in node.children:
                analyze_node(c, context)
            return
        if t == "attribute" and context is not None:
            base, attr = attribute_parts(node)
            if base == "self" and attr:
                # read by default (writes already handled in assignment)
                emit(attr, "read", None, node.start_point[0] + 1, context)
            return
        for c in node.children:
            analyze_node(c, context)

    analyze_node(root, None)
    return ios


# ---------- JS/TS/Go/Rust extractors (legacy Pass E1 only for v2) ----------

def extract_javascript_like(tree, src: bytes, relpath: str, location: str, language: str) -> list[Symbol]:
    out: list[Symbol] = []
    root = tree.root_node

    def visibility_for(name: str) -> str:
        return "public" if not name.startswith("#") and not name.startswith("_") else "private"

    def emit(kind: str, name: str, node, mods: list[str], shape: list[str],
             signature: str, parent: str | None = None, parent_id: str | None = None):
        q = f"{parent}.{name}" if parent else name
        out.append(Symbol(
            id=f"{relpath}:{q}",
            name=name,
            qualified_name=q,
            file=relpath,
            line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            language=language,
            signature=normalize_signature(signature),
            kind=kind,
            modifiers=sorted(set(mods)),
            shape=sorted(set(shape)),
            location=location,
            parent=parent,
            parent_id=parent_id,
            visibility=visibility_for(name),
        ))

    def get_name(node) -> str | None:
        for t in ("identifier", "property_identifier", "type_identifier", "name"):
            n = find_child(node, t)
            if n:
                return node_text(n, src)
        return None

    def has_throws(body) -> bool:
        return body is not None and body_has_descendant(body, {"throw_statement"})

    def has_yield(body) -> bool:
        return body is not None and body_has_descendant(body, {"yield_expression"})

    def signature_of(node, body_types=("statement_block", "function_body")) -> str:
        body = None
        for bt in body_types:
            body = find_child(node, bt)
            if body:
                break
        end = body.start_byte if body else node.end_byte
        return src[node.start_byte:end].decode("utf-8", errors="replace")

    def walk(node, parent: str | None):
        for child in node.children:
            t = child.type
            if t == "export_statement":
                for inner in child.children:
                    if inner.type in (
                        "function_declaration", "generator_function_declaration",
                        "class_declaration", "abstract_class_declaration",
                        "interface_declaration", "type_alias_declaration",
                        "enum_declaration", "lexical_declaration", "variable_declaration",
                    ):
                        handle(inner, parent, exported=True)
                continue
            handle(child, parent, exported=False)

    def handle(child, parent: str | None, exported: bool):
        t = child.type
        name = get_name(child)
        if t in ("function_declaration", "generator_function_declaration"):
            if not name:
                return
            body = find_child(child, "statement_block")
            mods = []
            if any(c.type == "async" for c in child.children):
                mods.append("async")
            if t == "generator_function_declaration" or has_yield(body):
                mods.append("generator")
            if has_throws(body):
                mods.append("throws")
            if exported:
                mods.append("exported")
            shape = ["entrypoint"] if (parent is None and name == "main") else []
            emit("function", name, child, mods, shape, signature_of(child), parent)

        elif t in ("class_declaration", "abstract_class_declaration"):
            if not name:
                return
            mods = []
            if t == "abstract_class_declaration":
                mods.append("abstract")
            if exported:
                mods.append("exported")
            heritage = find_child(child, "class_heritage")
            heritage_text = node_text(heritage, src) if heritage else ""
            shape = []
            if ERROR_NAME_RE.search(name) or any(
                w in heritage_text for w in ("Error", "Exception")
            ):
                shape.append("error-type")
            emit("class", name, child, mods, shape, f"class {name} {heritage_text}".strip(), parent)
            class_id = f"{relpath}:{name}" if not parent else f"{relpath}:{parent}.{name}"
            body = find_child(child, "class_body")
            if body:
                for m in body.children:
                    if m.type in ("method_definition", "method_signature"):
                        mname = get_name(m)
                        if not mname:
                            continue
                        mmods = []
                        for c in m.children:
                            if c.type == "async":
                                mmods.append("async")
                            if c.type == "static":
                                mmods.append("static")
                            if c.type in ("readonly", "abstract"):
                                mmods.append(c.type)
                        mbody = find_child(m, "statement_block")
                        if has_throws(mbody):
                            mmods.append("throws")
                        if has_yield(mbody):
                            mmods.append("generator")
                        emit("method", mname, m, mmods, [], signature_of(m),
                             parent=name, parent_id=class_id)

        elif t == "interface_declaration":
            if not name:
                return
            mods = ["exported"] if exported else []
            emit("interface", name, child, mods, [], first_line(child, src), parent)

        elif t == "type_alias_declaration":
            if not name:
                return
            mods = ["exported"] if exported else []
            emit("type-alias", name, child, mods, [], first_line(child, src), parent)

        elif t == "enum_declaration":
            if not name:
                return
            mods = ["exported"] if exported else []
            emit("enum", name, child, mods, [], first_line(child, src), parent)

        elif t in ("lexical_declaration", "variable_declaration"):
            is_const = node_text(child, src).lstrip().startswith("const")
            for decl in find_children(child, "variable_declarator"):
                dname = None
                n = find_child(decl, "identifier")
                if n:
                    dname = node_text(n, src)
                if not dname:
                    continue
                init = None
                for c in decl.children:
                    if c.type in (
                        "arrow_function", "function_expression",
                        "generator_function", "async_arrow_function",
                    ):
                        init = c
                        break
                mods = []
                if exported:
                    mods.append("exported")
                if init is not None:
                    body = find_child(init, "statement_block")
                    if any(c.type == "async" for c in init.children) or init.type == "async_arrow_function":
                        mods.append("async")
                    if has_yield(body) or init.type == "generator_function":
                        mods.append("generator")
                    if has_throws(body):
                        mods.append("throws")
                    emit("function", dname, decl, mods, [], signature_of(init) or first_line(decl, src), parent)
                else:
                    if is_const:
                        emit("constant", dname, decl, mods, [], first_line(decl, src), parent)
                    else:
                        emit("variable", dname, decl, mods, [], first_line(decl, src), parent)

    walk(root, parent=None)
    return out


def extract_go(tree, src: bytes, relpath: str, location: str) -> list[Symbol]:
    out: list[Symbol] = []
    root = tree.root_node

    def is_exported(name: str) -> bool:
        return bool(name) and name[0].isupper()

    def emit(kind: str, name: str, node, mods: list[str], shape: list[str],
             signature: str, parent: str | None = None, parent_id: str | None = None):
        q = f"{parent}.{name}" if parent else name
        out.append(Symbol(
            id=f"{relpath}:{q}",
            name=name,
            qualified_name=q,
            file=relpath,
            line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            language="go",
            signature=normalize_signature(signature),
            kind=kind,
            modifiers=sorted(set(mods)),
            shape=sorted(set(shape)),
            location=location,
            parent=parent,
            parent_id=parent_id,
            visibility="public" if is_exported(name) else "private",
        ))

    for child in root.children:
        t = child.type
        if t == "function_declaration":
            name_node = find_child(child, "identifier")
            if not name_node:
                continue
            name = node_text(name_node, src)
            body = find_child(child, "block")
            mods = []
            if is_exported(name):
                mods.append("exported")
            sig = src[child.start_byte:(body.start_byte if body else child.end_byte)].decode("utf-8", errors="replace")
            shape = ["entrypoint"] if name == "main" else []
            emit("function", name, child, mods, shape, sig)

        elif t == "method_declaration":
            name_node = find_child(child, "field_identifier")
            if not name_node:
                continue
            name = node_text(name_node, src)
            recv = find_child(child, "parameter_list")
            recv_text = node_text(recv, src) if recv else ""
            m = re.search(r"\*?(\w+)\s*\)", recv_text)
            parent = m.group(1) if m else None
            parent_id = f"{relpath}:{parent}" if parent else None
            body = find_child(child, "block")
            sig = src[child.start_byte:(body.start_byte if body else child.end_byte)].decode("utf-8", errors="replace")
            mods = []
            if is_exported(name):
                mods.append("exported")
            emit("method", name, child, mods, [], sig, parent=parent, parent_id=parent_id)

        elif t == "type_declaration":
            for spec in find_children(child, "type_spec"):
                name_node = find_child(spec, "type_identifier")
                if not name_node:
                    continue
                name = node_text(name_node, src)
                mods = []
                if is_exported(name):
                    mods.append("exported")
                body = None
                for c in spec.children:
                    if c.type in ("struct_type", "interface_type", "function_type"):
                        body = c
                        break
                if body is None:
                    emit("type-alias", name, spec, mods, [], first_line(spec, src))
                elif body.type == "struct_type":
                    shape = []
                    if ERROR_NAME_RE.search(name):
                        shape.append("error-type")
                    emit("struct", name, spec, mods, shape, first_line(spec, src))
                elif body.type == "interface_type":
                    emit("interface", name, spec, mods, [], first_line(spec, src))
                else:
                    emit("type-alias", name, spec, mods, [], first_line(spec, src))

        elif t == "const_declaration":
            for spec in find_children(child, "const_spec"):
                for id_node in find_children(spec, "identifier"):
                    name = node_text(id_node, src)
                    mods = ["exported"] if is_exported(name) else []
                    emit("constant", name, spec, mods, [], first_line(spec, src))

        elif t == "var_declaration":
            for spec in find_children(child, "var_spec"):
                for id_node in find_children(spec, "identifier"):
                    name = node_text(id_node, src)
                    mods = ["exported"] if is_exported(name) else []
                    emit("variable", name, spec, mods, [], first_line(spec, src))

    return out


def extract_rust(tree, src: bytes, relpath: str, location: str) -> list[Symbol]:
    out: list[Symbol] = []
    root = tree.root_node

    def emit(kind: str, name: str, node, mods: list[str], shape: list[str],
             signature: str, parent: str | None = None, parent_id: str | None = None):
        q = f"{parent}::{name}" if parent else name
        out.append(Symbol(
            id=f"{relpath}:{q}",
            name=name,
            qualified_name=q,
            file=relpath,
            line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            language="rust",
            signature=normalize_signature(signature),
            kind=kind,
            modifiers=sorted(set(mods)),
            shape=sorted(set(shape)),
            location=location,
            parent=parent,
            parent_id=parent_id,
            visibility="public" if "exported" in mods else "private",
        ))

    def is_pub(node) -> bool:
        for c in node.children:
            if c.type == "visibility_modifier":
                return True
        return False

    def get_name(node) -> str | None:
        for t in ("identifier", "type_identifier", "field_identifier"):
            n = find_child(node, t)
            if n:
                return node_text(n, src)
        return None

    def signature_until_body(node) -> str:
        body = find_child(node, "block") or find_child(node, "field_declaration_list") or find_child(node, "declaration_list") or find_child(node, "enum_variant_list")
        end = body.start_byte if body else node.end_byte
        return src[node.start_byte:end].decode("utf-8", errors="replace")

    def walk_items(container, parent: str | None):
        parent_id = f"{relpath}:{parent}" if parent else None
        for child in container.children:
            handle(child, parent, parent_id)

    def handle(child, parent: str | None, parent_id: str | None):
        t = child.type
        if t == "function_item":
            name = get_name(child)
            if not name:
                return
            mods = []
            if is_pub(child):
                mods.append("exported")
            if any(c.type == "async" for c in child.children):
                mods.append("async")
            body = find_child(child, "block")
            if body and body_has_descendant(body, {"try_expression"}):
                mods.append("throws")
            shape = ["entrypoint"] if name == "main" and parent is None else []
            kind = "method" if parent else "function"
            emit(kind, name, child, mods, shape, signature_until_body(child), parent, parent_id)

        elif t == "struct_item":
            name = get_name(child)
            if not name:
                return
            mods = ["exported"] if is_pub(child) else []
            shape = []
            if ERROR_NAME_RE.search(name):
                shape.append("error-type")
            emit("struct", name, child, mods, shape, signature_until_body(child), parent, parent_id)

        elif t == "enum_item":
            name = get_name(child)
            if not name:
                return
            mods = ["exported"] if is_pub(child) else []
            emit("enum", name, child, mods, [], signature_until_body(child), parent, parent_id)

        elif t == "trait_item":
            name = get_name(child)
            if not name:
                return
            mods = ["exported"] if is_pub(child) else []
            emit("interface", name, child, mods, [], signature_until_body(child), parent, parent_id)
            body = find_child(child, "declaration_list")
            if body:
                walk_items(body, name)

        elif t == "impl_item":
            type_node = None
            for c in child.children:
                if c.type == "type_identifier":
                    type_node = c
                    break
                if c.type == "generic_type":
                    inner = find_child(c, "type_identifier")
                    if inner:
                        type_node = inner
                        break
            impl_name = node_text(type_node, src) if type_node else None
            body = find_child(child, "declaration_list")
            if body and impl_name:
                walk_items(body, impl_name)

        elif t == "const_item":
            name = get_name(child)
            if not name:
                return
            mods = ["exported"] if is_pub(child) else []
            emit("constant", name, child, mods, [], first_line(child, src), parent, parent_id)

        elif t == "static_item":
            name = get_name(child)
            if not name:
                return
            mods = ["exported"] if is_pub(child) else []
            emit("variable", name, child, mods, [], first_line(child, src), parent, parent_id)

        elif t == "type_item":
            name = get_name(child)
            if not name:
                return
            mods = ["exported"] if is_pub(child) else []
            emit("type-alias", name, child, mods, [], first_line(child, src), parent, parent_id)

        elif t == "mod_item":
            body = find_child(child, "declaration_list")
            if body:
                walk_items(body, parent)

    walk_items(root, parent=None)
    return out


EXTRACTORS = {
    "python": extract_python,
    "javascript": lambda t, s, r, l: extract_javascript_like(t, s, r, l, "javascript"),
    "typescript": lambda t, s, r, l: extract_javascript_like(t, s, r, l, "typescript"),
    "go": extract_go,
    "rust": extract_rust,
}

# Per-language call-edge and field-I/O extractors. Python is fully supported;
# other languages emit empty lists in this iteration (their symbol extractor
# still runs, preserving v1-compatible inventory data for legacy consumers).
CALL_EDGE_EXTRACTORS = {
    "python": extract_python_call_edges,
}
FIELD_IO_EXTRACTORS = {
    "python": extract_python_field_io,
}


# ---------- call-edge resolution ----------

def resolve_call_edges(edges: list[CallEdge], symbols_by_id: dict[str, Symbol]) -> None:
    """Resolve callee_name → symbol id, using receiver_hint when available."""
    # Build lookup: qualified_name -> list of symbols
    by_qname: dict[str, list[Symbol]] = {}
    by_simple_name: dict[str, list[Symbol]] = {}
    for s in symbols_by_id.values():
        by_qname.setdefault(s.qualified_name, []).append(s)
        by_simple_name.setdefault(s.name, []).append(s)

    def resolve_one(edge: CallEdge):
        name = edge.callee_name
        hint = edge.receiver_hint
        candidates: list[Symbol] = []

        # 1. If receiver_hint is self, prefer methods of the caller's class.
        caller = symbols_by_id.get(edge.caller_id)
        if hint == "self" and caller is not None and caller.parent is not None:
            qn = f"{caller.parent}.{name}"
            if qn in by_qname:
                candidates = by_qname[qn]

        # 2. If receiver_hint looks like a class/type name (starts upper), try Type.name
        if not candidates and hint and hint[:1].isupper():
            qn = f"{hint}.{name}"
            if qn in by_qname:
                candidates = by_qname[qn]

        # 3. Try qualified_name match (module-style name)
        if not candidates and name in by_qname:
            candidates = by_qname[name]

        # 4. Fall back to simple-name match
        if not candidates and name in by_simple_name:
            candidates = by_simple_name[name]

        if len(candidates) == 1:
            edge.resolution = "resolved"
            edge.resolved_callee_id = candidates[0].id
        elif len(candidates) > 1:
            edge.resolution = "ambiguous"
            edge.candidate_ids = [c.id for c in candidates]
        else:
            edge.resolution = "unresolved"

    for edge in edges:
        resolve_one(edge)


# ---------- walker ----------

def iter_files(root: Path, language_filter: set[str] | None, excludes: list[str]):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in IGNORED_DIRS for part in p.parts):
            continue
        ext = p.suffix.lower()
        if ext not in LANGUAGES:
            continue
        lang_pack, handler = LANGUAGES[ext]
        if language_filter and handler not in language_filter:
            continue
        rel = p.relative_to(root).as_posix()
        if any(fnmatch(rel, pat) for pat in excludes):
            continue
        yield p, rel, lang_pack, handler


# ---------- main ----------

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("root", type=Path, help="Repository root to scan")
    ap.add_argument("-o", "--output", type=Path, default=None,
                    help="Output JSON path (default: <root>/clean-room/inventory.json)")
    ap.add_argument("--languages", default=None,
                    help="Comma-separated handler keys: python,typescript,javascript,go,rust")
    ap.add_argument("--exclude", action="append", default=[],
                    help="Glob (relative to root) to skip. Repeatable.")
    ap.add_argument("--strict", action="store_true",
                    help="Fail on vocab validation errors (default: print and continue)")
    ap.add_argument("--no-content-sidecar", action="store_true",
                    help="Skip writing content sidecar files (debug only)")
    args = ap.parse_args()

    if not args.root.is_dir():
        print(f"not a directory: {args.root}", file=sys.stderr)
        return 2

    vocab = load_vocab()
    lang_filter = set(args.languages.split(",")) if args.languages else None
    output = args.output or (args.root / "clean-room" / "inventory.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    sidecar_dir = output.parent / "content"

    parsers: dict[str, object] = {}
    def parser_for(lang_pack: str):
        if lang_pack not in parsers:
            parsers[lang_pack] = get_parser(lang_pack)
        return parsers[lang_pack]

    symbols: list[Symbol] = []
    call_edges: list[CallEdge] = []
    field_ios: list[FieldIO] = []
    files_scanned = 0
    lang_counts: dict[str, int] = {}
    errors: list[str] = []
    content_sidecars: dict[str, str] = {}  # sha -> raw text
    t0 = time.time()

    # First pass: trees + symbols (we cache trees for the second pass per-file).
    file_trees: list[tuple[Path, str, str, str, object, bytes, str]] = []
    # (path, rel, lang_pack, handler, tree, src, location)

    for path, rel, lang_pack, handler in iter_files(args.root, lang_filter, args.exclude):
        try:
            src = path.read_bytes()
        except Exception as e:
            errors.append(f"{rel}: read failed: {e}")
            continue
        try:
            tree = parser_for(lang_pack).parse(src)
        except Exception as e:
            errors.append(f"{rel}: parse failed: {e}")
            continue
        location = classify_location(rel)
        extractor = EXTRACTORS[handler]
        try:
            syms = extractor(tree, src, rel, location)
        except Exception as e:
            errors.append(f"{rel}: extract failed: {e}")
            continue

        # Collect any content-sidecar payload the Python extractor stashed.
        pending = getattr(extract_python, "_pending_content", None)
        if pending and handler == "python":
            for sid, raw in list(pending.items()):
                # Find sym and link
                for s in syms:
                    if s.id == sid and s.content_snapshot is not None:
                        content_sidecars[s.content_snapshot["sha256"]] = raw
                        break
            pending.clear()

        symbols.extend(syms)
        files_scanned += 1
        lang_counts[handler] = lang_counts.get(handler, 0) + 1
        file_trees.append((path, rel, lang_pack, handler, tree, src, location))

    # Build symbol index for call-edge + field-I/O resolution.
    symbols_by_id = {s.id: s for s in symbols}

    # Second pass: call-edges and field-I/O (languages that support it).
    for (_path, rel, _lang_pack, handler, tree, src, _location) in file_trees:
        if handler in CALL_EDGE_EXTRACTORS:
            try:
                edges = CALL_EDGE_EXTRACTORS[handler](tree, src, rel, symbols_by_id)
                call_edges.extend(edges)
            except Exception as e:
                errors.append(f"{rel}: call-edge extract failed: {e}")
        if handler in FIELD_IO_EXTRACTORS:
            try:
                ios = FIELD_IO_EXTRACTORS[handler](tree, src, rel, symbols_by_id)
                field_ios.extend(ios)
            except Exception as e:
                errors.append(f"{rel}: field-io extract failed: {e}")

    # Resolve call-edges against the symbol table.
    resolve_call_edges(call_edges, symbols_by_id)

    # Validate symbols.
    validation_errors: list[str] = []
    for s in symbols:
        validation_errors.extend(validate_symbol(s, vocab))
    if validation_errors:
        if args.strict:
            print("vocabulary validation failed:", file=sys.stderr)
            for e in validation_errors[:50]:
                print(f"  {e}", file=sys.stderr)
            return 2
        else:
            for e in validation_errors[:20]:
                print(f"warn: {e}", file=sys.stderr)

    # Sort for determinism.
    symbols.sort(key=lambda s: (s.file, s.line, s.id))
    call_edges.sort(key=lambda e: (e.file, e.line, e.id))
    field_ios.sort(key=lambda io: (io.file, io.line, io.id))

    # Write content sidecars.
    if not args.no_content_sidecar:
        for sha, raw in content_sidecars.items():
            write_content_sidecar(sidecar_dir, {"sha256": sha}, raw)

    doc = {
        "schema_version": SCHEMA_VERSION,
        "root": str(args.root.resolve()),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "vocab_version": vocab["version"],
        "stats": {
            "files_scanned": files_scanned,
            "symbols_found": len(symbols),
            "call_edges_found": len(call_edges),
            "field_io_found": len(field_ios),
            "languages": lang_counts,
            "elapsed_seconds": round(time.time() - t0, 2),
            "read_errors": len(errors),
        },
        "errors": errors,
        "symbols": [asdict(s) for s in symbols],
        "call_edges": [asdict(e) for e in call_edges],
        "field_io": [asdict(io) for io in field_ios],
    }
    output.write_text(json.dumps(doc, indent=2, sort_keys=False), encoding="utf-8")
    print(
        f"wrote {output} (schema v{SCHEMA_VERSION}) — "
        f"{len(symbols)} symbols, {len(call_edges)} call_edges, {len(field_ios)} field_io "
        f"across {files_scanned} files "
        f"({', '.join(f'{k}:{v}' for k, v in sorted(lang_counts.items()))})"
    )
    if errors:
        print(f"  {len(errors)} file error(s); see 'errors' array in JSON", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""The shape of graph.json: seventeen types over five layouts.

A diagram is decided here, before any syntax exists. Everything downstream --
Mermaid, draw.io, the budget -- reads this file's vocabulary, so a typo in a
role or an edge kind is caught once, in one place, and never reaches a
renderer as a silently empty shape.

stdlib only.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,39}$")

LAYOUTS = ("layered", "container", "table", "lifeline", "timeline")
DETAIL = ("minimal", "normal", "deep")
AUDIENCE = ("engineer", "management")

CARDINALITIES = ("1-1", "1-n", "n-1", "n-n")


@dataclass(frozen=True)
class TypeSpec:
    """What one diagram type is allowed to contain."""

    layout: str
    wave: int
    roles: frozenset = field(default_factory=frozenset)
    edge_kinds: frozenset = field(default_factory=frozenset)
    relation_style: str = ""  # "cardinality" | "kind" | ""
    relation_kinds: frozenset = field(default_factory=frozenset)


def _rs(*names: str) -> frozenset:
    return frozenset(names)


_FLOW_KINDS = _rs("flow", "request", "response", "async", "dep", "trigger")
CLASS_RELATIONS = _rs("inherit", "implement", "compose", "aggregate", "assoc", "dep")
REQ_RELATIONS = _rs("satisfies", "verifies", "derives", "refines", "traces")

TYPES: dict[str, TypeSpec] = {
    # --- wave 1 ----------------------------------------------------------
    "architecture": TypeSpec(
        layout="layered",
        wave=1,
        roles=_rs("service", "component", "store", "queue", "external", "actor"),
        edge_kinds=_FLOW_KINDS,
    ),
    "sequence": TypeSpec(
        layout="lifeline",
        wave=1,
        roles=_rs("actor", "participant", "store", "external", "boundary"),
        edge_kinds=_rs("request", "response", "async", "self", "create", "destroy"),
    ),
    "state": TypeSpec(
        layout="layered",
        wave=1,
        roles=_rs("state", "start", "end", "choice"),
        edge_kinds=_rs("transition"),
    ),
    "data-model": TypeSpec(
        layout="table",
        wave=1,
        relation_style="cardinality",
    ),
    "flowchart": TypeSpec(
        layout="layered",
        wave=1,
        roles=_rs("start", "end", "process", "decision", "io", "subroutine"),
        edge_kinds=_rs("flow"),
    ),
    "class": TypeSpec(
        layout="table",
        wave=1,
        relation_style="kind",
        relation_kinds=CLASS_RELATIONS,
    ),
    # --- wave 2 ----------------------------------------------------------
    "deployment": TypeSpec(
        layout="container",
        wave=2,
        roles=_rs("service", "component", "store", "queue", "external", "actor", "host"),
        edge_kinds=_FLOW_KINDS,
    ),
    "swimlane": TypeSpec(
        layout="container",
        wave=2,
        roles=_rs("start", "end", "process", "decision", "io", "subroutine"),
        edge_kinds=_rs("flow"),
    ),
    "dfd": TypeSpec(
        layout="container",
        wave=2,
        roles=_rs("process", "store", "external", "actor"),
        edge_kinds=_rs("flow", "read", "write"),
    ),
    "db-schema": TypeSpec(
        layout="table",
        wave=2,
        relation_style="cardinality",
    ),
    "c4": TypeSpec(
        layout="container",
        wave=2,
        roles=_rs("person", "system", "container", "component", "external", "store"),
        edge_kinds=_FLOW_KINDS,
    ),
    # --- wave 3 ----------------------------------------------------------
    "cicd": TypeSpec(
        layout="layered",
        wave=3,
        roles=_rs("start", "end", "job", "gate", "artifact", "environment"),
        edge_kinds=_rs("flow", "trigger"),
    ),
    "threat-model": TypeSpec(
        layout="container",
        wave=3,
        roles=_rs("process", "store", "external", "actor", "threat"),
        edge_kinds=_rs("request", "response", "flow"),
    ),
    "git-graph": TypeSpec(layout="timeline", wave=3),
    "gantt": TypeSpec(layout="timeline", wave=3),
    "user-journey": TypeSpec(layout="timeline", wave=3),
    "requirements": TypeSpec(
        layout="table",
        wave=3,
        relation_style="kind",
        relation_kinds=REQ_RELATIONS,
    ),
}

GROUP_KINDS = _rs("group", "lane", "boundary", "trust", "system", "node")
ROW_KEYS = _rs("pk", "fk", "uk")
ROW_KINDS = _rs("field", "method")
VISIBILITY = _rs("+", "-", "#", "~")
FRAGMENTS = _rs("alt", "opt", "loop", "par")
SPAN_KINDS = _rs("task", "milestone", "commit", "merge", "branch", "step")


# ---------------------------------------------------------------------------
# validation helpers -- every one appends to a flat list of messages
# ---------------------------------------------------------------------------


def _keys(obj: dict, path: str, required: tuple, optional: tuple, errors: list) -> None:
    for k in required:
        if k not in obj:
            errors.append(f"{path}: missing required key {k!r}")
    allowed = set(required) | set(optional)
    for k in obj:
        if k not in allowed:
            errors.append(f"{path}: unknown key {k!r}")


def _str(obj: dict, key: str, path: str, errors: list, *, allow_empty: bool = False) -> None:
    if key not in obj or obj[key] is None:
        return
    v = obj[key]
    if not isinstance(v, str):
        errors.append(f"{path}.{key}: must be a string, got {type(v).__name__}")
    elif not allow_empty and not v.strip():
        errors.append(f"{path}.{key}: must not be empty")


def _enum(obj: dict, key: str, allowed, path: str, errors: list) -> None:
    if key not in obj or obj[key] is None:
        return
    if obj[key] not in allowed:
        errors.append(f"{path}.{key}: {obj[key]!r} is not one of {sorted(allowed)}")


def _ident(obj: dict, key: str, path: str, errors: list) -> None:
    if key not in obj:
        return
    v = obj[key]
    if not isinstance(v, str) or not ID_RE.match(v):
        errors.append(
            f"{path}.{key}: {v!r} is not a valid id "
            "(letter or underscore first, then letters, digits, underscores, max 40)"
        )


def _list_of_dicts(payload: dict, key: str, path: str, errors: list) -> list:
    v = payload.get(key)
    if not isinstance(v, list):
        errors.append(f"{path}.{key}: must be a list")
        return []
    out = []
    for i, item in enumerate(v):
        if not isinstance(item, dict):
            errors.append(f"{path}.{key}[{i}]: must be an object")
        else:
            out.append(item)
    return out


def _collect_ids(items: list, key: str, path: str, errors: list) -> set:
    seen: set = set()
    for i, item in enumerate(items):
        _ident(item, key, f"{path}[{i}]", errors)
        raw = item.get(key)
        if isinstance(raw, str):
            if raw in seen:
                errors.append(f"{path}[{i}].{key}: duplicate id {raw!r}")
            seen.add(raw)
    return seen


def _ref(item: dict, key: str, known: set, path: str, errors: list) -> None:
    v = item.get(key)
    if not isinstance(v, str):
        errors.append(f"{path}.{key}: must be an id string")
    elif v not in known:
        errors.append(f"{path}.{key}: {v!r} does not name anything in this diagram")


def _cycle_check(graph: dict, path: str, key: str, errors: list) -> None:
    """Depth-first cycle detection over a small adjacency map."""
    WHITE, GREY, BLACK = 0, 1, 2
    colour: dict = {}

    def walk(node, trail):
        state = colour.get(node, WHITE)
        if state == BLACK:
            return
        if state == GREY:
            loop = " -> ".join(trail[trail.index(node) :] + [node])
            errors.append(f"{path}: {key!r} forms a cycle: {loop}")
            return
        colour[node] = GREY
        for nxt in graph.get(node, ()):
            walk(nxt, trail + [node])
        colour[node] = BLACK

    for n in list(graph):
        walk(n, [])


# ---------------------------------------------------------------------------
# payload validators, one per layout
# ---------------------------------------------------------------------------


def _nodes_and_edges(payload: dict, spec: TypeSpec, errors: list) -> set:
    nodes = _list_of_dicts(payload, "nodes", "payload", errors)
    for i, n in enumerate(nodes):
        p = f"payload.nodes[{i}]"
        _keys(n, p, ("id", "label"), ("role", "tier", "note"), errors)
        _str(n, "label", p, errors)
        _str(n, "note", p, errors)
        _enum(n, "role", spec.roles, p, errors)
        if "tier" in n and not isinstance(n["tier"], int):
            errors.append(f"{p}.tier: must be an integer")
    ids = _collect_ids(nodes, "id", "payload.nodes", errors)

    edges = _list_of_dicts(payload, "edges", "payload", errors)
    for i, e in enumerate(edges):
        p = f"payload.edges[{i}]"
        _keys(e, p, ("from", "to"), ("label", "kind", "note"), errors)
        _str(e, "label", p, errors)
        _enum(e, "kind", spec.edge_kinds, p, errors)
        _ref(e, "from", ids, p, errors)
        _ref(e, "to", ids, p, errors)
    return ids


def validate_layered(payload: dict, spec: TypeSpec, errors: list) -> None:
    _keys(payload, "payload", ("nodes", "edges"), (), errors)
    _nodes_and_edges(payload, spec, errors)


def validate_container(payload: dict, spec: TypeSpec, errors: list) -> None:
    _keys(payload, "payload", ("nodes", "edges", "groups"), (), errors)
    node_ids = _nodes_and_edges(payload, spec, errors)

    groups = _list_of_dicts(payload, "groups", "payload", errors)
    for i, g in enumerate(groups):
        p = f"payload.groups[{i}]"
        _keys(g, p, ("id", "label", "members"), ("kind", "parent", "note"), errors)
        _str(g, "label", p, errors)
        _enum(g, "kind", GROUP_KINDS, p, errors)
    group_ids = _collect_ids(groups, "id", "payload.groups", errors)

    claimed: dict = {}
    for i, g in enumerate(groups):
        p = f"payload.groups[{i}]"
        if g.get("parent") is not None:
            _ref(g, "parent", group_ids, p, errors)
            if g.get("parent") == g.get("id"):
                errors.append(f"{p}.parent: a group cannot contain itself")
        members = g.get("members")
        if not isinstance(members, list):
            errors.append(f"{p}.members: must be a list of node ids")
            continue
        for j, m in enumerate(members):
            mp = f"{p}.members[{j}]"
            if not isinstance(m, str) or m not in node_ids:
                errors.append(f"{mp}: {m!r} does not name a node in this diagram")
            elif m in claimed:
                errors.append(f"{mp}: node {m!r} is already inside group {claimed[m]!r}")
            else:
                claimed[m] = g.get("id")

    parents = {
        g["id"]: [g["parent"]]
        for g in groups
        if isinstance(g.get("id"), str) and isinstance(g.get("parent"), str)
    }
    _cycle_check(parents, "payload.groups", "parent", errors)


def validate_table(payload: dict, spec: TypeSpec, errors: list) -> None:
    _keys(payload, "payload", ("entities", "relations"), (), errors)
    entities = _list_of_dicts(payload, "entities", "payload", errors)
    for i, e in enumerate(entities):
        p = f"payload.entities[{i}]"
        _keys(e, p, ("id", "label", "rows"), ("stereotype", "note"), errors)
        _str(e, "label", p, errors)
        _str(e, "stereotype", p, errors)
        rows = e.get("rows")
        if not isinstance(rows, list):
            errors.append(f"{p}.rows: must be a list")
            continue
        for j, r in enumerate(rows):
            rp = f"{p}.rows[{j}]"
            if not isinstance(r, dict):
                errors.append(f"{rp}: must be an object")
                continue
            _keys(r, rp, ("name",), ("type", "key", "kind", "visibility", "note"), errors)
            _str(r, "name", rp, errors)
            _str(r, "type", rp, errors)
            _enum(r, "key", ROW_KEYS, rp, errors)
            _enum(r, "kind", ROW_KINDS, rp, errors)
            _enum(r, "visibility", VISIBILITY, rp, errors)
    ids = _collect_ids(entities, "id", "payload.entities", errors)

    relations = _list_of_dicts(payload, "relations", "payload", errors)
    for i, r in enumerate(relations):
        p = f"payload.relations[{i}]"
        _keys(r, p, ("from", "to"), ("label", "kind", "cardinality", "optional"), errors)
        _str(r, "label", p, errors)
        _ref(r, "from", ids, p, errors)
        _ref(r, "to", ids, p, errors)
        if "optional" in r and not isinstance(r["optional"], bool):
            errors.append(f"{p}.optional: must be true or false")
        if spec.relation_style == "cardinality":
            if "cardinality" not in r:
                errors.append(f"{p}: missing 'cardinality', required for this type")
            _enum(r, "cardinality", CARDINALITIES, p, errors)
            if "kind" in r:
                errors.append(f"{p}: 'kind' does not apply here, use 'cardinality'")
        else:
            if "kind" not in r:
                errors.append(f"{p}: missing 'kind', required for this type")
            _enum(r, "kind", spec.relation_kinds, p, errors)
            if "cardinality" in r:
                errors.append(f"{p}: 'cardinality' does not apply here, use 'kind'")


def validate_lifeline(payload: dict, spec: TypeSpec, errors: list) -> None:
    _keys(payload, "payload", ("actors", "messages"), ("fragments",), errors)
    actors = _list_of_dicts(payload, "actors", "payload", errors)
    for i, a in enumerate(actors):
        p = f"payload.actors[{i}]"
        _keys(a, p, ("id", "label"), ("kind", "note"), errors)
        _str(a, "label", p, errors)
        _enum(a, "kind", spec.roles, p, errors)
    ids = _collect_ids(actors, "id", "payload.actors", errors)

    messages = _list_of_dicts(payload, "messages", "payload", errors)
    for i, m in enumerate(messages):
        p = f"payload.messages[{i}]"
        _keys(m, p, ("from", "to", "label"), ("kind", "note"), errors)
        _str(m, "label", p, errors)
        _enum(m, "kind", spec.edge_kinds, p, errors)
        _ref(m, "from", ids, p, errors)
        _ref(m, "to", ids, p, errors)
        if m.get("kind") == "self" and m.get("from") != m.get("to"):
            errors.append(f"{p}: kind 'self' but 'from' and 'to' name different actors")

    fragments = payload.get("fragments")
    if fragments is None:
        return
    if not isinstance(fragments, list):
        errors.append("payload.fragments: must be a list")
        return
    for i, f in enumerate(fragments):
        p = f"payload.fragments[{i}]"
        if not isinstance(f, dict):
            errors.append(f"{p}: must be an object")
            continue
        _keys(f, p, ("kind", "label", "start", "end"), (), errors)
        _enum(f, "kind", FRAGMENTS, p, errors)
        _str(f, "label", p, errors)
        start, end = f.get("start"), f.get("end")
        for name, v in (("start", start), ("end", end)):
            if not isinstance(v, int) or isinstance(v, bool):
                errors.append(f"{p}.{name}: must be a message index, an integer")
            elif not 0 <= v < len(messages):
                errors.append(f"{p}.{name}: index {v} is outside the message list")
        if isinstance(start, int) and isinstance(end, int) and start > end:
            errors.append(f"{p}: start {start} comes after end {end}")


def validate_timeline(payload: dict, spec: TypeSpec, errors: list, graph_type: str = "") -> None:
    _keys(payload, "payload", ("tracks", "spans"), (), errors)
    tracks = _list_of_dicts(payload, "tracks", "payload", errors)
    for i, t in enumerate(tracks):
        p = f"payload.tracks[{i}]"
        _keys(t, p, ("id", "label"), ("note",), errors)
        _str(t, "label", p, errors)
    track_ids = _collect_ids(tracks, "id", "payload.tracks", errors)

    spans = _list_of_dicts(payload, "spans", "payload", errors)
    for i, s in enumerate(spans):
        p = f"payload.spans[{i}]"
        _keys(
            s,
            p,
            ("id", "track", "label", "start"),
            ("end", "kind", "depends_on", "note", "score"),
            errors,
        )
        _str(s, "label", p, errors)
        _str(s, "start", p, errors)
        _str(s, "end", p, errors)
        _enum(s, "kind", SPAN_KINDS, p, errors)
        _ref(s, "track", track_ids, p, errors)
        score = s.get("score")
        if score is not None:
            if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 5:
                errors.append(f"{p}.score: must be a whole number from 0 to 5")
            elif graph_type != "user-journey":
                errors.append(f"{p}.score: only type 'user-journey' takes a score")
    span_ids = _collect_ids(spans, "id", "payload.spans", errors)

    deps: dict = {}
    for i, s in enumerate(spans):
        p = f"payload.spans[{i}]"
        dep = s.get("depends_on")
        if dep is None:
            continue
        if not isinstance(dep, list):
            errors.append(f"{p}.depends_on: must be a list of span ids")
            continue
        for j, d in enumerate(dep):
            if not isinstance(d, str) or d not in span_ids:
                errors.append(f"{p}.depends_on[{j}]: {d!r} does not name a span")
        if isinstance(s.get("id"), str):
            deps[s["id"]] = [d for d in dep if isinstance(d, str) and d in span_ids]
    _cycle_check(deps, "payload.spans", "depends_on", errors)


_PAYLOAD_VALIDATORS = {
    "layered": validate_layered,
    "container": validate_container,
    "table": validate_table,
    "lifeline": validate_lifeline,
    "timeline": validate_timeline,
}


# ---------------------------------------------------------------------------
# entry points
# ---------------------------------------------------------------------------


def validate_meta(meta: dict, graph_type, errors: list) -> None:
    _keys(
        meta,
        "meta",
        ("title", "scope", "detail", "audience"),
        ("dropped", "budget_override", "level", "note"),
        errors,
    )
    _str(meta, "title", "meta", errors)
    _str(meta, "scope", "meta", errors)
    _enum(meta, "detail", DETAIL, "meta", errors)
    _enum(meta, "audience", AUDIENCE, "meta", errors)

    dropped = meta.get("dropped")
    if dropped is not None:
        if not isinstance(dropped, list):
            errors.append("meta.dropped: must be a list")
        else:
            for i, d in enumerate(dropped):
                p = f"meta.dropped[{i}]"
                if not isinstance(d, dict):
                    errors.append(f"{p}: must be an object")
                    continue
                _keys(d, p, ("what", "why"), (), errors)
                _str(d, "what", p, errors)
                _str(d, "why", p, errors)

    override = meta.get("budget_override")
    if override is not None:
        if not isinstance(override, dict):
            errors.append("meta.budget_override: must be null, or an object with a reason")
        else:
            _keys(override, "meta.budget_override", ("reason",), (), errors)
            _str(override, "reason", "meta.budget_override", errors)

    if graph_type == "c4":
        level = meta.get("level")
        if not isinstance(level, int) or isinstance(level, bool) or not 1 <= level <= 4:
            errors.append("meta.level: type 'c4' needs a level from 1 to 4")
    elif "level" in meta:
        errors.append("meta.level: only type 'c4' takes a level")


def validate(graph: object) -> list:
    """Structural check of a whole graph.json.

    Returns a list of messages; an empty list means the shape is sound.
    Budget lives in budget.py and escaping in escape.py -- this is shape only.
    """
    errors: list = []
    if not isinstance(graph, dict):
        return ["root: graph.json must be a JSON object"]

    _keys(graph, "root", ("type", "layout", "meta", "payload"), (), errors)

    graph_type = graph.get("type")
    spec = TYPES.get(graph_type) if isinstance(graph_type, str) else None
    if spec is None:
        errors.append(f"type: {graph_type!r} is not a known type ({', '.join(sorted(TYPES))})")
    else:
        layout = graph.get("layout")
        if layout != spec.layout:
            errors.append(
                f"layout: type {graph_type!r} uses layout {spec.layout!r}, got {layout!r}"
            )

    meta = graph.get("meta")
    if not isinstance(meta, dict):
        errors.append("meta: must be an object")
    else:
        validate_meta(meta, graph_type, errors)

    payload = graph.get("payload")
    if not isinstance(payload, dict):
        errors.append("payload: must be an object")
    elif spec is not None:
        if spec.layout == "timeline":
            validate_timeline(payload, spec, errors, graph_type or "")
        else:
            _PAYLOAD_VALIDATORS[spec.layout](payload, spec, errors)

    return errors


def load(path) -> dict:
    """Read graph.json from disk.

    Raises ValueError with a readable message rather than a traceback: a
    person reads this output.
    """
    p = Path(path)
    try:
        raw = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read {p}: {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{p} is not valid JSON: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

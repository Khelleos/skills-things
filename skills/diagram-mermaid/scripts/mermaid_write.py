"""graph.json -> Mermaid.

The agent never writes Mermaid by hand. It decides what the diagram says, in
graph.json, and this turns that into syntax. Three things follow from doing it
this way: the syntax cannot be got wrong, escaping happens in exactly one
place, and the same intent always produces the same file.

All seventeen types:

    architecture, flowchart, cicd            -> flowchart TD
    deployment, swimlane, dfd, c4, threat    -> flowchart TD + subgraph
    state                                    -> stateDiagram-v2
    sequence                                 -> sequenceDiagram
    data-model, db-schema                    -> erDiagram
    class, requirements                      -> classDiagram
    gantt                                    -> gantt
    user-journey                             -> journey
    git-graph                                -> gitGraph

What Mermaid spends its vocabulary on, one convention for every type that
uses it:

    solid arrow   -->    flow, request
    dotted arrow  -.->   response, dep
    circle end    --o    async: sent, no reply awaited
    thick arrow   ==>    trigger

Usage:
    python mermaid_write.py <graph.json> [-o out.mmd] [--fence] [--no-header]

Exit code 2 when the graph does not validate: nothing is written, because a
diagram generated from a broken intent is worse than no diagram.

stdlib only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SKILLS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_SKILLS / "_shared"))
sys.path.insert(0, str(_SKILLS / "validate"))

import escape  # noqa: E402
import schema  # noqa: E402
from validate_graph import validate_graph  # noqa: E402

INDENT = "    "
QUOTE = chr(34)

# The timeline axis is ordered the same way in both formats. layouts.py owns
# that rule; this borrows it rather than keeping a second copy that can drift.
sys.path.insert(0, str(_SKILLS / "diagram-drawio" / "scripts"))
from layouts import _axis_key as _AXIS_KEY  # noqa: E402

#: Words Mermaid reads as syntax wherever they appear as a bare id. 'end' is
#: the notorious one: it closes a subgraph and silently breaks the diagram.
RESERVED = {
    "end", "graph", "subgraph", "flowchart", "style", "class", "classdef",
    "click", "linkstyle", "direction", "state", "note", "call", "href",
    "o", "x", "v",
}

#: role -> the two halves of a Mermaid flowchart node shape.
SHAPES = {
    "service": ("[", "]"),
    "component": ("(", ")"),
    "store": ("[(", ")]"),
    "queue": ("[/", "/]"),
    "external": ("{{", "}}"),
    "actor": ("((", "))"),
    "start": ("([", "])"),
    "end": ("([", "])"),
    "process": ("[", "]"),
    "decision": ("{", "}"),
    "io": ("[/", "/]"),
    "subroutine": ("[[", "]]"),
    "job": ("[", "]"),
    "gate": ("{", "}"),
    "artifact": ("[(", ")]"),
    "environment": ("[[", "]]"),
}
DEFAULT_SHAPE = ("[", "]")

ARROWS = {
    "flow": "-->",
    "request": "-->",
    "response": "-.->",
    "dep": "-.->",
    "async": "--o",
    "trigger": "==>",
    "transition": "-->",
    "read": "-.->",
    "write": "-->",
}
DEFAULT_ARROW = "-->"

MESSAGES = {
    "request": "->>",
    "response": "-->>",
    "async": "-)",
    "self": "->>",
    "create": "->>",
    "destroy": "--x",
}
DEFAULT_MESSAGE = "->>"

#: cardinality -> (left, right) Mermaid ER connector halves, in the
#: (required, optional) pair the 'optional' flag chooses between.
ER_LEFT = {
    "1-1": ("||", "||"),
    "1-n": ("||", "||"),
    "n-1": ("}|", "}o"),
    "n-n": ("}|", "}o"),
}
ER_RIGHT = {
    "1-1": ("||", "o|"),
    "1-n": ("|{", "o{"),
    "n-1": ("||", "o|"),
    "n-n": ("|{", "o{"),
}

#: A requirements relation has no UML arrow of its own, so it borrows the
#: dependency arrow and says which kind it is in the label.
REQUIREMENT_RELATIONS = ("satisfies", "verifies", "derives", "refines", "traces")

CLASS_RELATIONS = {
    "inherit": "--|>",
    "implement": "..|>",
    "compose": "*--",
    "aggregate": "o--",
    "assoc": "-->",
    "dep": "..>",
}


class GenerationError(Exception):
    """Raised when the graph is sound but this format cannot carry it."""


# ---------------------------------------------------------------------------
# shared bits
# ---------------------------------------------------------------------------


def safe_id(raw: str) -> str:
    """Node ids are already identifiers by schema. This only steps around the
    handful of words Mermaid claims for itself."""
    return raw + "_" if raw.lower() in RESERVED else raw


def _yaml_quote(text: str) -> str:
    return '"' + escape.normalize(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def header(graph: dict) -> list:
    """Front matter with the title, then the settings and the loss report as
    comments. Comments cost nothing to render and make the file explain itself
    in a diff."""
    meta = graph.get("meta") or {}
    lines = ["---", f"title: {_yaml_quote(meta.get('title', ''))}", "---"]
    lines.append(
        f"%% scope: {escape.normalize(meta.get('scope', ''))}"
        f" | detail: {meta.get('detail')} | audience: {meta.get('audience')}"
    )
    for d in meta.get("dropped") or []:
        lines.append(f"%% dropped: {escape.normalize(d.get('what'))} - {escape.normalize(d.get('why'))}")
    override = (meta.get("budget_override") or {}).get("reason") if meta.get("budget_override") else None
    if override:
        lines.append(f"%% over budget on purpose: {escape.normalize(override)}")
    return lines


def _index(items, key="id") -> dict:
    return {item[key]: item for item in items if isinstance(item, dict) and key in item}


def _unique_names(items, fallback: str) -> dict:
    """id -> a display name that is a bare identifier and unique.

    Mermaid ER and class diagrams name a box with an identifier, not with free
    text, so 'Order line' has to become 'Order_line'. Two labels can collapse
    onto the same identifier; the second one gets a suffix rather than
    silently merging into the first.
    """
    names: dict = {}
    taken: set = set()
    for item in items:
        base = escape.identifier(item.get("label") or item.get("id"), fallback)
        name, n = base, 2
        while name in taken:
            name, n = f"{base}_{n}", n + 1
        taken.add(name)
        names[item["id"]] = name
    return names


# ---------------------------------------------------------------------------
# one writer per Mermaid diagram kind
# ---------------------------------------------------------------------------


def _leftover_notes(entities: list, names: dict) -> list:
    """Notes neither erDiagram nor classDiagram can draw.

    An ER block has no comment line and a class has no per-member comment, so
    these would vanish without a trace. They come out as %% comments instead:
    a reader of the file keeps them, and nothing is silently lost.
    """
    lines: list = []
    for entity in entities:
        name = names[entity["id"]]
        if entity.get("note"):
            lines.append(f"%% {name}: {escape.mermaid_plain(entity['note'])}")
        for row in entity.get("rows") or []:
            if row.get("note"):
                row_name = escape.mermaid_plain(row["name"])
                lines.append(f"%% {name}.{row_name}: {escape.mermaid_plain(row['note'])}")
    return [""] + lines if lines else []


def declare(node: dict, depth: int = 1) -> str:
    """One node declaration, shaped by its role."""
    open_, close = SHAPES.get(node.get("role"), DEFAULT_SHAPE)
    label = escape.mermaid_quoted(node["label"])
    return f"{INDENT * depth}{safe_id(node['id'])}{open_}{label}{close}"


def write_flowchart(graph: dict) -> list:
    payload = graph["payload"]
    nodes = list(payload.get("nodes") or [])
    lines = ["flowchart TD"]

    # Mermaid lays the graph out itself, but it does respect declaration
    # order, so declaring by tier nudges it towards the intended layering.
    for node in sorted(nodes, key=lambda n: (n.get("tier") is None, n.get("tier") or 0)):
        lines.append(declare(node, 1))

    lines.append("")
    for edge in payload.get("edges") or []:
        arrow = ARROWS.get(edge.get("kind"), DEFAULT_ARROW)
        label = edge.get("label")
        mid = f"|{escape.mermaid_quoted(label)}|" if label else ""
        lines.append(f"{INDENT}{safe_id(edge['from'])} {arrow}{mid} {safe_id(edge['to'])}")

    notes = [(n["id"], n["note"]) for n in nodes if n.get("note")]
    if notes:
        lines.append("")
        for node_id, note in notes:
            lines.append(f"%% {safe_id(node_id)}: {escape.mermaid_plain(note)}")
    return lines


def write_state(graph: dict) -> list:
    payload = graph["payload"]
    nodes = _index(payload.get("nodes") or [])
    lines = ["stateDiagram-v2"]

    def ref(node_id: str) -> str:
        role = nodes.get(node_id, {}).get("role")
        return "[*]" if role in ("start", "end") else safe_id(node_id)

    for node in payload.get("nodes") or []:
        role = node.get("role")
        if role in ("start", "end"):
            continue  # both are [*] in Mermaid, they get no declaration
        name = safe_id(node["id"])
        if role == "choice":
            lines.append(f"{INDENT}state {name} <<choice>>")
        elif escape.normalize(node["label"]) != node["id"]:
            caption = escape.mermaid_plain(node["label"])
            lines.append(f'{INDENT}state "{caption}" as {name}')

    lines.append("")
    for edge in payload.get("edges") or []:
        label = edge.get("label")
        tail = f" : {escape.mermaid_plain(label)}" if label else ""
        lines.append(f"{INDENT}{ref(edge['from'])} --> {ref(edge['to'])}{tail}")

    for node in payload.get("nodes") or []:
        if node.get("note") and node.get("role") not in ("start", "end"):
            lines.append("")
            lines.append(f"{INDENT}note right of {safe_id(node['id'])}")
            lines.append(f"{INDENT}{INDENT}{escape.mermaid_plain(node['note'])}")
            lines.append(f"{INDENT}end note")
    return lines


def write_sequence(graph: dict) -> list:
    payload = graph["payload"]
    actors = list(payload.get("actors") or [])
    messages = list(payload.get("messages") or [])
    fragments = list(payload.get("fragments") or [])

    # A participant that a 'create' message brings into being must not be
    # declared up front, or Mermaid draws it standing there from the start.
    created = {m["to"] for m in messages if m.get("kind") == "create"}

    lines = ["sequenceDiagram", f"{INDENT}autonumber"]
    for actor in actors:
        if actor["id"] in created:
            continue
        keyword = "actor" if actor.get("kind") == "actor" else "participant"
        lines.append(f"{INDENT}{keyword} {safe_id(actor['id'])} as {escape.mermaid_plain(actor['label'])}")

    lines.append("")

    opens: dict = {}
    closes: dict = {}
    for frag in fragments:
        opens.setdefault(frag["start"], []).append(frag)
        closes.setdefault(frag["end"], []).append(frag)

    by_id = _index(actors)
    depth = 0
    for i, message in enumerate(messages):
        for frag in opens.get(i, []):
            lines.append(
                f"{INDENT}{INDENT * depth}{frag['kind']} {escape.mermaid_plain(frag['label'])}"
            )
            depth += 1

        pad = INDENT + INDENT * depth
        kind = message.get("kind")
        target = safe_id(message["to"])

        if kind == "create":
            actor = by_id.get(message["to"], {})
            keyword = "actor" if actor.get("kind") == "actor" else "participant"
            label = escape.mermaid_plain(actor.get("label", message["to"]))
            lines.append(f"{pad}create {keyword} {target} as {label}")
        elif kind == "destroy":
            lines.append(f"{pad}destroy {target}")

        arrow = MESSAGES.get(kind, DEFAULT_MESSAGE)
        lines.append(
            f"{pad}{safe_id(message['from'])}{arrow}{target}: {escape.mermaid_plain(message['label'])}"
        )
        if message.get("note"):
            over = safe_id(message["from"])
            if message["from"] != message["to"]:
                over += f",{target}"
            lines.append(f"{pad}Note over {over}: {escape.mermaid_plain(message['note'])}")

        for _ in closes.get(i, []):
            depth -= 1
            lines.append(f"{INDENT}{INDENT * depth}end")
    return lines


def write_er(graph: dict) -> list:
    payload = graph["payload"]
    entities = list(payload.get("entities") or [])
    names = _unique_names(entities, "entity")
    lines = ["erDiagram"]

    for relation in payload.get("relations") or []:
        cardinality = relation["cardinality"]
        optional = 1 if relation.get("optional") else 0
        left = ER_LEFT[cardinality][optional]
        right = ER_RIGHT[cardinality][optional]
        label = escape.mermaid_plain(relation.get("label") or "")
        lines.append(
            f"{INDENT}{names[relation['from']]} {left}--{right} "
            f'{names[relation["to"]]} : "{label}"'
        )

    for entity in entities:
        lines.append("")
        lines.append(f"{INDENT}{names[entity['id']]} {{")
        for row in entity.get("rows") or []:
            # Mermaid ER wants "type name"; there is no form without a type,
            # so a row that has none says so rather than inventing one.
            row_type = escape.identifier(row.get("type") or "unknown", "unknown")
            row_name = escape.identifier(row["name"], "column")
            key = f" {row['key'].upper()}" if row.get("key") else ""
            note = f' "{escape.mermaid_plain(row["note"])}"' if row.get("note") else ""
            lines.append(f"{INDENT * 2}{row_type} {row_name}{key}{note}")
        lines.append(f"{INDENT}}}")

    # Row notes are drawn inline above; an entity note has nowhere to go.
    stripped = [dict(e, rows=[]) for e in entities]
    return lines + _leftover_notes(stripped, names)


def write_class(graph: dict) -> list:
    payload = graph["payload"]
    entities = list(payload.get("entities") or [])
    names = _unique_names(entities, "Class")
    lines = ["classDiagram"]

    for entity in entities:
        name = names[entity["id"]]
        rows = entity.get("rows") or []
        stereotype = entity.get("stereotype")
        if not rows and not stereotype:
            lines.append(f"{INDENT}class {name}")
            continue
        lines.append(f"{INDENT}class {name} {{")
        if stereotype:
            lines.append(f"{INDENT * 2}<<{escape.identifier(stereotype, 'kind')}>>")
        for row in rows:
            visibility = row.get("visibility") or ""
            row_name = escape.mermaid_member(row["name"])
            row_type = escape.mermaid_member(row.get("type") or "")
            if row.get("kind") == "method":
                if "(" not in row_name:
                    row_name += "()"
                tail = f" {row_type}" if row_type else ""
                lines.append(f"{INDENT * 2}{visibility}{row_name}{tail}")
            else:
                head = f"{row_type} " if row_type else ""
                lines.append(f"{INDENT * 2}{visibility}{head}{row_name}")
        lines.append(f"{INDENT}}}")

    if payload.get("relations"):
        lines.append("")
    for relation in payload.get("relations") or []:
        kind = relation["kind"]
        arrow = CLASS_RELATIONS.get(kind, "..>")
        label = relation.get("label")
        if kind in REQUIREMENT_RELATIONS:
            label = f"{kind} {label}" if label else kind
        tail = f" : {escape.mermaid_plain(label)}" if label else ""
        lines.append(f"{INDENT}{names[relation['from']]} {arrow} {names[relation['to']]}{tail}")
    return lines + _leftover_notes(entities, names)


def write_container(graph: dict) -> list:
    """A container type, drawn with subgraph frames.

    This is the approximate half of the matrix in plan section 3. Mermaid has
    frames and nothing else: a host, a lane and a trust boundary are the same
    construct with different words in them, and the difference is carried by
    a class rather than by the shape. draw.io draws all three properly.
    """
    payload = graph["payload"]
    nodes = {n["id"]: n for n in payload.get("nodes") or [] if isinstance(n, dict)}
    groups = [g for g in payload.get("groups") or [] if isinstance(g, dict)]
    edges = payload.get("edges") or []

    children_of: dict = {g["id"]: [] for g in groups}
    roots = []
    for group in groups:
        parent = group.get("parent")
        (children_of[parent] if parent in children_of else roots).append(group)

    lines = ["flowchart TD"]

    def frame(group: dict, depth: int) -> None:
        pad = INDENT * depth
        label = escape.mermaid_quoted(group.get("label", ""))
        lines.append(f"{pad}subgraph sg_{safe_id(group['id'])}[{label}]")
        if graph.get("type") == "swimlane":
            # Mermaid accepts this and honours it unreliably once frames
            # nest. It is the reason swimlane is not full coverage here.
            lines.append(f"{pad}{INDENT}direction LR")
        for child in children_of[group["id"]]:
            frame(child, depth + 1)
        for member in group.get("members") or []:
            node = nodes.get(member)
            if node is not None:
                lines.append(declare(node, depth + 1))
        lines.append(f"{pad}end")

    for group in roots:
        frame(group, 1)

    claimed = {m for g in groups for m in (g.get("members") or [])}
    for node in payload.get("nodes") or []:
        if node["id"] not in claimed:
            lines.append(declare(node, 1))

    lines.append("")
    for edge in edges:
        arrow = ARROWS.get(edge.get("kind"), DEFAULT_ARROW)
        label = edge.get("label")
        mid = f"|{escape.mermaid_quoted(label)}|" if label else ""
        lines.append(f"{INDENT}{safe_id(edge['from'])} {arrow}{mid} {safe_id(edge['to'])}")

    # A trust boundary is the one container kind that has to look different,
    # because crossing it is the thing the diagram is about. Section 3 fixes
    # the convention: a dashed red frame, in both formats.
    trust = [g for g in groups if g.get("kind") in ("trust", "boundary")]
    if trust:
        lines.append("")
        lines.append(
            f"{INDENT}classDef trust stroke:#B3261E,stroke-width:2px,"
            "stroke-dasharray: 6 4,fill:none"
        )
        for group in trust:
            lines.append(f"{INDENT}class sg_{safe_id(group['id'])} trust")

    notes = [(n["id"], n["note"]) for n in payload.get("nodes") or [] if n.get("note")]
    if notes:
        lines.append("")
        for node_id, note in notes:
            lines.append(f"%% {safe_id(node_id)}: {escape.mermaid_plain(note)}")
    return lines


def _axis_is_dates(spans: list) -> bool:
    """Mermaid's gantt has one axis and it is made of dates."""
    values = []
    for span in spans:
        for key in ("start", "end"):
            value = span.get(key)
            if value:
                values.append(str(value))
    return bool(values) and all(
        len(v.split("-")) == 3 and all(part.isdigit() for part in v.split("-"))
        for v in values
    )


def write_gantt(graph: dict) -> list:
    payload = graph["payload"]
    tracks = {t["id"]: t for t in payload.get("tracks") or []}
    spans = list(payload.get("spans") or [])

    if not _axis_is_dates(spans):
        raise GenerationError(
            "Mermaid's gantt only understands real dates. Either give every span a "
            "start and an end in YYYY-MM-DD, or draw it in draw.io, whose timeline "
            "axis is ordinal and does not care"
        )

    lines = ["gantt", f"{INDENT}dateFormat YYYY-MM-DD", f"{INDENT}axisFormat %d %b"]
    for track_id, track in tracks.items():
        rows = [s for s in spans if s.get("track") == track_id]
        if not rows:
            continue
        lines.append(f"{INDENT}section {escape.mermaid_plain(track['label'])}")
        for span in rows:
            tags = [escape.identifier(span["id"], "s")]
            if span.get("kind") == "milestone":
                tags.insert(0, "milestone")
            body = ", ".join(tags + [str(span["start"]), str(span.get("end") or "0d")])
            lines.append(f"{INDENT * 2}{escape.mermaid_plain(span['label'])} :{body}")
    return lines


def write_journey(graph: dict) -> list:
    payload = graph["payload"]
    tracks = {t["id"]: t for t in payload.get("tracks") or []}
    spans = list(payload.get("spans") or [])

    missing = [s["id"] for s in spans if s.get("score") is None]
    if missing:
        raise GenerationError(
            "a journey step is a score out of five, and "
            + ", ".join(missing)
            + " has none. Give every span a 'score', or drop the diagram: without "
            "the scores it says nothing a numbered list would not say better"
        )

    lines = ["journey"]
    for track_id, track in tracks.items():
        rows = [s for s in spans if s.get("track") == track_id]
        if not rows:
            continue
        lines.append(f"{INDENT}section {escape.mermaid_plain(track['label'])}")
        for span in rows:
            actor = escape.mermaid_plain(span.get("note") or "User")
            label = escape.mermaid_plain(span["label"])
            lines.append(f"{INDENT * 2}{label}: {span['score']}: {actor}")
    return lines


def write_gitgraph(graph: dict) -> list:
    """Tracks are branches, spans are what lands on them, in axis order.

    The first track is the trunk. Mermaid opens on it already, so it is never
    branched and never checked out at the start; every other track is created
    the first time something lands on it.
    """
    payload = graph["payload"]
    tracks = list(payload.get("tracks") or [])
    if not tracks:
        return ["gitGraph"]

    names = {t["id"]: escape.identifier(t.get("label") or t["id"], "branch") for t in tracks}
    trunk = tracks[0]["id"]
    spans = sorted(
        payload.get("spans") or [], key=lambda s: _AXIS_KEY(str(s.get("start", "")))
    )
    track_of = {s["id"]: s.get("track") for s in spans}

    lines = ["gitGraph"]
    opened = {trunk}
    current = trunk
    for span in spans:
        track = span.get("track")
        if track not in opened:
            if current != trunk:
                lines.append(f"{INDENT}checkout {names[trunk]}")
                current = trunk
            lines.append(f"{INDENT}branch {names[track]}")
            opened.add(track)
            current = track
        elif track != current:
            lines.append(f"{INDENT}checkout {names[track]}")
            current = track

        label = escape.mermaid_plain(span["label"])
        if span.get("kind") == "merge":
            sources = [
                track_of[d]
                for d in span.get("depends_on") or []
                if track_of.get(d) and track_of[d] != track
            ]
            if not sources:
                raise GenerationError(
                    f"span {span['id']!r} is a merge but depends on nothing in another "
                    "branch, so there is nothing for it to merge in"
                )
            lines.append(f"{INDENT}merge {names[sources[0]]} tag: {QUOTE}{label}{QUOTE}")
        else:
            lines.append(f"{INDENT}commit id: {QUOTE}{label}{QUOTE}")
    return lines


def write_requirements(graph: dict) -> list:
    """requirementDiagram, which is what the type is actually for.

    Reusing the class writer was tempting and wrong: a class member is a bare
    token, so "9 blocks, 12 links" came out as "9_blocks,12_links". A
    requirement is a sentence, and this is the one Mermaid diagram that has a
    place to put one.

    An entity with a stereotype is an element -- the thing that satisfies a
    requirement. Everything else is a requirement.
    """
    payload = graph["payload"]
    entities = list(payload.get("entities") or [])
    names = _unique_names(entities, "req")

    lines = ["requirementDiagram", ""]
    for i, entity in enumerate(entities, 1):
        name = names[entity["id"]]
        if entity.get("stereotype"):
            lines.append(f"{INDENT}element {name} {{")
            lines.append(f"{INDENT * 2}type: {escape.identifier(entity['stereotype'], 'check')}")
            lines.append(f"{INDENT}}}")
        else:
            lines.append(f"{INDENT}requirement {name} {{")
            lines.append(f"{INDENT * 2}id: {i}")
            lines.append(f"{INDENT * 2}text: {escape.mermaid_plain(entity.get('label', ''))}")
            lines.append(f"{INDENT * 2}risk: medium")
            lines.append(f"{INDENT * 2}verifymethod: inspection")
            lines.append(f"{INDENT}}}")
        lines.append("")

    for relation in payload.get("relations") or []:
        lines.append(
            f"{INDENT}{names[relation['from']]} - {relation['kind']} -> "
            f"{names[relation['to']]}"
        )

    # A requirement block has four fixed fields and no room for the acceptance
    # criteria underneath it. They are kept as comments rather than mangled
    # into member names, which is what the class writer did to them.
    rows = []
    for entity in entities:
        for row in entity.get("rows") or []:
            rows.append(
                f"%% {names[entity['id']]}: {escape.mermaid_plain(row.get('name', ''))}"
            )
    if rows:
        lines.append("")
        lines.extend(rows)
    return lines


WRITERS = {
    "architecture": write_flowchart,
    "flowchart": write_flowchart,
    "cicd": write_flowchart,
    "state": write_state,
    "sequence": write_sequence,
    "data-model": write_er,
    "db-schema": write_er,
    "class": write_class,
    "requirements": write_requirements,
    "deployment": write_container,
    "swimlane": write_container,
    "dfd": write_container,
    "c4": write_container,
    "threat-model": write_container,
    "gantt": write_gantt,
    "user-journey": write_journey,
    "git-graph": write_gitgraph,
}


# ---------------------------------------------------------------------------
# entry points
# ---------------------------------------------------------------------------


def render(graph: dict, *, with_header: bool = True) -> str:
    graph_type = graph.get("type")
    writer = WRITERS.get(graph_type)
    if writer is None:
        wave = schema.TYPES[graph_type].wave if graph_type in schema.TYPES else "?"
        raise GenerationError(
            f"type {graph_type!r} is not written yet in Mermaid (wave {wave}); "
            f"available now: {', '.join(sorted(WRITERS))}"
        )
    lines = (header(graph) if with_header else []) + writer(graph)
    return "\n".join(lines).rstrip() + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Turn a graph.json into Mermaid.")
    parser.add_argument("graph", type=Path)
    parser.add_argument("-o", "--out", type=Path, help="write here instead of stdout")
    parser.add_argument("--fence", action="store_true", help="wrap in a ```mermaid fence")
    parser.add_argument("--no-header", action="store_true", help="omit title and comments")
    args = parser.parse_args(argv)

    try:
        graph = schema.load(args.graph)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    errors, warnings = validate_graph(graph)
    for warning in warnings:
        print(f"note: {warning}", file=sys.stderr)
    if errors:
        print(f"error: {args.graph} does not validate, nothing written:", file=sys.stderr)
        for error in errors:
            for line in str(error).splitlines():
                print(f"  {line}", file=sys.stderr)
        return 2

    try:
        text = render(graph, with_header=not args.no_header)
    except GenerationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.fence:
        text = "```mermaid\n" + text + "```\n"

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(text)

    print(
        "note: syntax is correct by construction, but nothing here has rendered the "
        "diagram. Open it in a Mermaid preview before shipping it.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

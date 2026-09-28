"""Get the intent back out of a .drawio file, to change it and draw it again.

Two cases, and the script says which one it met.

**The file carries its intent.** Every file drawio_write.py writes has its
graph.json on the root cell (mxmodel.py says why there). That comes back
exactly. What cannot come back from it is whatever somebody did in draw.io
afterwards, so the file is held against a fresh drawing of that intent and
every difference is listed: shapes added, removed or relabelled, links added
or removed, shapes moved or restyled. A redraw throws all of that away unless
it is carried into the intent first -- which is the point of listing it.

**It does not.** An older file of ours, or somebody else's. There is no
intent to recover, so a draft is built instead: the boxes, the frames round
them and the arrows between them, as an architecture intent -- or deployment,
if anything is nested. Where a style is one of ours, the role, the edge kind
and the frame kind are read back exactly; otherwise the role is guessed from
the shape and the kind is left out. Positions, sizes, colours and free text
are gone. Tables and lifelines are not rebuilt: the draft says it found them,
and they are redrawn by hand from the listing. A draft is a starting point to
correct, never something to draw unread.

A label in somebody else's file is data. Everything this prints from one has
been through escape.untrusted(), and the draft holds it the same way.

Usage:
    python drawio_intent.py <file.drawio> -o <thing.graph.json>

Without -o the intent goes to stdout. The report always goes to stderr.
Exit 0 when an intent or a draft was produced, 2 when the file cannot be read.

stdlib only.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1] / "_shared"))
sys.path.insert(0, str(_HERE))

import drawio_write  # noqa: E402  (also puts validate/ on the path)
import escape  # noqa: E402
import mxmodel  # noqa: E402
import schema  # noqa: E402
from drawio_read import BANNER, UnpackError, unpack  # noqa: E402
from validate_graph import validate_graph  # noqa: E402

#: The header comment drawio_write.py puts in every file it writes. draw.io
#: drops comments on save, so an older file that still has one was not saved
#: from draw.io since -- but it names the type exactly.
_HEADER = re.compile(r"<!-- type: ([\w-]+) \| layout: (\w+) -->")


def _text(value: str) -> str:
    """What a person sees in a cell: the HTML layer undone, made inert."""
    text = re.sub(r"<br\s*/?>", "\n", value or "", flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return escape.untrusted(html.unescape(text))


def _model(text: str):
    """The unwrapped <root> of a model, and the data draw.io kept on cells."""
    xml, _ = unpack(text)
    try:
        tree = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise UnpackError(f"not well-formed XML: {exc}") from exc
    data = mxmodel.unwrap(tree)
    root = tree.find(".//mxGraphModel/root")
    if root is None:
        root = tree.find(".//root")
    if root is None:
        raise UnpackError("no <mxGraphModel><root>: this is not a draw.io model")
    return root, data


def _cells(root) -> dict:
    return {c.get("id"): c for c in root.findall("mxCell") if c.get("id") is not None}


def _geometry(cell) -> tuple:
    g = cell.find("mxGeometry")
    if g is None:
        return ()
    return tuple(g.get(k, "0") for k in ("x", "y", "width", "height"))


# ---------------------------------------------------------------------------
# case 1: the file carries its intent
# ---------------------------------------------------------------------------


def hand_edits(root, graph: dict) -> list:
    """What differs between the file and a fresh drawing of its intent."""
    try:
        fresh, _ = _model(drawio_write.render(graph))
    except (drawio_write.GenerationError, UnpackError) as exc:
        return [f"cannot redraw the embedded intent to compare against: {exc}"]

    have, want = _cells(root), _cells(fresh)
    lines: list = []

    def name(cell) -> str:
        return repr(_text(cell.get("value") or "") or cell.get("id"))

    def vertices(cells):
        return {i: c for i, c in cells.items() if c.get("vertex") == "1"}

    got_v, want_v = vertices(have), vertices(want)
    for cell_id in got_v.keys() - want_v.keys():
        lines.append(f"added by hand: shape {name(got_v[cell_id])}")
    for cell_id in want_v.keys() - got_v.keys():
        lines.append(f"removed by hand: shape {name(want_v[cell_id])}")
    moved = restyled = 0
    for cell_id in got_v.keys() & want_v.keys():
        a, b = got_v[cell_id], want_v[cell_id]
        if _text(a.get("value") or "") != _text(b.get("value") or ""):
            lines.append(f"relabelled by hand: {name(b)} is now {name(a)}")
        if _geometry(a) != _geometry(b):
            moved += 1
        if (a.get("style") or "") != (b.get("style") or ""):
            restyled += 1

    def links(cells):
        return Counter(
            (c.get("source"), c.get("target"))
            for c in cells.values()
            if c.get("edge") == "1" and c.get("source") and c.get("target")
        )

    def end(cells, cell_id) -> str:
        cell = cells.get(cell_id)
        return name(cell) if cell is not None else repr(cell_id)

    got_e, want_e = links(have), links(want)
    for (src, dst), n in (got_e - want_e).items():
        lines.append(f"added by hand: {n} link(s) {end(have, src)} -> {end(have, dst)}")
    for (src, dst), n in (want_e - got_e).items():
        lines.append(f"removed by hand: {n} link(s) {end(want, src)} -> {end(want, dst)}")
    for cell_id in have.keys() & want.keys():
        a, b = have[cell_id], want[cell_id]
        if a.get("edge") == "1" and b.get("edge") == "1":
            if _text(a.get("value") or "") != _text(b.get("value") or ""):
                lines.append(f"relabelled by hand: link {name(b)} is now {name(a)}")

    if moved:
        lines.append(f"{moved} shape(s) moved or resized by hand: a redraw puts them back")
    if restyled:
        lines.append(f"{restyled} shape(s) restyled by hand: a redraw uses the house style")
    return sorted(lines)


# ---------------------------------------------------------------------------
# case 2: it does not -- build a draft
# ---------------------------------------------------------------------------


def _invert(styles: dict) -> dict:
    """style string -> the one name that produces it, where there is one."""
    seen: dict = {}
    for key, style in styles.items():
        seen.setdefault(style, []).append(key)
    return {style: keys for style, keys in seen.items()}


def _guess_role(style: str, spec) -> str | None:
    exact = _invert(drawio_write.STYLES).get(style)
    if exact:
        for role in exact:
            if role in spec.roles:
                return role
    parts = style.split(";")
    guesses = (
        ("cylinder" in style, "store"),
        ("parallelogram" in style, "queue"),
        ("dashed=1" in parts, "external"),
        ("ellipse" in parts or "umlActor" in style, "actor"),
        ("rounded=1" in parts, "component"),
    )
    for hit, role in guesses:
        if hit and role in spec.roles:
            return role
    return None


def _edge_kind(style: str, spec) -> str | None:
    """Only ever exact: a style of ours with the side anchors taken off."""
    base = re.sub(r"(exit|entry)(X|Y|Dx|Dy)=[^;]*;", "", style)
    for kind in _invert(drawio_write.EDGE_STYLES).get(base, []):
        if kind in spec.edge_kinds:
            return kind
    return None


def _group_kind(style: str) -> str:
    for kind in _invert(drawio_write.GROUP_STYLES).get(style, []):
        if kind in schema.GROUP_KINDS:
            return kind
    return "trust" if "dashed=1" in style.split(";") else "group"


class NoDraft(Exception):
    """A file whose intent cannot honestly be guessed from its shapes."""


def _is_text(cell) -> bool:
    style = cell.get("style") or ""
    return style.startswith("text;") or "edgeLabel" in style


def _vertices(cells: dict) -> dict:
    """Every shape, leaving out labels that ride on an edge."""
    return {
        i: c
        for i, c in cells.items()
        if c.get("vertex") == "1"
        and not (cells.get(c.get("parent")) is not None and cells[c.get("parent")].get("edge") == "1")
    }


def _ids(cell_ids) -> dict:
    """Cell id -> an id the schema accepts, unique, with our own 'n_' taken off
    so that an older file of ours gets its original ids back."""
    ids: dict = {}
    taken: set = set()
    for cell_id in cell_ids:
        base = cell_id[2:] if cell_id[:2] in ("n_", "s_") else cell_id
        new = escape.identifier(base, "n")[:36]
        candidate, n = new, 2
        while candidate in taken or not schema.ID_RE.match(candidate):
            candidate = f"{new[:32]}_{n}"
            n += 1
        taken.add(candidate)
        ids[cell_id] = candidate
    return ids


def _header_type(raw_text: str, layout: str):
    """The type the file names in its header comment, if it fits the layout."""
    header = _HEADER.search(raw_text)
    if not header:
        return None
    named = header.group(1)
    if named in schema.TYPES and schema.TYPES[named].layout == layout == header.group(2):
        return named
    return None


def _wrap(graph_type: str, payload: dict, title: str, source: str, dropped: list) -> dict:
    dropped.insert(0, {"what": "positions, sizes and colours", "why": "the layout is worked out again"})
    return {
        "type": graph_type,
        "layout": schema.TYPES[graph_type].layout,
        "meta": {
            "title": title or "Recovered diagram",
            "scope": f"recovered from {source}",
            "detail": "normal",
            "audience": "engineer",
            "dropped": dropped,
            "budget_override": None,
        },
        "payload": payload,
    }


def _points(cell) -> tuple:
    """(x1, y1, x2, y2) of an edge drawn by points rather than by ends."""
    g = cell.find("mxGeometry")
    found = {}
    if g is not None:
        for p in g.findall("mxPoint"):
            try:
                found[p.get("as")] = (float(p.get("x", 0)), float(p.get("y", 0)))
            except ValueError:
                pass
    a, b = found.get("sourcePoint"), found.get("targetPoint")
    return (a[0], a[1], b[0], b[1]) if a and b else ()


def draft_sequence(cells: dict, raw_text: str, title: str, source: str) -> tuple:
    """Lifelines in the order they stand, messages in the order they fall."""
    vertices = _vertices(cells)
    heads = sorted(
        (c for c in vertices.values() if "umlLifeline" in (c.get("style") or "")),
        key=lambda c: float((c.find("mxGeometry").get("x") if c.find("mxGeometry") is not None else 0) or 0),
    )
    ids = _ids(c.get("id") for c in heads)
    spec = schema.TYPES["sequence"]
    centres = []
    for c in heads:
        g = _geometry(c)
        centres.append((float(g[0]) + float(g[2]) / 2 if g else 0.0, ids[c.get("id")]))

    def lifeline_of(cell_id, x):
        while cell_id in vertices:  # an activation bar sits inside its lifeline
            if cell_id in ids:
                return ids[cell_id]
            cell_id = vertices[cell_id].get("parent")
        if x is None or not centres:
            return None
        return min(centres, key=lambda cx: abs(cx[0] - x))[1]

    styles = _invert(drawio_write.MESSAGE_STYLES)
    found, loose = [], 0
    for cell in cells.values():
        if cell.get("edge") != "1":
            continue
        pts = _points(cell)
        src = lifeline_of(cell.get("source"), pts[0] if pts else None)
        dst = lifeline_of(cell.get("target"), pts[2] if pts else None)
        if src is None or dst is None:
            loose += 1
            continue
        message = {"from": src, "to": dst, "label": _text(cell.get("value") or "") or "(no label)"}
        for kind in styles.get(cell.get("style") or "", []):
            if kind in spec.edge_kinds and (kind == "self") == (src == dst):
                message["kind"] = kind
                break
        found.append((pts[1] if pts else 0.0, message))
    found.sort(key=lambda ym: ym[0])

    dropped = []
    frames = [c for c in vertices.values() if "umlFrame" in (c.get("style") or "")]
    if frames:
        dropped.append({"what": f"{len(frames)} alt/opt/loop frame(s)", "why": "which messages they span is not recorded"})
    if loose:
        dropped.append({"what": f"{loose} message(s) not between two lifelines", "why": "no sender or receiver"})
    payload = {
        "actors": [{"id": ids[c.get("id")], "label": _text(c.get("value") or "") or ids[c.get("id")]} for c in heads],
        "messages": [m for _, m in found],
    }
    graph = _wrap("sequence", payload, title, source, dropped)
    return graph, [
        f"draft: {len(heads)} lifeline(s), {len(found)} message(s), in the order they are drawn. "
        "Check the order, and put any alt/opt/loop frames back by message index"
    ]


#: A row as layouts._row_text() writes it: "+name() : type  PK". The two
#: spaces before the key are one by the time a label has been flattened.
_ROW = re.compile(r"^(?P<vis>[-+#~])?(?P<name>.+?)(?: : (?P<type>.+?))?(?:\s+(?P<key>PK|FK|UK))?$")


def draft_table(cells: dict, raw_text: str, title: str, source: str) -> tuple:
    """Tables with their rows; relations with their ends, where they are ours."""
    vertices = _vertices(cells)
    tables = {
        i: c for i, c in vertices.items()
        if "swimlane" in (c.get("style") or "") and c.get("parent") not in vertices
    }
    ids = _ids(tables)
    rows_of: dict = {i: [] for i in tables}
    for c in vertices.values():
        if c.get("parent") in tables and _is_text(c):
            g = _geometry(c)
            rows_of[c.get("parent")].append((float(g[1]) if g else 0.0, _text(c.get("value") or "")))

    keyed = False
    entities = []
    for cell_id, cell in tables.items():
        title_text = _text(cell.get("value") or "")
        stereotype = None
        match = re.match(r"^<<(.+?)>>\s*(.*)$", title_text)
        if match:
            stereotype, title_text = match.group(1), match.group(2)
        rows = []
        for _, text in sorted(rows_of[cell_id]):
            m = _ROW.match(text)
            if not m or not m.group("name").strip():
                continue
            row = {"name": m.group("name").strip()}
            if m.group("vis"):
                row["visibility"] = m.group("vis")
            if row["name"].endswith(")"):
                row["kind"] = "method"
            if m.group("type"):
                row["type"] = m.group("type").strip()
            if m.group("key"):
                row["key"] = m.group("key").lower()
                keyed = True
            rows.append(row)
        entity = {"id": ids[cell_id], "label": title_text or ids[cell_id], "rows": rows}
        if stereotype:
            entity["stereotype"] = stereotype
        entities.append(entity)

    graph_type = _header_type(raw_text, "table") or ("data-model" if keyed else "class")
    spec = schema.TYPES[graph_type]
    kinds = _invert({k: v for k, v in drawio_write.CLASS_RELATIONS.items()})
    ends = {v: k for k, v in drawio_write.ER_ENDS.items()}

    def owner(cell_id):
        while cell_id in vertices:
            if cell_id in ids:
                return ids[cell_id]
            cell_id = vertices[cell_id].get("parent")
        return None

    relations, loose = [], 0
    for cell in cells.values():
        if cell.get("edge") != "1":
            continue
        src, dst = owner(cell.get("source")), owner(cell.get("target"))
        if src is None or dst is None:
            loose += 1
            continue
        relation = {"from": src, "to": dst}
        label = _text(cell.get("value") or "")
        if label:
            relation["label"] = label
        if spec.relation_style == "cardinality":
            near = far = ""
            for child in cells.values():
                if child.get("parent") == cell.get("id"):
                    x = (child.find("mxGeometry").get("x") if child.find("mxGeometry") is not None else "0") or "0"
                    text = _text(child.get("value") or "")
                    if float(x) < 0:
                        near = text
                    else:
                        far = text
            if far.startswith("0.."):
                relation["optional"] = True
                far = far[3:]
            relation["cardinality"] = ends.get((near, far), "1-n")
        else:
            base = re.sub(r"(exit|entry)(X|Y|Dx|Dy)=[^;]*;", "", cell.get("style") or "")
            for kind in kinds.get(base, []):
                if kind in spec.relation_kinds:
                    relation["kind"] = kind
                    break
            relation.setdefault("kind", "assoc" if graph_type == "class" else "traces")
        relations.append(relation)

    dropped = []
    if loose:
        dropped.append({"what": f"{loose} link(s) not between two tables", "why": "no table at one end"})
    graph = _wrap(graph_type, {"entities": entities, "relations": relations}, title, source, dropped)
    named = "The type was named in the file." if _HEADER.search(raw_text) else "The type is a guess."
    return graph, [
        f"draft: {len(entities)} table(s), {sum(len(e['rows']) for e in entities)} row(s), "
        f"{len(relations)} relation(s), drawn as {graph_type!r}. {named} "
        "Check the row types, the keys and each relation's cardinality or kind"
    ]


def draft(root, raw_text: str, title: str, source: str) -> tuple:
    """(graph, notes). Boxes, frames and arrows, and what could not come."""
    cells = _cells(root)
    vertices = _vertices(cells)
    styles = [c.get("style") or "" for c in vertices.values()]
    header = _HEADER.search(raw_text)
    if (header and header.group(2) == "timeline") or any(
        s.startswith("swimlane;horizontal=0;") for s in styles
    ):
        raise NoDraft(
            "this is a timeline -- a Gantt chart, a user journey or a branch diagram. "
            "Its dates and order are not in the drawing, only where the bars ended up, "
            "so no draft is built. List it with drawio_read.py and write the intent by hand"
        )
    if any("umlLifeline" in s for s in styles):
        return draft_sequence(cells, raw_text, title, source)
    if any(
        _is_text(c) and c.get("parent") in vertices
        and "swimlane" in (vertices[c.get("parent")].get("style") or "")
        and vertices[c.get("parent")].get("parent") not in vertices
        for c in vertices.values()
    ):
        return draft_table(cells, raw_text, title, source)

    notes: list = []
    dropped: list = []
    loose = [c for c in vertices.values() if _is_text(c) or "umlFrame" in (c.get("style") or "")]
    if loose:
        dropped.append({"what": f"{len(loose)} piece(s) of free text", "why": "not a box or a link"})

    shapes = {i: c for i, c in vertices.items() if c not in loose}
    frames = {c.get("parent") for c in shapes.values() if c.get("parent") in shapes}

    layout = "container" if frames else "layered"
    graph_type = _header_type(raw_text, layout) or ("deployment" if frames else "architecture")
    if graph_type == "c4":
        graph_type = "deployment"
        notes.append("the file says it was a C4 diagram; the draft is 'deployment' because the "
                     "level is not recorded. Change the type back and set meta.level")
    spec = schema.TYPES[graph_type]
    ids = _ids(shapes)

    nodes, groups = [], []
    for cell_id, cell in shapes.items():
        label = _text(cell.get("value") or "") or ids[cell_id]
        if cell_id in frames:
            group = {"id": ids[cell_id], "label": label, "kind": _group_kind(cell.get("style") or ""),
                     "members": [ids[i] for i, c in shapes.items()
                                 if c.get("parent") == cell_id and i not in frames]}
            parent = cell.get("parent")
            if parent in frames:
                group["parent"] = ids[parent]
            groups.append(group)
            continue
        node = {"id": ids[cell_id], "label": label}
        role = _guess_role(cell.get("style") or "", spec)
        if role:
            node["role"] = role
        nodes.append(node)

    def owner(cell_id):
        """The box an arrow end belongs to: itself, or whatever it sits in."""
        while cell_id is not None and cell_id in vertices:
            if cell_id in shapes and cell_id not in frames:
                return ids[cell_id]
            if cell_id in frames:
                return None
            cell_id = vertices[cell_id].get("parent")
        return None

    edges, to_frames, floating = [], 0, 0
    for cell in cells.values():
        if cell.get("edge") != "1":
            continue
        src, dst = owner(cell.get("source")), owner(cell.get("target"))
        if src is None or dst is None:
            if cell.get("source") in frames or cell.get("target") in frames:
                to_frames += 1
            else:
                floating += 1
            continue
        edge = {"from": src, "to": dst}
        label = _text(cell.get("value") or "")
        for child in cells.values():  # draw.io keeps a moved label as a child cell
            if child.get("parent") == cell.get("id") and not label:
                label = _text(child.get("value") or "")
        if label:
            edge["label"] = label
        kind = _edge_kind(cell.get("style") or "", spec)
        if kind:
            edge["kind"] = kind
        edges.append(edge)
    if to_frames:
        dropped.append({"what": f"{to_frames} link(s) to a whole frame", "why": "links join boxes, not frames"})
    if floating:
        dropped.append({"what": f"{floating} link(s) with a loose end", "why": "not attached to a box"})

    # Start and end share one shape, so the style cannot tell them apart.
    # The links can: nothing leaves an end, and nothing arrives at a start.
    leaves = {e["from"] for e in edges}
    arrives = {e["to"] for e in edges}
    for node in nodes:
        style = shapes[next(i for i in shapes if ids[i] == node["id"])].get("style") or ""
        both = set(_invert(drawio_write.STYLES).get(style, [])) & {"start", "end"} & spec.roles
        if len(both) == 2:
            if node["id"] not in leaves:
                node["role"] = "end"
            elif node["id"] not in arrives:
                node["role"] = "start"

    payload = {"nodes": nodes, "edges": edges}
    if spec.layout == "container":
        payload["groups"] = groups
    graph = _wrap(graph_type, payload, title, source, dropped)
    notes.insert(
        0,
        f"draft: {len(nodes)} box(es), {len(groups)} frame(s), {len(edges)} link(s), "
        f"drawn as {graph_type!r}. "
        + ("The type was named in the file. " if header and graph_type == header.group(1) else "The type is a guess. ")
        + "Check the type, the roles and the kinds before drawing",
    )
    return graph, notes


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Recover the intent from a .drawio file, or draft one from it."
    )
    parser.add_argument("path", type=Path)
    parser.add_argument("-o", "--out", type=Path, help="write the intent here instead of stdout")
    args = parser.parse_args(argv)

    try:
        text = args.path.read_text(encoding="utf-8")
        root, data = _model(text)
    except (OSError, UnpackError) as exc:
        print(f"error: cannot read {args.path}: {exc}", file=sys.stderr)
        return 2

    embedded, problem = mxmodel.embedded_intent(data)
    if problem:
        print(f"note: {problem}; building a draft instead", file=sys.stderr)

    if embedded is not None:
        graph = embedded
        report = ["recovered: the file carries its intent, and this is it exactly"]
        edits = hand_edits(root, graph)
        if edits:
            report.append(
                "changed in draw.io since it was drawn. A redraw loses these "
                "unless they are put into the intent first:"
            )
            report += [f"  {line}" for line in edits]
        else:
            report.append("nothing was changed by hand since it was drawn")
    else:
        title = ""
        match = re.search(r'<diagram[^>]*\bname="([^"]*)"', text)
        if match:
            title = escape.untrusted(html.unescape(match.group(1)))
        try:
            graph, report = draft(root, text, title, args.path.name)
        except NoDraft as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        report.append(BANNER)

    errors, warnings = validate_graph(graph)
    if errors:
        report.append("does not validate yet -- fix these before drawing:")
        report += [f"  {line}" for e in errors for line in str(e).splitlines()]
    report += [f"note: {w}" for w in warnings]

    out = json.dumps(graph, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(out, encoding="utf-8", newline="\n")
        report.append(f"wrote {args.out}")
    else:
        sys.stdout.write(out)
    for line in report:
        print(line, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

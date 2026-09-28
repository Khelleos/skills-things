"""Check a generated .drawio file.

The second of the three layers in plan section 6. It cannot tell you the
diagram is any good -- that is what validate_graph.py did, before this file
existed -- but it can tell you the model is one draw.io will open and that
nothing was lost between the intent and the XML.

Five passes:

  1. well-formed    -- it parses as XML at all
  2. model shape    -- the mxGraphModel skeleton, cells 0 and 1, every cell
                       parented, every vertex with a geometry
  3. references     -- edge source and target name cells that exist; a
                       parent chain that terminates and does not loop
  4. geometry       -- no zero or negative sizes, nothing off the page, no
                       two sibling boxes sitting on top of each other
  5. round trip     -- every node and edge in the intent is findable in the
                       XML, with the label it was given. The intent is the
                       one --graph names, or else the one the file carries;
                       given both, they have to be the same intent

Usage:
    python validate_drawio.py <file.drawio> [--graph <graph.json>] [--json]

Exit code 0 when clean, 1 when any file has an error.

stdlib only.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))

import escape  # noqa: E402
import mxmodel  # noqa: E402
import schema  # noqa: E402

#: Shapes that are meant to sit over other shapes: a frame around a group of
#: lifelines, a note pinned beside a message, a label riding on an edge.
_OVERLAPS_BY_DESIGN = ("umlFrame", "umlLifeline", "shape=note", "edgeLabel")

_XML_ENTITIES = (("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'"), ("&amp;", "&"))


def _xml_unescape(text: str) -> str:
    """Undo exactly one XML layer, the one ElementTree already undid for us.

    Used to predict what an attribute should read as after parsing, so that a
    label can be compared without guessing.
    """
    for entity, char in _XML_ENTITIES:
        text = text.replace(entity, char)
    return text


def _rects_overlap(a: dict, b: dict) -> bool:
    return (
        a["x"] < b["x"] + b["w"]
        and b["x"] < a["x"] + a["w"]
        and a["y"] < b["y"] + b["h"]
        and b["y"] < a["y"] + a["h"]
    )


def _geometry_of(cell) -> dict | None:
    geometry = cell.find("mxGeometry")
    if geometry is None:
        return None
    try:
        return {
            "x": float(geometry.get("x", 0)),
            "y": float(geometry.get("y", 0)),
            "w": float(geometry.get("width", 0)),
            "h": float(geometry.get("height", 0)),
        }
    except ValueError:
        return None


def check_model(root, errors: list, warnings: list) -> dict:
    """Passes 2 and 3. Returns the cells by id, for the geometry pass."""
    model = root.find(".//mxGraphModel")
    if model is None:
        errors.append("no <mxGraphModel> element: draw.io will not open this")
        return {}
    tree_root = model.find("root")
    if tree_root is None:
        errors.append("<mxGraphModel> has no <root>")
        return {}

    cells = {}
    for cell in tree_root.findall("mxCell"):
        cell_id = cell.get("id")
        if cell_id is None:
            errors.append("a cell with no id")
            continue
        if cell_id in cells:
            errors.append(f"cell {cell_id!r}: id used twice")
        cells[cell_id] = cell

    for required in ("0", "1"):
        if required not in cells:
            errors.append(f"cell {required!r} is missing: every mxGraphModel needs it")

    for cell_id, cell in cells.items():
        if cell_id in ("0", "1"):
            continue
        parent = cell.get("parent")
        if parent is None:
            errors.append(f"cell {cell_id!r}: no parent")
        elif parent not in cells:
            errors.append(f"cell {cell_id!r}: parent {parent!r} does not exist")

        is_edge = cell.get("edge") == "1"
        is_vertex = cell.get("vertex") == "1"
        if not is_edge and not is_vertex:
            errors.append(f"cell {cell_id!r}: neither vertex nor edge")
        if is_vertex and cell.find("mxGeometry") is None:
            errors.append(f"cell {cell_id!r}: a vertex with no geometry is invisible")
        if not cell.get("style"):
            warnings.append(f"cell {cell_id!r}: no style, draw.io will use its default")

        for end in ("source", "target"):
            ref = cell.get(end)
            if ref is not None and ref not in cells:
                errors.append(f"cell {cell_id!r}: {end} {ref!r} does not exist")
        if is_edge and cell.get("source") is None and cell.get("target") is None:
            geometry = cell.find("mxGeometry")
            has_points = geometry is not None and geometry.find("mxPoint") is not None
            if not has_points:
                errors.append(
                    f"cell {cell_id!r}: a floating edge with neither ends nor points "
                    "draws nothing"
                )

    # a parent chain that loops would hang draw.io rather than fail politely
    for cell_id in cells:
        seen, current = set(), cell_id
        while current in cells and current not in ("0", "1"):
            if current in seen:
                errors.append(f"cell {cell_id!r}: parent chain loops")
                break
            seen.add(current)
            current = cells[current].get("parent")

    return cells


#: Roughly the width of one character of 12px Helvetica. Deliberately a little
#: under the figure layouts.py sizes boxes with, so this flags real overflow
#: rather than arguing with the layout about a pixel.
_CHAR_W = 6.9
_LINE_H = 16

#: Shapes whose label does not live in the body: a title band, a lane header,
#: a label positioned outside the shape, a label riding on an edge.
_LABEL_ELSEWHERE = ("edgeLabel", "umlFrame", "umlLifeline", "labelPosition=right")


def _text_of(value: str) -> str:
    """The value attribute after its HTML layer, near enough to measure."""
    text = value.replace("&lt;br&gt;", " ").replace("<br>", " ")
    text = re.sub(r"&lt;[^&]*&gt;", "", text)
    text = re.sub(r"<[^>]*>", "", text)
    return html.unescape(html.unescape(text)).strip()


def check_labels_fit(cells: dict, warnings: list) -> None:
    """A label wider than its box is what a person notices first.

    Nothing else in the toolchain can see it: the model is valid, the round
    trip succeeds, and the text simply runs out of the shape. The estimate is
    approximate on purpose -- it is here to catch a label at twice the width
    of its box, not to police kerning.
    """
    for cell_id, cell in cells.items():
        if cell.get("vertex") != "1":
            continue
        style = cell.get("style") or ""
        if any(marker in style for marker in _LABEL_ELSEWHERE):
            continue
        value = cell.get("value") or ""
        text = _text_of(value)
        if not text:
            continue
        geometry = _geometry_of(cell)
        if not geometry or geometry["w"] <= 0 or geometry["h"] <= 0:
            continue

        usable = geometry["w"] - 16
        if usable <= 0:
            continue

        longest_word = max((len(w) for w in text.split()), default=0) * _CHAR_W
        if longest_word > usable + 1:
            warnings.append(
                f"cell {cell_id!r}: {text[:40]!r} has a word wider than the shape "
                f"({round(longest_word)}px in {round(geometry['w'])}px). It will run "
                "over the edge"
            )
            continue

        if "swimlane" in style:
            continue  # the label sits in the title band, not in the body

        lines = max(1, -(-round(len(text) * _CHAR_W) // max(1, round(usable))))
        # No padding in the comparison: a single 12px line sits comfortably in
        # a 22px row, and demanding room for the padding as well would flag
        # every table row in the corpus.
        if lines * _LINE_H > geometry["h"] + 1:
            warnings.append(
                f"cell {cell_id!r}: {text[:40]!r} wraps to about {lines} lines and the "
                f"shape is {round(geometry['h'])}px tall"
            )


def _absolute(cells: dict, cell_id: str):
    """A cell's rectangle in page coordinates, following its parent chain."""
    cell = cells.get(cell_id)
    if cell is None:
        return None
    geometry = _geometry_of(cell)
    if geometry is None or geometry["w"] <= 0 or geometry["h"] <= 0:
        return None
    rect = dict(geometry)
    parent = cell.get("parent")
    seen = 0
    while parent in cells and parent not in ("0", "1") and seen < 16:
        parent_geometry = _geometry_of(cells[parent])
        if parent_geometry:
            rect["x"] += parent_geometry["x"]
            rect["y"] += parent_geometry["y"]
        parent = cells[parent].get("parent")
        seen += 1
    return rect


def _ancestors(cells: dict, cell_id: str) -> set:
    chain, parent, seen = set(), cells.get(cell_id, {}).get("parent"), 0
    while parent in cells and parent not in ("0", "1") and seen < 16:
        chain.add(parent)
        parent = cells[parent].get("parent")
        seen += 1
    return chain


def _descendants(cells: dict, cell_id: str) -> set:
    """Everything drawn inside one cell.

    A row of a table is not something an edge into that table crosses: it is
    part of what the edge connects to. Without this, every table relation
    reports itself as passing through the rows at both of its ends.
    """
    inside, frontier = set(), [cell_id]
    while frontier:
        parent = frontier.pop()
        for other_id, cell in cells.items():
            if cell.get("parent") == parent and other_id not in inside:
                inside.add(other_id)
                frontier.append(other_id)
    return inside


def _anchor(style: str, prefix: str, rect: dict):
    """The point an edge leaves or arrives at, when the style fixes it."""
    x = y = None
    for part in style.split(";"):
        if part.startswith(f"{prefix}X="):
            x = float(part.split("=", 1)[1])
        elif part.startswith(f"{prefix}Y="):
            y = float(part.split("=", 1)[1])
    if x is None or y is None:
        return None
    return (rect["x"] + rect["w"] * x, rect["y"] + rect["h"] * y)


def _segment_hits(x1, y1, x2, y2, rect, pad=2) -> bool:
    return (
        min(x1, x2) < rect["x"] + rect["w"] - pad
        and rect["x"] + pad < max(x1, x2) + 0.001
        and min(y1, y2) < rect["y"] + rect["h"] - pad
        and rect["y"] + pad < max(y1, y2) + 0.001
    )


def check_routes(cells: dict, warnings: list) -> tuple:
    """An edge drawn through a shape it does not connect.

    Only edges whose style fixes both ends are checked: those are the ones the
    layout routes itself, and the route can be reconstructed exactly. A
    sequence message and a timeline dependency fix neither end, so draw.io
    routes them and there is nothing here to reconstruct -- and nothing is
    claimed about them. Of the table relations, only the two entity-relation
    types are anchored, so only those are measured.

    Returns (measured, total), because a count of crossings means nothing
    without the count of edges it was taken over.
    """
    solid = {}
    for cell_id, cell in cells.items():
        if cell.get("vertex") != "1":
            continue
        style = cell.get("style") or ""
        element = cell.find("mxGeometry")
        if element is not None and element.get("relative") == "1":
            continue
        if "edgeLabel" in style or "umlFrame" in style:
            continue
        rect = _absolute(cells, cell_id)
        if rect:
            solid[cell_id] = rect

    measured = total = 0
    for cell_id, cell in cells.items():
        if cell.get("edge") != "1":
            continue
        total += 1
        style = cell.get("style") or ""
        source, target = cell.get("source"), cell.get("target")
        if not source or not target:
            continue
        a, b = solid.get(source), solid.get(target)
        if not a or not b:
            continue
        start, end = _anchor(style, "exit", a), _anchor(style, "entry", b)
        if start is None or end is None:
            continue
        measured += 1

        points = [start]
        geometry = cell.find("mxGeometry")
        array = geometry.find("Array") if geometry is not None else None
        if array is not None:
            for point in array.findall("mxPoint"):
                try:
                    points.append((float(point.get("x", 0)), float(point.get("y", 0))))
                except ValueError:
                    pass
        else:
            # no waypoints: out perpendicular, across at the midpoint, in
            if abs(start[1] - end[1]) > abs(start[0] - end[0]):
                mid = (start[1] + end[1]) / 2
                points += [(start[0], mid), (end[0], mid)]
            else:
                mid = (start[0] + end[0]) / 2
                points += [(mid, start[1]), (mid, end[1])]
        points.append(end)

        skip = {source, target}
        for cell_end in (source, target):
            skip |= _ancestors(cells, cell_end) | _descendants(cells, cell_end)
        crossed = set()
        for i in range(len(points) - 1):
            (x1, y1), (x2, y2) = points[i], points[i + 1]
            for other_id, rect in solid.items():
                if other_id in skip:
                    continue
                if _segment_hits(x1, y1, x2, y2, rect):
                    crossed.add(other_id)
        if crossed:
            warnings.append(
                f"edge {cell_id!r}: its route passes through "
                f"{', '.join(sorted(crossed))}, which it does not connect"
            )
    return measured, total


def check_geometry(root, cells: dict, errors: list, warnings: list) -> None:
    model = root.find(".//mxGraphModel")
    if model is None:
        return
    try:
        page_w = float(model.get("pageWidth", 0))
        page_h = float(model.get("pageHeight", 0))
    except ValueError:
        page_w = page_h = 0

    boxes = []
    for cell_id, cell in cells.items():
        if cell.get("vertex") != "1":
            continue
        geometry = _geometry_of(cell)
        if geometry is None:
            continue
        style = cell.get("style") or ""

        # A label riding on an edge is positioned along its parent rather
        # than sized: relative="1" and no width or height is correct there.
        element = cell.find("mxGeometry")
        if element is not None and element.get("relative") == "1":
            continue

        if geometry["w"] <= 0 or geometry["h"] <= 0:
            errors.append(
                f"cell {cell_id!r}: {geometry['w']}x{geometry['h']} -- a shape with no "
                "size is invisible and cannot be clicked"
            )
            continue

        parent = cell.get("parent")
        absolute = dict(geometry)
        if parent not in (None, "1", "0"):
            parent_geometry = _geometry_of(cells[parent]) if parent in cells else None
            if parent_geometry:
                absolute["x"] += parent_geometry["x"]
                absolute["y"] += parent_geometry["y"]

        if page_w and (absolute["x"] < 0 or absolute["y"] < 0):
            warnings.append(f"cell {cell_id!r}: sits at a negative coordinate")
        if page_w and absolute["x"] + absolute["w"] > page_w + 1:
            warnings.append(f"cell {cell_id!r}: runs past the right edge of the page")
        if page_h and absolute["y"] + absolute["h"] > page_h + 1:
            warnings.append(f"cell {cell_id!r}: runs past the bottom of the page")

        if any(marker in style for marker in _OVERLAPS_BY_DESIGN):
            continue
        boxes.append((cell_id, parent, absolute))

    for i, (id_a, parent_a, rect_a) in enumerate(boxes):
        for id_b, parent_b, rect_b in boxes[i + 1 :]:
            if parent_a == parent_b and _rects_overlap(rect_a, rect_b):
                errors.append(
                    f"cells {id_a!r} and {id_b!r} sit on top of one another. "
                    "The layout put two shapes in the same place"
                )


def check_round_trip(root, graph: dict, errors: list, warnings: list) -> None:
    """Pass 5. Everything the intent asked for has to be findable in the XML.

    This is what catches a builder that quietly drops a node: the shape count
    looks plausible and only a comparison against the intent notices.
    """
    values, ids = {}, set()
    for cell in root.iter("mxCell"):
        cell_id = cell.get("id")
        if cell_id:
            ids.add(cell_id)
            values[cell_id] = cell.get("value") or ""

    payload = graph.get("payload") or {}
    layout = graph.get("layout")

    if layout in ("layered", "container"):
        wanted = [(n["id"], n.get("label", "")) for n in payload.get("nodes") or []]
        link_count = len(payload.get("edges") or [])
    elif layout == "table":
        wanted = [(e["id"], e.get("label", "")) for e in payload.get("entities") or []]
        link_count = len(payload.get("relations") or [])
    elif layout == "lifeline":
        wanted = [(a["id"], a.get("label", "")) for a in payload.get("actors") or []]
        link_count = len(payload.get("messages") or [])
    elif layout == "timeline":
        wanted = [(t["id"], t.get("label", "")) for t in payload.get("tracks") or []]
        link_count = sum(
            len(s.get("depends_on") or []) for s in payload.get("spans") or []
        )
        # A span is the content of a timeline, so losing one is the failure
        # this pass exists to catch. Tracks are checked by the loop below.
        for span in payload.get("spans") or []:
            cell_id = f"s_{escape.identifier(span['id'], 'x')}"
            if cell_id not in ids:
                errors.append(
                    f"round trip: span {span['id']!r} is in the intent but not in the XML"
                )
    else:
        warnings.append(f"round trip: layout {layout!r} is not understood here")
        return

    for node_id, label in wanted:
        cell_id = f"n_{escape.identifier(node_id, 'x')}"
        if cell_id not in ids:
            errors.append(f"round trip: {node_id!r} is in the intent but not in the XML")
            continue
        expected = _xml_unescape(escape.drawio_value(label))
        if expected and expected not in values[cell_id]:
            errors.append(
                f"round trip: {node_id!r} is drawn as {values[cell_id]!r}, "
                f"the intent says {expected!r}"
            )

    prefix = "m_" if layout == "lifeline" else "e_"
    drawn = sum(1 for i in ids if i.startswith(prefix) and not i.endswith(("_note", "s", "t")))
    if drawn < link_count:
        errors.append(
            f"round trip: the intent has {link_count} links, the XML draws {drawn}"
        )


def validate_file(path, graph_path=None) -> tuple:
    """(errors, warnings, measured).

    'measured' says how many of the edges the route check could reconstruct,
    out of how many there are. A crossing count without it reads as a
    statement about every edge, and it is not one.
    """
    errors: list = []
    warnings: list = []
    measured = {"routes": 0, "edges": 0}
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read {path}: {exc}"], [], measured

    if "<mxGraphModel" not in text and "<diagram" in text:
        return (
            [
                "the model is compressed. Files written by this toolchain are not; "
                "use drawio_read.py to unpack somebody else's"
            ],
            [],
            measured,
        )

    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return [f"not well-formed XML: {exc}"], [], measured

    # A cell somebody gave data to in draw.io comes back wrapped, and so does
    # the root cell of every file this toolchain writes.
    data = mxmodel.unwrap(root)
    embedded, problem = mxmodel.embedded_intent(data)
    if problem:
        errors.append(problem)

    cells = check_model(root, errors, warnings)
    if cells:
        check_geometry(root, cells, errors, warnings)
        check_labels_fit(cells, warnings)
        routes, edges = check_routes(cells, warnings)
        measured = {"routes": routes, "edges": edges}

    if graph_path:
        try:
            graph = schema.load(graph_path)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            if embedded is not None and embedded != graph:
                errors.append(
                    f"the file carries a different intent from {graph_path}: one of "
                    "them is stale. Redraw from the one that is right"
                )
            check_round_trip(root, graph, errors, warnings)
    elif embedded is not None:
        check_round_trip(root, embedded, errors, warnings)

    return errors, warnings, measured


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate a generated .drawio file.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--graph", type=Path, help="the graph.json it came from, for a round trip")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true", help="print only problems")
    args = parser.parse_args(argv)

    if args.graph and len(args.paths) > 1:
        print("error: --graph takes one .drawio at a time", file=sys.stderr)
        return 2

    results, failed = [], False
    for path in args.paths:
        errors, warnings, measured = validate_file(path, args.graph)
        failed = failed or bool(errors)
        results.append(
            {
                "path": str(path),
                "ok": not errors,
                "errors": errors,
                "warnings": warnings,
                "measured": measured,
            }
        )

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for r in results:
            if r["errors"]:
                print(f"FAIL  {r['path']}")
            elif r["warnings"]:
                print(f"ok    {r['path']}  ({len(r['warnings'])} to look at)")
            elif not args.quiet:
                print(f"ok    {r['path']}")
            for e in r["errors"]:
                print(f"  error: {e}")
            for w in r["warnings"]:
                print(f"  note:  {w}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

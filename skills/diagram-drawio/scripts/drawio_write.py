"""graph.json -> an uncompressed .drawio file.

The twin of mermaid_write.py, reading the same intent. Where Mermaid decides
its own layout and we cannot influence it, draw.io decides nothing: every
shape carries explicit coordinates, computed in layouts.py. This file does
one job on top of that -- turn placed boxes into mxCells, with a style
vocabulary where colour and shape mean something fixed across every type.

Output is uncompressed on purpose. draw.io normally deflates the model into
base64, which makes the file unreadable in a diff and unreadable to the next
agent that opens it. Uncompressed costs nothing and keeps both.

All seventeen types, over five layouts:

    architecture, flowchart, state, cicd  -> layered
    data-model, class, db-schema, reqs    -> table
    sequence                              -> lifeline
    deployment, swimlane, dfd, c4, threat -> container
    gantt, user-journey, git-graph        -> timeline

Usage:
    python drawio_write.py <graph.json> [-o out.drawio]

Exit code 2 when the graph does not validate: nothing is written.

stdlib only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SKILLS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_SKILLS / "_shared"))
sys.path.insert(0, str(_SKILLS / "validate"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import escape  # noqa: E402
import layouts  # noqa: E402
import mxmodel  # noqa: E402
import schema  # noqa: E402
from validate_graph import validate_graph  # noqa: E402

FONT = "fontFamily=Helvetica;fontSize=12;"

# --- the style vocabulary --------------------------------------------------
#
# One convention for every type. A reader who learns it on an architecture
# diagram reads a threat model with it. Shape says what kind of thing it is;
# colour says which family it belongs to; a dashed outline always means "not
# ours to change".

_BASE = f"whiteSpace=wrap;html=1;{FONT}"

INK = "#1F2933"
STORE_FILL, STORE_LINE = "#EAF2FF", "#2B5D9B"
QUEUE_FILL, QUEUE_LINE = "#FFF4E0", "#A96A12"
OUTSIDE_FILL, OUTSIDE_LINE = "#F2F3F4", "#7B8794"
CHOICE_FILL, CHOICE_LINE = "#FFF9DB", "#A9861A"
TERMINAL_FILL, TERMINAL_LINE = "#E9F5EE", "#2C7A4B"

STYLES = {
    # the ordinary thing: a service, a step, a state
    "service": f"rounded=0;{_BASE}fillColor=#FFFFFF;strokeColor={INK};",
    "process": f"rounded=0;{_BASE}fillColor=#FFFFFF;strokeColor={INK};",
    "job": f"rounded=0;{_BASE}fillColor=#FFFFFF;strokeColor={INK};",
    "component": f"rounded=1;arcSize=12;{_BASE}fillColor=#FFFFFF;strokeColor={INK};",
    "state": f"rounded=1;arcSize=20;{_BASE}fillColor=#FFFFFF;strokeColor={INK};",
    # state that outlives a request
    "store": (
        f"shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=14;{_BASE}"
        f"fillColor={STORE_FILL};strokeColor={STORE_LINE};"
    ),
    "artifact": (
        f"shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=14;{_BASE}"
        f"fillColor={STORE_FILL};strokeColor={STORE_LINE};"
    ),
    # data in motion
    "queue": (
        f"shape=parallelogram;perimeter=parallelogramPerimeter;fixedSize=1;size=18;{_BASE}"
        f"fillColor={QUEUE_FILL};strokeColor={QUEUE_LINE};"
    ),
    "io": (
        f"shape=parallelogram;perimeter=parallelogramPerimeter;fixedSize=1;size=18;{_BASE}"
        f"fillColor=#FFFFFF;strokeColor={INK};"
    ),
    # not ours
    "external": f"rounded=0;dashed=1;{_BASE}fillColor={OUTSIDE_FILL};strokeColor={OUTSIDE_LINE};",
    "actor": f"ellipse;{_BASE}fillColor=#FFFFFF;strokeColor={INK};",
    # a question
    "decision": f"rhombus;{_BASE}fillColor={CHOICE_FILL};strokeColor={CHOICE_LINE};",
    "gate": f"rhombus;{_BASE}fillColor={CHOICE_FILL};strokeColor={CHOICE_LINE};",
    "choice": f"rhombus;{_BASE}fillColor={CHOICE_FILL};strokeColor={CHOICE_LINE};",
    # the way in and the way out
    "start": f"rounded=1;arcSize=50;{_BASE}fillColor={TERMINAL_FILL};strokeColor={TERMINAL_LINE};",
    "end": f"rounded=1;arcSize=50;{_BASE}fillColor={TERMINAL_FILL};strokeColor={TERMINAL_LINE};",
    # drawn elsewhere
    "subroutine": f"shape=process;backgroundOutline=1;{_BASE}fillColor=#FFFFFF;strokeColor={INK};",
    "environment": f"shape=process;backgroundOutline=1;{_BASE}fillColor=#FFFFFF;strokeColor={INK};",
}
DEFAULT_STYLE = f"rounded=0;{_BASE}fillColor=#FFFFFF;strokeColor={INK};"

# labelBackgroundColor is the one thing that makes a label readable where a
# route has to pass over something. Without it the text and whatever lies
# underneath it are drawn on top of each other.
EDGE_BASE = (
    f"edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;{FONT}strokeColor={INK};"
    "labelBackgroundColor=#FFFFFF;"
)
EDGE_STYLES = {
    "flow": EDGE_BASE,
    "request": EDGE_BASE,
    "transition": EDGE_BASE,
    "write": EDGE_BASE,
    "response": EDGE_BASE + "dashed=1;",
    "dep": EDGE_BASE + "dashed=1;",
    "read": EDGE_BASE + "dashed=1;",
    "async": EDGE_BASE + "endArrow=oval;endFill=0;endSize=8;",
    "trigger": EDGE_BASE + "strokeWidth=3;",
}

ENTITY_STYLE = (
    f"swimlane;startSize={layouts.HEADER_H};html=1;{FONT}"
    f"fillColor=#FFFFFF;strokeColor={INK};fontStyle=1;align=center;"
    "horizontalStack=0;resizeParent=0;collapsible=0;"
)
ROW_STYLE = (
    f"text;html=1;{FONT}align=left;verticalAlign=middle;spacingLeft=10;"
    "strokeColor=none;fillColor=none;"
)
KEY_ROW_STYLE = ROW_STYLE + "fontStyle=1;"

LIFELINE_STYLE = (
    f"shape=umlLifeline;perimeter=lifelinePerimeter;{_BASE}"
    f"fillColor=#FFFFFF;strokeColor={INK};container=0;collapsible=0;"
    f"recursiveResize=0;outlineConnect=0;size={layouts.ACTOR_H};"
)
# A message label sits above its arrow and crosses every lifeline the arrow
# spans, so it needs the same backing every other edge label has.
_MSG = f"html=1;{FONT}verticalAlign=bottom;labelBackgroundColor=#FFFFFF;"
MESSAGE_STYLES = {
    "request": _MSG + f"endArrow=block;endFill=1;strokeColor={INK};",
    "response": _MSG + f"endArrow=open;dashed=1;strokeColor={INK};",
    "async": _MSG + f"endArrow=open;strokeColor={INK};",
    "self": _MSG + f"endArrow=block;endFill=1;strokeColor={INK};",
    "create": _MSG + f"endArrow=block;dashed=1;strokeColor={INK};",
    "destroy": _MSG + f"endArrow=cross;strokeColor={INK};",
}
DEFAULT_MESSAGE_STYLE = MESSAGE_STYLES["request"]

TRUST_LINE = "#B3261E"

#: A container says what kind of boundary it is by how it is drawn. Three
#: kinds, because three is what a reader can hold: a thing that runs
#: somewhere, a lane belonging to somebody, and a line trust does not cross.
GROUP_STYLES = {
    "group": (
        f"swimlane;startSize={layouts.GROUP_HEADER};html=1;{FONT}fillColor=#FAFBFC;"
        f"strokeColor={OUTSIDE_LINE};fontStyle=1;align=left;spacingLeft=8;"
        "collapsible=0;container=1;"
    ),
    "lane": (
        f"swimlane;startSize={layouts.GROUP_HEADER};html=1;{FONT}fillColor=#FFFFFF;"
        f"strokeColor={INK};fontStyle=1;align=left;spacingLeft=8;"
        "collapsible=0;container=1;"
    ),
    "trust": (
        f"rounded=0;html=1;{FONT}dashed=1;dashPattern=8 8;strokeWidth=2;"
        f"strokeColor={TRUST_LINE};fontColor={TRUST_LINE};fillColor=none;"
        "verticalAlign=top;align=left;spacingLeft=8;spacingTop=4;"
        "collapsible=0;container=1;"
    ),
}
GROUP_STYLES["node"] = GROUP_STYLES["group"]
GROUP_STYLES["system"] = GROUP_STYLES["group"]
GROUP_STYLES["boundary"] = GROUP_STYLES["trust"]

TRACK_STYLE = (
    f"swimlane;horizontal=0;html=1;{FONT}fillColor=#FFFFFF;strokeColor={OUTSIDE_LINE};"
    "fontStyle=1;collapsible=0;container=1;"
)
AXIS_STYLE = (
    f"text;html=1;{FONT}fontSize=10;align=left;verticalAlign=bottom;"
    f"strokeColor=none;fillColor=none;fontColor={OUTSIDE_LINE};"
)
SPAN_STYLES = {
    "task": f"rounded=1;arcSize=16;{_BASE}fillColor=#EAF2FF;strokeColor={STORE_LINE};",
    "step": f"rounded=1;arcSize=16;{_BASE}fillColor=#EAF2FF;strokeColor={STORE_LINE};",
    "branch": f"rounded=1;arcSize=16;{_BASE}fillColor=#FAFBFC;strokeColor={OUTSIDE_LINE};",
    "milestone": f"rhombus;{_BASE}fillColor={CHOICE_FILL};strokeColor={CHOICE_LINE};",
    "commit": f"ellipse;{_BASE}fillColor=#FFFFFF;strokeColor={INK};",
    "merge": f"ellipse;{_BASE}fillColor={TERMINAL_FILL};strokeColor={TERMINAL_LINE};",
}
DEFAULT_SPAN_STYLE = SPAN_STYLES["task"]

#: A journey score, drawn as a colour rather than as a number the reader has
#: to translate. Five steps from "this hurt" to "this was fine".
SCORE_FILL = {
    0: "#F8D7DA", 1: "#F8D7DA", 2: "#FFE8CC",
    3: "#FFF9DB", 4: "#E4F1E6", 5: "#D4EDDA",
}

FRAGMENT_STYLE = (
    f"shape=umlFrame;whiteSpace=wrap;html=1;{FONT}width=70;height=26;"
    f"fillColor=none;strokeColor={OUTSIDE_LINE};align=left;verticalAlign=top;"
)

RELATION_BASE = (
    f"edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;{FONT}strokeColor={INK};"
    "labelBackgroundColor=#FFFFFF;"
)
CLASS_RELATIONS = {
    "inherit": RELATION_BASE + "endArrow=block;endFill=0;endSize=12;",
    "implement": RELATION_BASE + "endArrow=block;endFill=0;endSize=12;dashed=1;",
    "compose": RELATION_BASE + "startArrow=diamondThin;startFill=1;startSize=12;endArrow=none;",
    "aggregate": RELATION_BASE + "startArrow=diamondThin;startFill=0;startSize=12;endArrow=none;",
    "assoc": RELATION_BASE + "endArrow=open;",
    "dep": RELATION_BASE + "endArrow=open;dashed=1;",
    "satisfies": RELATION_BASE + "endArrow=open;dashed=1;",
    "verifies": RELATION_BASE + "endArrow=open;dashed=1;",
    "derives": RELATION_BASE + "endArrow=open;dashed=1;",
    "refines": RELATION_BASE + "endArrow=open;dashed=1;",
    "traces": RELATION_BASE + "endArrow=open;dashed=1;",
}

#: cardinality -> the text drawn at each end of an ER relation.
ER_ENDS = {
    "1-1": ("1", "1"),
    "1-n": ("1", "n"),
    "n-1": ("n", "1"),
    "n-n": ("n", "n"),
}


class GenerationError(Exception):
    """Raised when the graph is sound but this format cannot carry it."""


# ---------------------------------------------------------------------------
# XML, built by hand because the model is small and the escaping is ours
# ---------------------------------------------------------------------------


def _cell(cell_id: str, value: str, style: str, geometry: str, *, edge=False, parent="1") -> str:
    kind = 'edge="1"' if edge else 'vertex="1"'
    return (
        f'        <mxCell id="{cell_id}" value="{value}" style="{style}" '
        f'{kind} parent="{parent}">\n{geometry}\n        </mxCell>'
    )


def _geometry(x, y, w, h) -> str:
    return (
        f'          <mxGeometry x="{round(x)}" y="{round(y)}" '
        f'width="{round(w)}" height="{round(h)}" as="geometry" />'
    )


def _edge_geometry(x1, y1, x2, y2, waypoints=()) -> str:
    points = ""
    if waypoints:
        inner = "".join(
            f'\n              <mxPoint x="{round(px)}" y="{round(py)}" />' for px, py in waypoints
        )
        points = f'\n            <Array as="points">{inner}\n            </Array>'
    return (
        '          <mxGeometry relative="1" as="geometry">'
        f'\n            <mxPoint x="{round(x1)}" y="{round(y1)}" as="sourcePoint" />'
        f'\n            <mxPoint x="{round(x2)}" y="{round(y2)}" as="targetPoint" />'
        f"{points}"
        "\n          </mxGeometry>"
    )


def _comment(text: str) -> str:
    """An XML comment cannot contain a double hyphen, and a label from a
    codebase very well might."""
    clean = escape.normalize(text).replace("\n", " ")
    while "--" in clean:
        clean = clean.replace("--", "-")
    return f"    <!-- {clean.rstrip('-')} -->"


def _sid(prefix: str, raw: str) -> str:
    return f"{prefix}_{escape.identifier(raw, 'x')}"


# ---------------------------------------------------------------------------
# one builder per layout
# ---------------------------------------------------------------------------


#: which side of a shape an endpoint sits on
_ANCHOR = {
    "top": ("0.5", "0"),
    "bottom": ("0.5", "1"),
    "left": ("0", "0.5"),
    "right": ("1", "0.5"),
}


def _sides(edge: dict) -> str:
    """The exit and entry sides layouts.py chose for this edge."""
    style = ""
    for end, key in (("exit", "exit"), ("entry", "entry")):
        side = edge.get(end)
        if side in _ANCHOR:
            x, y = _ANCHOR[side]
            style += f"{key}X={x};{key}Y={y};{key}Dx=0;{key}Dy=0;"
    return style


def _waypoints(edge: dict) -> str:
    """The detour, if the router gave this edge one."""
    points = edge.get("points") or []
    if not points:
        return '          <mxGeometry relative="1" as="geometry" />'
    inner = "".join(
        chr(10) + f'              <mxPoint x="{round(x)}" y="{round(y)}" />' for x, y in points
    )
    return (
        '          <mxGeometry relative="1" as="geometry">'
        + chr(10)
        + f'            <Array as="points">{inner}'
        + chr(10)
        + "            </Array>"
        + chr(10)
        + "          </mxGeometry>"
    )


def _node_cells(placed: dict) -> list:
    cells = []
    for box in placed["boxes"]:
        style = STYLES.get(box.get("role"), DEFAULT_STYLE)
        cells.append(
            _cell(
                _sid("n", box["id"]),
                escape.drawio_value(box["label"]),
                style,
                _geometry(box["x"], box["y"], box["w"], box["h"]),
            )
        )
    return cells


def build_layered(graph: dict, placed: dict) -> list:
    cells = _node_cells(placed)
    for i, edge in enumerate(placed['edges']):
        style = EDGE_STYLES.get(edge.get("kind"), EDGE_BASE)
        style += _sides(edge)
        cells.append(
            f'        <mxCell id="e_{i}" value="{escape.drawio_value(edge.get("label") or "")}" '
            f'style="{style}" edge="1" parent="1" '
            f'source="{_sid("n", edge["from"])}" target="{_sid("n", edge["to"])}">'
            + chr(10)
            + _waypoints(edge)
            + chr(10)
            + "        </mxCell>"
        )
    return cells


def build_table(graph: dict, placed: dict) -> list:
    cells = []
    for box in placed["boxes"]:
        title = box["label"]
        if box.get("role"):
            title = f"<<{box['role']}>>\n{title}"
        cells.append(
            _cell(
                _sid("n", box["id"]),
                escape.drawio_value(title),
                ENTITY_STYLE,
                _geometry(box["x"], box["y"], box["w"], box["h"]),
            )
        )

    parents = {b["id"]: b for b in placed["boxes"]}
    for row in placed["rows"]:
        parent = parents[row["parent"]]
        style = KEY_ROW_STYLE if row.get("role") in ("pk", "uk") else ROW_STYLE
        cells.append(
            _cell(
                _sid("r", row["id"]),
                escape.drawio_value(row["label"]),
                style,
                _geometry(0, row["y"] - parent["y"], row["w"], row["h"]),
                parent=_sid("n", row["parent"]),
            )
        )

    graph_type = graph.get("type")
    for i, relation in enumerate(placed["edges"]):
        if graph_type in ("data-model", "db-schema"):
            style = RELATION_BASE + "endArrow=none;"
            near, far = ER_ENDS.get(relation.get("cardinality"), ("", ""))
            if relation.get("optional"):
                far = f"0..{far}"
        else:
            style = CLASS_RELATIONS.get(relation.get("kind"), RELATION_BASE)
            near = far = ""
        style += _sides(relation)
        geometry = _waypoints(relation)
        cells.append(
            f'        <mxCell id="e_{i}" value="{escape.drawio_value(relation.get("label") or "")}" '
            f'style="{style}" edge="1" parent="1" '
            f'source="{_sid("n", relation["from"])}" target="{_sid("n", relation["to"])}">\n'
            + geometry
            + "\n        </mxCell>"
        )
        for suffix, text, position in (("s", near, -1), ("t", far, 1)):
            if not text:
                continue
            cells.append(
                f'        <mxCell id="e_{i}{suffix}" value="{escape.drawio_value(text)}" '
                f'style="edgeLabel;html=1;{FONT}align=center;verticalAlign=middle;resizable=0;points=[];" '
                f'vertex="1" connectable="0" parent="e_{i}">\n'
                f'          <mxGeometry x="{position * 0.85}" relative="1" as="geometry">\n'
                '            <mxPoint as="offset" />\n'
                "          </mxGeometry>\n"
                "        </mxCell>"
            )
    return cells


def build_lifeline(graph: dict, placed: dict) -> list:
    cells = []
    bottom = placed["lifeline_bottom"]

    for frame in placed["fragments"]:
        cells.append(
            _cell(
                _sid("f", f"{frame['kind']}_{frame['y']}"),
                escape.drawio_value(f"{frame['kind']} {frame['label']}".strip()),
                FRAGMENT_STYLE,
                _geometry(frame["x"], frame["y"], frame["w"], frame["h"]),
            )
        )

    for head in placed["boxes"]:
        cells.append(
            _cell(
                _sid("n", head["id"]),
                escape.drawio_value(head["label"]),
                LIFELINE_STYLE,
                _geometry(head["x"], head["y"], head["w"], bottom - head["y"]),
            )
        )

    for message in placed["messages"]:
        style = MESSAGE_STYLES.get(message.get("kind"), DEFAULT_MESSAGE_STYLE)
        x1, x2, y = message["x1"], message["x2"], message["y"]
        if message["from"] == message["to"]:
            # A self-message goes out, down and back. Without the waypoints it
            # is a zero-length edge and draw.io draws nothing at all.
            out = x1 + 60
            geometry = _edge_geometry(x1, y, x2, y + 30, [(out, y), (out, y + 30)])
        else:
            geometry = _edge_geometry(x1, y, x2, y)
        cells.append(
            _cell(
                f"m_{message['index']}",
                escape.drawio_value(message["label"]),
                style,
                geometry,
                edge=True,
            )
        )
        if message.get("note"):
            width = max(160, min(300, len(message["note"]) * layouts.CHAR_W + 24))
            lines = layouts.wrap(
                message["note"], max(8, int((width - 24) / layouts.CHAR_W))
            )
            height = max(26, len(lines) * layouts.LINE_H + 12)
            cells.append(
                _cell(
                    f"m_{message['index']}_note",
                    escape.drawio_value(message["note"]),
                    f"shape=note;whiteSpace=wrap;html=1;{FONT}size=12;"
                    f"fillColor=#FFF9DB;strokeColor={CHOICE_LINE};align=left;spacingLeft=6;",
                    _geometry(min(x1, x2) + 20, y + 8, width, height),
                )
            )
    return cells


def build_container(graph: dict, placed: dict) -> list:
    """Groups first, then what they hold.

    mxGraph gives a child coordinates relative to its parent, so every placed
    item is re-based onto whatever contains it. Emitting parents before
    children is not cosmetic: draw.io resolves parent by id as it reads.
    """
    origin = {g["id"]: g for g in placed["groups"]}
    cells = []

    def geometry_for(item: dict) -> str:
        parent = origin.get(item.get("parent"))
        dx = parent["x"] if parent else 0
        dy = parent["y"] if parent else 0
        return _geometry(item["x"] - dx, item["y"] - dy, item["w"], item["h"])

    def parent_of(item: dict) -> str:
        return _sid("n", item["parent"]) if item.get("parent") in origin else "1"

    for group in sorted(placed["groups"], key=lambda g: g["depth"]):
        cells.append(
            _cell(
                _sid("n", group["id"]),
                escape.drawio_value(group["label"]),
                GROUP_STYLES.get(group.get("role"), GROUP_STYLES["group"]),
                geometry_for(group),
                parent=parent_of(group),
            )
        )

    for box in placed["boxes"]:
        cells.append(
            _cell(
                _sid("n", box["id"]),
                escape.drawio_value(box["label"]),
                STYLES.get(box.get("role"), DEFAULT_STYLE),
                geometry_for(box),
                parent=parent_of(box),
            )
        )

    for i, edge in enumerate(placed['edges']):
        style = EDGE_STYLES.get(edge.get("kind"), EDGE_BASE)
        style += _sides(edge)
        cells.append(
            f'        <mxCell id="e_{i}" value="{escape.drawio_value(edge.get("label") or "")}" '
            f'style="{style}" edge="1" parent="1" '
            f'source="{_sid("n", edge["from"])}" target="{_sid("n", edge["to"])}">'
            + chr(10)
            + _waypoints(edge)
            + chr(10)
            + "        </mxCell>"
        )
    return cells


def build_timeline(graph: dict, placed: dict) -> list:
    """Bands on a shared axis.

    The axis is ordinal, not metric: neighbouring values sit one column
    apart whether they are a day or a quarter apart. A timeline here answers
    "what follows what", and pretending to answer "how long" would be a lie
    the layout cannot back up.
    """
    cells = []

    for tick in placed["axis"]:
        cells.append(
            _cell(
                _sid("t", f"axis_{tick['label']}"),
                escape.drawio_value(tick["label"]),
                AXIS_STYLE,
                _geometry(tick["x"], tick["y"], layouts.COL_W, layouts.AXIS_H - 6),
            )
        )

    for band in placed["tracks"]:
        style = TRACK_STYLE + f"startSize={band['label_w']};"
        cells.append(
            _cell(
                _sid("n", band["id"]),
                escape.drawio_value(band["label"]),
                style,
                _geometry(band["x"], band["y"], band["w"], band["h"]),
            )
        )

    origin = {b["id"]: b for b in placed["tracks"]}
    for span in placed["boxes"]:
        style = SPAN_STYLES.get(span.get("role"), DEFAULT_SPAN_STYLE)
        if span.get("score") is not None:
            style += f"fillColor={SCORE_FILL.get(span['score'], '#FFFFFF')};"
        band = origin.get(span.get("track"))
        dx = band["x"] if band else 0
        dy = band["y"] if band else 0
        label = span["label"]
        if span.get("label_outside"):
            # A milestone is a point in time and stays small, so its label is
            # drawn to the right of it rather than crushed inside.
            style += "verticalLabelPosition=middle;labelPosition=right;align=left;spacingLeft=6;"
        cells.append(
            _cell(
                _sid("s", span["id"]),
                escape.drawio_value(label),
                style,
                _geometry(span["x"] - dx, span["y"] - dy, span["w"], span["h"]),
                parent=_sid("n", span["track"]) if band else "1",
            )
        )

    for i, edge in enumerate(placed["edges"]):
        cells.append(
            f'        <mxCell id="e_{i}" value="" style="{EDGE_BASE}dashed=1;" '
            f'edge="1" parent="1" source="{_sid("s", edge["from"])}" '
            f'target="{_sid("s", edge["to"])}">'
            + chr(10)
            + _waypoints(edge)
            + chr(10)
            + "        </mxCell>"
        )
    return cells


BUILDERS = {
    "layered": build_layered,
    "table": build_table,
    "lifeline": build_lifeline,
    "container": build_container,
    "timeline": build_timeline,
}


# ---------------------------------------------------------------------------
# entry points
# ---------------------------------------------------------------------------


def render(graph: dict) -> str:
    layout = graph.get("layout")
    if layout not in BUILDERS:
        raise GenerationError(
            f"layout {layout!r} is not drawn yet in draw.io; "
            f"available now: {', '.join(sorted(BUILDERS))}"
        )
    try:
        placed = layouts.place(graph["payload"], layout, graph.get("type") or "")
    except KeyError as exc:
        raise GenerationError(f"no layout named {exc}") from exc

    cells = BUILDERS[layout](graph, placed)
    width, height = placed["canvas"]

    meta = graph.get("meta") or {}
    notes = [
        _comment(f"type: {graph.get('type')} | layout: {layout}"),
        _comment(
            f"scope: {meta.get('scope', '')} | detail: {meta.get('detail')}"
            f" | audience: {meta.get('audience')}"
        ),
    ]
    for dropped in meta.get("dropped") or []:
        notes.append(_comment(f"dropped: {dropped.get('what')} - {dropped.get('why')}"))
    override = (meta.get("budget_override") or {}).get("reason") if meta.get("budget_override") else None
    if override:
        notes.append(_comment(f"over budget on purpose: {override}"))

    body = "\n".join(cells)
    return (
        '<mxfile host="tech-documentation-writer" type="device">\n'
        + "\n".join(notes)
        + f'\n  <diagram id="{escape.identifier(meta.get("title", "diagram"), "diagram")}" '
        f'name="{escape.drawio_attr(meta.get("title", "Diagram"))}">\n'
        f'    <mxGraphModel dx="{width + 200}" dy="{height + 200}" grid="1" gridSize="10" '
        'guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
        f'pageWidth="{max(850, width + 80)}" pageHeight="{max(1100, height + 80)}" '
        'math="0" shadow="0">\n'
        "      <root>\n"
        # The intent rides on the root cell, so the file can be redrawn
        # without its graph.json. mxmodel.py says why there and nowhere else.
        f'        <object label="" id="0" {mxmodel.INTENT_ATTR}="{mxmodel.intent_attr(graph)}">\n'
        "          <mxCell />\n"
        "        </object>\n"
        '        <mxCell id="1" parent="0" />\n'
        f"{body}\n"
        "      </root>\n"
        "    </mxGraphModel>\n"
        "  </diagram>\n"
        "</mxfile>\n"
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Turn a graph.json into a .drawio file.")
    parser.add_argument("graph", type=Path)
    parser.add_argument("-o", "--out", type=Path, help="write here instead of stdout")
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
        text = render(graph)
    except GenerationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(text)

    print(
        "note: the model is well formed and every shape has coordinates, but nothing "
        "here has opened it. Check it in draw.io before shipping it.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

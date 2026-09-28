"""Coordinates for draw.io.

draw.io has no layout engine. An mxGraphModel is a list of shapes with
explicit x, y, width and height, so every position on the page is computed
here. Mermaid is the opposite -- it lays out and we cannot influence it --
which is why the two formats agree on what a diagram says and never on how
it looks.

All five layouts:

    layered    nodes on ranks, top to bottom      architecture, flowchart, state
    table      a header box with rows under it    data model, class, requirements
    lifeline   columns with a time axis           sequence
    container  nested frames holding nodes        deployment, swimlane, DFD, C4
    timeline   bands on a shared axis             Gantt, user journey, branches

Everything returns the same shape: a dict of boxes, edges and canvas size,
which drawio_write.py turns into XML without making any further decisions.

stdlib only.
"""

from __future__ import annotations

MARGIN = 40

# 12px Helvetica, measured the only way that matters here: wide enough that a
# label never overflows its box. Being a few pixels generous costs nothing;
# being tight clips text and nothing in the toolchain would notice.
CHAR_W = 7.4
LINE_H = 16

MIN_W, MAX_W = 120, 240
PAD_X, PAD_Y = 16, 14

RANK_GAP = 70          # vertical space between layered ranks
NODE_GAP = 30          # horizontal space between boxes on one rank

ROW_H = 22             # one row inside a table box
HEADER_H = 34          # the title bar of a table box
TABLE_GAP_X, TABLE_GAP_Y = 70, 60
TABLE_GAP_X_MAX = 300   # past this a relation label is the problem, not the gap
TABLE_PER_ROW = 3

ACTOR_H = 40           # a lifeline's head box
ACTOR_GAP = 50
MSG_GAP = 46           # vertical step between messages
SELF_GAP = 68          # a self-message needs room for its loop
LIFELINE_TOP = 26      # gap between the head box and the first message
FRAGMENT_PAD = 22

GROUP_HEADER = 30      # the title bar of a container
GROUP_PAD = 18         # space between a container's edge and what it holds
GROUP_GAP = 22         # space between two things inside the same container
GROUP_ROW_MAX = 620    # a container wraps its contents past this width
CONTAINER_GAP_X = 70   # between top-level frames: room for a labelled edge
CONTAINER_GAP_Y = 96
CORRIDOR_GAP = 26      # between the content and the first detour lane
CORRIDOR_STEP = 18     # between one detour lane and the next

SPAN_H = 28            # one span, and one sub-row of a track
SPAN_GAP = 6
TRACK_GAP = 8
AXIS_H = 26            # the tick strip above the bands
COL_W = 96             # the floor; the real width is taken from the labels
COL_W_MAX = 320
SPAN_MIN_W = 74
MILESTONE_W = 26


def wrap(label: str, max_chars: int) -> list:
    """Break a label into lines on word boundaries.

    A word longer than the line is left alone rather than hyphenated: an
    identifier split across two lines is harder to read than one that runs
    a little wide.
    """
    words = str(label).split()
    if not words:
        return [""]
    lines, current = [], words[0]
    for word in words[1:]:
        if len(current) + 1 + len(word) <= max_chars:
            current = f"{current} {word}"
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def measure(label: str, min_w: int = MIN_W, max_w: int = MAX_W) -> tuple:
    """Box size for a label, and the lines it was broken into."""
    text = str(label)
    words = text.split() or [""]
    longest_word = max(len(w) for w in words)
    single = len(text) * CHAR_W + PAD_X * 2
    if single <= max_w:
        lines = [text]
        width = max(min_w, single)
    else:
        max_chars = int((max_w - PAD_X * 2) / CHAR_W)
        lines = wrap(text, max(max_chars, longest_word))
        width = max(min_w, min(max_w, max(len(l) for l in lines) * CHAR_W + PAD_X * 2))
    height = max(40, len(lines) * LINE_H + PAD_Y * 2)
    return round(width), round(height), lines


def _box(node: dict, kind: str = "node") -> dict:
    width, height, lines = measure(node.get("label", node.get("id", "")))
    return {
        "id": node["id"],
        "kind": kind,
        "label": node.get("label", ""),
        "role": node.get("role") or node.get("kind"),
        "note": node.get("note"),
        "lines": lines,
        "x": 0,
        "y": 0,
        "w": width,
        "h": height,
    }


# ---------------------------------------------------------------------------
# layered
# ---------------------------------------------------------------------------


def _ranks(nodes: list, edges: list) -> dict:
    """Put every node on a rank.

    An explicit `tier` is authoritative -- the author said where it goes.
    Everything else is pulled down below whatever points at it, by relaxing
    rank[to] >= rank[from] + 1 until nothing moves. The iteration is capped
    at the node count, so a cycle settles instead of spinning.
    """
    ids = [n["id"] for n in nodes]
    pinned = {n["id"]: n["tier"] for n in nodes if isinstance(n.get("tier"), int)}
    rank = {i: pinned.get(i, 0) for i in ids}

    for _ in range(len(ids)):
        moved = False
        for edge in edges:
            src, dst = edge.get("from"), edge.get("to")
            if src not in rank or dst not in rank or dst in pinned or src == dst:
                continue
            if rank[dst] < rank[src] + 1:
                rank[dst] = rank[src] + 1
                moved = True
        if not moved:
            break

    floor = min(rank.values(), default=0)
    return {i: r - floor for i, r in rank.items()}


def _order_within_ranks(rows: dict, edges: list) -> None:
    """Two barycentre passes, to stop links crossing more than they must.

    Each node slides towards the average position of what points at it. Two
    passes is where the improvement stops being visible on a nine-box diagram.
    """
    for _ in range(2):
        position = {b["id"]: i for row in rows.values() for i, b in enumerate(row)}
        for rank in sorted(rows)[1:]:
            def barycentre(box, _rank=rank):
                above = [
                    position[e["from"]]
                    for e in edges
                    if e.get("to") == box["id"] and e.get("from") in position
                ]
                return sum(above) / len(above) if above else position[box["id"]]

            rows[rank].sort(key=barycentre)


def layered(payload: dict) -> dict:
    nodes = [n for n in payload.get("nodes") or [] if isinstance(n, dict)]
    edges = [e for e in payload.get("edges") or [] if isinstance(e, dict)]
    boxes = {n["id"]: _box(n) for n in nodes}

    rank = _ranks(nodes, edges)
    rows: dict = {}
    for node in nodes:
        rows.setdefault(rank[node["id"]], []).append(boxes[node["id"]])
    _order_within_ranks(rows, edges)

    widest = 0
    for row in rows.values():
        widest = max(widest, sum(b["w"] for b in row) + NODE_GAP * (len(row) - 1))

    y = MARGIN
    for r in sorted(rows):
        row = rows[r]
        span = sum(b["w"] for b in row) + NODE_GAP * (len(row) - 1)
        x = MARGIN + (widest - span) / 2
        tallest = max(b["h"] for b in row)
        for box in row:
            box["x"] = round(x)
            box["y"] = round(y + (tallest - box["h"]) / 2)
            x += box["w"] + NODE_GAP
        y += tallest + RANK_GAP

    result = {
        "layout": "layered",
        "boxes": list(boxes.values()),
        "edges": [dict(e) for e in edges],
        "canvas": (round(widest + MARGIN * 2), round(y - RANK_GAP + MARGIN)),
    }
    route(result, result["boxes"], {})
    return result


# ---------------------------------------------------------------------------
# table
# ---------------------------------------------------------------------------


def table(payload: dict) -> dict:
    entities = [e for e in payload.get("entities") or [] if isinstance(e, dict)]
    relations = [r for r in payload.get("relations") or [] if isinstance(r, dict)]

    boxes, rows_by_entity = [], {}
    for entity in entities:
        rows = [r for r in entity.get("rows") or [] if isinstance(r, dict)]
        widest = max(
            [len(str(entity.get("label", "")))]
            + [len(_row_text(r)) for r in rows]
            or [1]
        )
        width = round(max(MIN_W + 30, min(MAX_W + 60, widest * CHAR_W + PAD_X * 2)))
        box = {
            "id": entity["id"],
            "kind": "entity",
            "label": entity.get("label", ""),
            "role": entity.get("stereotype"),
            "note": entity.get("note"),
            "lines": [entity.get("label", "")],
            "x": 0,
            "y": 0,
            "w": width,
            "h": HEADER_H + ROW_H * len(rows),  # replaced once the rows are measured
        }
        boxes.append(box)
        # A row that has to wrap needs the height to wrap into. Stacking at a
        # fixed pitch is what puts the second line over the row below.
        placed_rows, cursor = [], HEADER_H
        for i, row in enumerate(rows):
            text = _row_text(row)
            lines = wrap(text, max(6, int((width - PAD_X * 2) / CHAR_W)))
            height = max(ROW_H, len(lines) * LINE_H + 6)
            placed_rows.append(
                {
                    "id": f"{entity['id']}__r{i}",
                    "kind": "row",
                    "parent": entity["id"],
                    "label": text,
                    "lines": lines,
                    "role": row.get("key") or row.get("kind"),
                    "note": row.get("note"),
                    "x": 0,
                    "y": cursor,
                    "w": width,
                    "h": height,
                }
            )
            cursor += height
        rows_by_entity[entity["id"]] = placed_rows
        box["h"] = cursor

    # A relation label is drawn at the middle of its edge, which for two boxes
    # side by side is the gap between them. A fixed gap therefore puts the
    # label on top of both tables as soon as it is longer than the gap, so the
    # gap is sized from the widest label there is.
    longest = max((len(str(r.get("label") or "")) for r in relations), default=0)
    gap_x = round(min(TABLE_GAP_X_MAX, max(TABLE_GAP_X, longest * CHAR_W + PAD_X * 2)))

    # A simple grid. Entities are boxes of very different heights, so each
    # grid row is aligned on its top edge and the next starts below the
    # tallest of them -- nothing stretches to fill dead space.
    x = y = MARGIN
    canvas_w = 0
    for start in range(0, len(boxes), TABLE_PER_ROW):
        band = boxes[start : start + TABLE_PER_ROW]
        x = MARGIN
        for box in band:
            box["x"], box["y"] = round(x), round(y)
            x += box["w"] + gap_x
        canvas_w = max(canvas_w, x - gap_x)
        y += max(b["h"] for b in band) + TABLE_GAP_Y

    result = {
        "layout": "table",
        "boxes": boxes,
        "rows": [],
        "edges": [dict(r) for r in relations],
        "canvas": (round(canvas_w + MARGIN), round(y - TABLE_GAP_Y + MARGIN)),
    }
    # Tables in a grid are not neighbours in pairs: a link between the first
    # and third of a band goes straight through the second unless something
    # sends it round. Routed before the rows are placed, because a detour to
    # the left moves the tables and the rows have to follow them.
    route(result, boxes, {})

    for box in boxes:
        for row in rows_by_entity[box["id"]]:
            row["x"] = box["x"]
            row["y"] = box["y"] + row["y"]
    result["rows"] = [r for rows in rows_by_entity.values() for r in rows]
    return result


def _row_text(row: dict) -> str:
    """One line of a table box, in the order a reader scans it."""
    name = str(row.get("name", ""))
    if row.get("kind") == "method" and "(" not in name:
        name += "()"
    text = f"{row['visibility']}{name}" if row.get("visibility") else name
    if row.get("type"):
        text += f" : {row['type']}"
    if row.get("key"):
        text += f"  {row['key'].upper()}"
    return text.strip()


# ---------------------------------------------------------------------------
# lifeline
# ---------------------------------------------------------------------------


def lifeline(payload: dict) -> dict:
    actors = [a for a in payload.get("actors") or [] if isinstance(a, dict)]
    messages = [m for m in payload.get("messages") or [] if isinstance(m, dict)]
    fragments = [f for f in payload.get("fragments") or [] if isinstance(f, dict)]

    heads, x = [], MARGIN
    for actor in actors:
        width, _, lines = measure(actor.get("label", actor["id"]), min_w=110, max_w=180)
        heads.append(
            {
                "id": actor["id"],
                "kind": "actor",
                "label": actor.get("label", ""),
                "role": actor.get("kind"),
                "note": actor.get("note"),
                "lines": lines,
                "x": round(x),
                "y": MARGIN,
                "w": round(width),
                "h": ACTOR_H,
            }
        )
        x += width + ACTOR_GAP

    centre = {h["id"]: h["x"] + h["w"] / 2 for h in heads}

    placed, y = [], MARGIN + ACTOR_H + LIFELINE_TOP
    for i, message in enumerate(messages):
        step = SELF_GAP if message.get("from") == message.get("to") else MSG_GAP
        placed.append(
            {
                "index": i,
                "from": message.get("from"),
                "to": message.get("to"),
                "label": message.get("label", ""),
                "kind": message.get("kind"),
                "note": message.get("note"),
                "y": round(y),
                "x1": round(centre.get(message.get("from"), MARGIN)),
                "x2": round(centre.get(message.get("to"), MARGIN)),
            }
        )
        y += step
        if message.get("note"):
            y += 28

    bottom = round(y + 10)

    frames = []
    for fragment in fragments:
        start, end = fragment.get("start", 0), fragment.get("end", 0)
        touched = {m["from"] for m in placed[start : end + 1]} | {
            m["to"] for m in placed[start : end + 1]
        }
        involved = [h for h in heads if h["id"] in touched] or heads
        left = min(h["x"] for h in involved) - FRAGMENT_PAD
        right = max(h["x"] + h["w"] for h in involved) + FRAGMENT_PAD
        top = placed[start]["y"] - 30 if placed else MARGIN
        frames.append(
            {
                "kind": fragment.get("kind"),
                "label": fragment.get("label", ""),
                "x": round(left),
                "y": round(top),
                "w": round(right - left),
                "h": round(placed[end]["y"] - top + 26) if placed else 60,
            }
        )

    width = round(max([h["x"] + h["w"] for h in heads], default=MARGIN) + MARGIN)
    return {
        "layout": "lifeline",
        "boxes": heads,
        "messages": placed,
        "fragments": frames,
        "lifeline_bottom": bottom,
        "canvas": (width, bottom + MARGIN),
    }


# ---------------------------------------------------------------------------
# routing
# ---------------------------------------------------------------------------


def _hits(x1: float, y1: float, x2: float, y2: float, rect: dict, pad: float = 2) -> bool:
    """Does an axis-aligned segment pass through a rectangle?"""
    return (
        min(x1, x2) < rect["x"] + rect["w"] - pad
        and rect["x"] + pad < max(x1, x2) + 0.001
        and min(y1, y2) < rect["y"] + rect["h"] - pad
        and rect["y"] + pad < max(y1, y2) + 0.001
    )


def _direct(a: dict, b: dict) -> tuple:
    """The route draw.io draws when the exit and entry sides are fixed:
    out perpendicular, across at the midpoint, in perpendicular."""
    acx, bcx = a["x"] + a["w"] / 2, b["x"] + b["w"] / 2
    acy, bcy = a["y"] + a["h"] / 2, b["y"] + b["h"] / 2
    if b["y"] >= a["y"] + a["h"]:
        mid = (a["y"] + a["h"] + b["y"]) / 2
        return "bottom", "top", [(acx, a["y"] + a["h"]), (acx, mid), (bcx, mid), (bcx, b["y"])]
    if a["y"] >= b["y"] + b["h"]:
        mid = (a["y"] + b["y"] + b["h"]) / 2
        return "top", "bottom", [(acx, a["y"]), (acx, mid), (bcx, mid), (bcx, b["y"] + b["h"])]
    if b["x"] >= a["x"] + a["w"]:
        mid = (a["x"] + a["w"] + b["x"]) / 2
        return "right", "left", [(a["x"] + a["w"], acy), (mid, acy), (mid, bcy), (b["x"], bcy)]
    if a["x"] >= b["x"] + b["w"]:
        mid = (a["x"] + b["x"] + b["w"]) / 2
        return "left", "right", [(a["x"], acy), (mid, acy), (mid, bcy), (b["x"] + b["w"], bcy)]
    return "", "", []


def _free_band(rect: dict, obstacles: list, skip: set, downwards: bool) -> float:
    """A horizontal line just outside a shape that nothing else sits on.

    Walks away from the edge of the shape until it finds a y no obstacle
    spans. Layouts leave a gap between ranks, so this normally lands in the
    first one; the search is here for the cases where it does not.
    """
    step = 6 if downwards else -6
    y = rect["y"] + rect["h"] + 8 if downwards else rect["y"] - 8
    for _ in range(60):
        if not any(
            o["id"] not in skip and o["y"] - 2 <= y <= o["y"] + o["h"] + 2 for o in obstacles
        ):
            return y
        y += step
    return y


def route(placed: dict, obstacles: list, ancestors: dict) -> None:
    """Give every edge a side to leave on, a side to arrive on, and -- when
    the direct way is blocked -- waypoints that go round the outside.

    draw.io routes orthogonally and does not avoid anything, so a link
    spanning more than its neighbours ends up drawn straight through whatever
    sits between. Sending it out to a lane beside the diagram costs a longer
    line and buys a diagram where every crossing is a real one.

    Each detour gets its own lane, so two of them never share a corridor.
    """
    boxes = {b["id"]: b for b in placed["boxes"]}
    if not boxes:
        return

    left_edge = min(b["x"] for b in obstacles)
    right_edge = max(b["x"] + b["w"] for b in obstacles)
    lanes = {"left": 0, "right": 0}

    for edge in placed["edges"]:
        a, b = boxes.get(edge.get("from")), boxes.get(edge.get("to"))
        if not a or not b or a is b:
            continue

        exit_side, entry_side, points = _direct(a, b)
        edge["exit"], edge["entry"], edge["points"] = exit_side, entry_side, []
        if not points:
            continue

        skip = {a["id"], b["id"]} | ancestors.get(a["id"], set()) | ancestors.get(b["id"], set())
        blocked = any(
            _hits(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1], o)
            for i in range(len(points) - 1)
            for o in obstacles
            if o["id"] not in skip
        )
        if not blocked:
            continue

        # Leave vertically into the empty band below (or above) the source,
        # cross to the lane along that band, run the lane, and come back in
        # along the band beside the target. Every segment then lies either in
        # a band with nothing in it or in a lane outside the diagram, so the
        # detour cannot cross anything -- which a sideways approach could,
        # straight through whatever sits beside the shape.
        if (a["x"] + a["w"] / 2) + (b["x"] + b["w"] / 2) <= left_edge + right_edge:
            side = "left"
            lane = left_edge - CORRIDOR_GAP - lanes["left"] * CORRIDOR_STEP
        else:
            side = "right"
            lane = right_edge + CORRIDOR_GAP + lanes["right"] * CORRIDOR_STEP
        lanes[side] += 1

        down = b["y"] >= a["y"]
        band_a = _free_band(a, obstacles, skip, downwards=down)
        band_b = _free_band(b, obstacles, skip, downwards=not down)
        edge["exit"] = "bottom" if down else "top"
        edge["entry"] = "top" if down else "bottom"
        edge["points"] = [
            (round(a["x"] + a["w"] / 2), round(band_a)),
            (round(lane), round(band_a)),
            (round(lane), round(band_b)),
            (round(b["x"] + b["w"] / 2), round(band_b)),
        ]

    used = [e["points"][0][0] for e in placed["edges"] if e.get("points")]
    if used:
        low, high = min(used), max(used)
        width, height = placed["canvas"]
        shift = max(0, MARGIN - low)
        if shift:
            for item in placed["boxes"] + placed.get("groups", []):
                _shift(item, shift, 0)
            for edge in placed["edges"]:
                edge["points"] = [(x + shift, y) for x, y in edge.get("points") or []]
        placed["canvas"] = (round(max(width + shift, high + MARGIN)), height)


# ---------------------------------------------------------------------------
# container
# ---------------------------------------------------------------------------


def _arrange(items: list, top: int) -> tuple:
    """Lay a container's contents out in wrapped rows. Returns (width, height).

    Rows rather than ranks: inside a boundary the reader is being shown what
    is in it, not the order things happen in. Ordering lives on the edges,
    which draw.io routes across container walls without help.
    """
    x, y, row_h, widest = GROUP_PAD, top, 0, 0
    for item in items:
        if row_h and x + item["w"] > GROUP_ROW_MAX:
            x, y, row_h = GROUP_PAD, y + row_h + GROUP_GAP, 0
        item["x"], item["y"] = round(x), round(y)
        x += item["w"] + GROUP_GAP
        row_h = max(row_h, item["h"])
        widest = max(widest, x - GROUP_GAP)
    return widest + GROUP_PAD, y + row_h + GROUP_PAD


def _shift(item: dict, dx: float, dy: float) -> None:
    """Move a placed item and everything inside it."""
    item["x"] = round(item["x"] + dx)
    item["y"] = round(item["y"] + dy)
    for child in item.get("contents") or ():
        _shift(child, dx, dy)


def container(payload: dict, lanes: bool = False) -> dict:
    nodes = [n for n in payload.get("nodes") or [] if isinstance(n, dict)]
    edges = [e for e in payload.get("edges") or [] if isinstance(e, dict)]
    groups = [g for g in payload.get("groups") or [] if isinstance(g, dict)]

    node_boxes = {n["id"]: _box(n) for n in nodes}
    children_of: dict = {g["id"]: [] for g in groups}
    roots = []
    for group in groups:
        parent = group.get("parent")
        (children_of[parent] if parent in children_of else roots).append(group)

    def place(group: dict) -> dict:
        inner = [place(child) for child in children_of[group["id"]]]
        inner += [node_boxes[m] for m in group.get("members") or [] if m in node_boxes]
        width, height = _arrange(inner, GROUP_HEADER + GROUP_PAD)
        label_w = len(str(group.get("label", ""))) * CHAR_W + GROUP_PAD * 2
        return {
            "id": group["id"],
            "kind": "group",
            "label": group.get("label", ""),
            "role": group.get("kind") or "group",
            "note": group.get("note"),
            "lines": [group.get("label", "")],
            "contents": inner,
            "x": 0,
            "y": 0,
            "w": round(max(width, label_w, MIN_W)),
            "h": round(max(height, GROUP_HEADER + GROUP_PAD * 2)),
        }

    placed_roots = [place(group) for group in roots]

    # Lanes are not ranked. A swimlane's whole point is that the reader knows
    # which lane is whose, and that is the order the author wrote them in --
    # the flow zigzags between lanes, so ranking them by it says nothing.
    if lanes and placed_roots:
        width = max(item["w"] for item in placed_roots)
        y = MARGIN
        for item in placed_roots:
            _shift(item, MARGIN - item["x"], y - item["y"])
            item["w"] = width
            y += item["h"] + GROUP_GAP
        loose_ids = {n["id"] for n in nodes} - {
            m for g in groups for m in (g.get("members") or [])
        }
        if loose_ids:
            raise ValueError(
                "swimlane: every step belongs to a lane; "
                f"{', '.join(sorted(loose_ids))} is in none"
            )
        flat: list = []

        def collect_lane(item: dict, depth: int = 0, parent=None) -> None:
            item["depth"] = depth
            item["parent"] = parent
            flat.append(item)
            for child in item.get("contents") or ():
                collect_lane(child, depth + 1, item["id"])

        for item in placed_roots:
            collect_lane(item)
        lane_result = {
            "layout": "container",
            "boxes": [b for b in flat if b.get("kind") != "group"],
            "groups": [b for b in flat if b.get("kind") == "group"],
            "edges": [dict(e) for e in edges],
            "canvas": (round(width + MARGIN * 2), round(y - GROUP_GAP + MARGIN)),
        }
        by_id = {item["id"]: item for item in flat}
        ancestry = {}
        for item in lane_result["boxes"]:
            chain, current = set(), item.get("parent")
            while current in by_id:
                chain.add(current)
                current = by_id[current].get("parent")
            ancestry[item["id"]] = chain
        route(lane_result, lane_result["boxes"] + lane_result["groups"], ancestry)
        return lane_result

    # A node in no group sits at the top level beside the containers.
    claimed = {m for g in groups for m in (g.get("members") or [])}
    loose = [node_boxes[n["id"]] for n in nodes if n["id"] not in claimed]
    top_items = placed_roots + loose

    # Which top-level item does a node belong to? Edges are drawn between
    # nodes, but the ranking is done between the things on the page.
    owner: dict = {}
    for item in placed_roots:
        stack = [item]
        while stack:
            current = stack.pop()
            for child in current.get("contents") or ():
                if child.get("kind") == "group":
                    stack.append(child)
                else:
                    owner[child["id"]] = item["id"]
    for box in loose:
        owner[box["id"]] = box["id"]

    top_edges = [
        {"from": owner[e["from"]], "to": owner[e["to"]]}
        for e in edges
        if e.get("from") in owner and e.get("to") in owner and owner[e["from"]] != owner[e["to"]]
    ]
    rank = _ranks([{"id": i["id"]} for i in top_items], top_edges)

    rows: dict = {}
    for item in top_items:
        rows.setdefault(rank[item["id"]], []).append(item)
    _order_within_ranks(rows, top_edges)

    # Frames are spaced further apart than bare nodes are. An edge between two
    # frames carries a label, and the label is drawn on the line: without room
    # in the gap it lands on top of whatever the line is passing.
    widest = max(
        (
            sum(b["w"] for b in row) + CONTAINER_GAP_X * (len(row) - 1)
            for row in rows.values()
        ),
        default=0,
    )
    y = MARGIN
    for r in sorted(rows):
        row = rows[r]
        span = sum(b["w"] for b in row) + CONTAINER_GAP_X * (len(row) - 1)
        x = MARGIN + (widest - span) / 2
        tallest = max(b["h"] for b in row)
        for item in row:
            _shift(item, x - item["x"], y - item["y"])
            x += item["w"] + CONTAINER_GAP_X
        y += tallest + CONTAINER_GAP_Y

    flat: list = []

    def collect(item: dict, depth: int = 0, parent=None) -> None:
        item["depth"] = depth
        item["parent"] = parent
        flat.append(item)
        for child in item.get("contents") or ():
            collect(child, depth + 1, item["id"])

    for item in top_items:
        collect(item)

    result = {
        "layout": "container",
        "boxes": [b for b in flat if b.get("kind") != "group"],
        "groups": [b for b in flat if b.get("kind") == "group"],
        "edges": [dict(e) for e in edges],
        "canvas": (round(widest + MARGIN * 2), round(y - CONTAINER_GAP_Y + MARGIN)),
    }
    # A frame holding one end of an edge is not something that edge crosses.
    by_id = {item["id"]: item for item in flat}
    ancestry: dict = {}
    for item in result["boxes"]:
        chain, current = set(), item.get("parent")
        while current in by_id:
            chain.add(current)
            current = by_id[current].get("parent")
        ancestry[item["id"]] = chain
    route(result, result["boxes"] + result["groups"], ancestry)
    return result


# ---------------------------------------------------------------------------
# timeline
# ---------------------------------------------------------------------------


def _axis_key(value: str):
    """Sort axis values without knowing what kind of value they are.

    A Gantt carries dates, a journey carries step numbers, a branch diagram
    carries positions. Rather than ask the type, each value is parsed as the
    most specific thing it could be, and the kinds are kept apart so a mixed
    axis still has a total order instead of raising.
    """
    text = str(value).strip()
    parts = text.split("-")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        return (0, tuple(int(part) for part in parts))
    if text.lstrip("+-").isdigit():
        return (1, (int(text),))
    return (2, (text,))


def timeline(payload: dict) -> dict:
    tracks = [t for t in payload.get("tracks") or [] if isinstance(t, dict)]
    spans = [s for s in payload.get("spans") or [] if isinstance(s, dict)]

    values = {str(s["start"]) for s in spans if s.get("start") is not None}
    values |= {str(s["end"]) for s in spans if s.get("end")}
    ordered = sorted(values, key=_axis_key)
    column = {value: i for i, value in enumerate(ordered)}

    label_w = round(
        max([len(str(t.get("label", ""))) for t in tracks] or [8]) * CHAR_W + PAD_X * 2
    )
    label_w = max(MIN_W, min(MAX_W, label_w))

    # A bar's width says how many columns it covers, so it cannot simply grow
    # to fit its label without lying about the span. Widen every column
    # instead: the axis is ordinal, so scaling it uniformly changes nothing it
    # claims. A point -- a milestone, a commit -- keeps its small shape and has
    # its label drawn beside it.
    def _is_point(span: dict) -> bool:
        return span.get("kind") in ("milestone", "commit", "merge")

    needed = COL_W
    outside = 0
    for span in spans:
        text_w = len(str(span.get("label", ""))) * CHAR_W + PAD_X * 2
        if _is_point(span):
            outside = max(outside, text_w)
            continue
        start = column.get(str(span.get("start")), 0)
        end = column.get(str(span.get("end")), start) if span.get("end") else start
        needed = max(needed, text_w / max(1, end - start))
    col_w = round(min(COL_W_MAX, max(COL_W, needed)))

    origin = MARGIN + label_w
    # Every value gets a column, including the last one: a span starting on
    # it still occupies a full column and would otherwise run off the page.
    axis_w = max(col_w * max(len(ordered), 1), col_w) + round(outside)

    axis = [
        {"label": value, "x": round(origin + column[value] * col_w), "y": MARGIN}
        for value in ordered
    ]

    # Geometry first, then the packing, then the bands: a track is only as
    # tall as what it has to hold.
    measured = []
    for span in sorted(spans, key=lambda s: _axis_key(str(s.get("start", "")))):
        start = column.get(str(span.get("start")), 0)
        end = column.get(str(span.get("end")), start) if span.get("end") else start
        point = _is_point(span)
        # A span covering no columns -- a one-day task, a step with no end --
        # still occupies one, because a zero-width bar is not a bar.
        width = MILESTONE_W if point else max(SPAN_MIN_W, max(1, end - start) * col_w)
        label = str(span.get("label", ""))
        # The score is drawn as part of the label, so it has to be part of
        # what the label is measured as. Appending it after the measurement
        # is how a bar ends up narrower than its own text.
        if span.get("score") is not None:
            label = f"{label} ({span['score']}/5)"
        if point:
            lines, height = [label], SPAN_H
        else:
            lines = wrap(label, max(4, int((width - PAD_X * 2) / CHAR_W)))
            height = max(SPAN_H, len(lines) * LINE_H + 10)
        measured.append(
            {
                "id": span["id"],
                "kind": "span",
                "role": span.get("kind") or ("milestone" if point else "task"),
                "label": label,
                "lines": lines,
                "label_outside": point,
                "note": span.get("note"),
                "score": span.get("score"),
                "track": span.get("track"),
                "depends_on": span.get("depends_on") or [],
                "x": round(origin + start * col_w),
                "w": round(width),
                "h": round(height),
            }
        )

    # Two spans overlapping in time on one track is ordinary -- two things
    # running at once -- so they are packed into sub-rows rather than drawn on
    # top of each other. A track whose spans never overlap keeps one row,
    # which is what a branch diagram wants.
    sub_row: dict = {}
    rows_used: dict = {}
    for span in measured:
        track = span.get("track")
        occupied = rows_used.setdefault(track, [])
        for index, taken in enumerate(occupied):
            if all(span["x"] >= b or span["x"] + span["w"] <= a for a, b in taken):
                taken.append((span["x"], span["x"] + span["w"]))
                sub_row[span["id"]] = index
                break
        else:
            occupied.append([(span["x"], span["x"] + span["w"])])
            sub_row[span["id"]] = len(occupied) - 1

    bands, placed = [], []
    y = MARGIN + AXIS_H
    for track in tracks:
        rows = max(1, len(rows_used.get(track["id"], [])))
        tallest = max(
            [s["h"] for s in measured if s.get("track") == track["id"]] or [SPAN_H]
        )
        height = rows * tallest + (rows + 1) * SPAN_GAP
        bands.append(
            {
                "id": track["id"],
                "kind": "track",
                "label": track.get("label", ""),
                "note": track.get("note"),
                "x": MARGIN,
                "y": round(y),
                "w": round(label_w + axis_w),
                "h": round(height),
                "label_w": label_w,
                "rows": rows,
            }
        )
        for span in measured:
            if span.get("track") != track["id"]:
                continue
            span["y"] = round(y + SPAN_GAP + sub_row[span["id"]] * (tallest + SPAN_GAP))
            placed.append(span)
        y += height + TRACK_GAP

    for span in measured:
        span.setdefault("y", MARGIN + AXIS_H)
        if span not in placed:
            placed.append(span)

    return {
        "layout": "timeline",
        "boxes": placed,
        "tracks": bands,
        "axis": axis,
        "edges": [
            {"from": dep, "to": span["id"], "kind": "flow"}
            for span in placed
            for dep in span["depends_on"]
        ],
        "canvas": (round(MARGIN * 2 + label_w + axis_w), round(y - TRACK_GAP + MARGIN)),
    }


LAYOUTS = {
    "layered": layered,
    "table": table,
    "lifeline": lifeline,
    "container": container,
    "timeline": timeline,
}


def place(payload: dict, layout: str, graph_type: str = "") -> dict:
    """Entry point. Raises KeyError for a layout that is not built yet, which
    drawio_write.py turns into a readable message.

    The type matters in one place only: a swimlane is a container whose
    groups keep the order they were written in rather than being ranked.
    """
    if layout == "container":
        return container(payload, lanes=graph_type == "swimlane")
    return LAYOUTS[layout](payload)

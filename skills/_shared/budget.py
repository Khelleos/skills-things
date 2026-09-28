"""The complexity budget, counted rather than eyeballed.

Plan section 7: no more than 9 blocks and 12 links, plus a per-type limit
where the type has one of its own. Going over is a refusal by default. The
way out is to reduce or to split, not to argue -- and if the limit is honestly
in the way, meta.budget_override lifts it with a reason that then travels in
the loss report.

The ladder below is the order in which things get dropped. The order is code;
the choice of what to drop is the agent's, because nothing here can tell
"five identical workers collapse into one" from "logging goes away".

stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass

MAX_BLOCKS = 9
MAX_LINKS = 12

#: Fixed order for giving things up. Never reorder -- the whole point is that
#: two runs of the same diagram drop the same things.
LADDER = (
    "decoration: notes, captions, legends carried over from the source",
    "exact duplicates: five identical workers become one block, 'Worker x5'",
    "groups of leaves only: the container replaces what is inside it",
    "dead ends that do not change the story: logs, archives, metrics",
    "cross-cutting infrastructure: logging, secrets, CI",
    "still too big: split into two diagrams. Splitting beats squeezing.",
)

#: Per-layout defaults. The first two keys of each are the block and the link
#: count, in the vocabulary that layout actually uses.
_BY_LAYOUT = {
    "layered": {"nodes": MAX_BLOCKS, "edges": MAX_LINKS},
    "container": {"nodes": MAX_BLOCKS, "edges": MAX_LINKS, "groups": 4},
    "table": {"entities": 8, "relations": MAX_LINKS, "rows": 12},
    "lifeline": {"actors": 6, "messages": MAX_LINKS},
    "timeline": {"tracks": 5, "spans": 15},
}

#: Where a type is stricter or looser than its layout. Plan section 7.
_BY_TYPE = {
    "swimlane": {"groups": 5},  # more than five lanes stops being readable
    "db-schema": {"rows": 15},  # a real table carries more columns than a model
    "c4": {"groups": 4},
    "requirements": {"rows": 8},
}

#: What each metric is called when a message has to name it to a person.
_HUMAN = {
    "nodes": "blocks",
    "edges": "links",
    "groups": "groups",
    "entities": "entities",
    "relations": "relations",
    "rows": "rows in a single entity",
    "actors": "lifelines",
    "messages": "messages",
    "tracks": "tracks",
    "spans": "spans",
}


@dataclass(frozen=True)
class Violation:
    metric: str
    actual: int
    allowed: int

    def __str__(self) -> str:
        return (
            f"budget: {self.actual} {_HUMAN.get(self.metric, self.metric)}, "
            f"limit is {self.allowed}"
        )


def limits_for(graph_type: str, layout: str) -> dict:
    """The limits that apply to one type, layout defaults plus type overrides."""
    limits = dict(_BY_LAYOUT.get(layout, {}))
    limits.update(_BY_TYPE.get(graph_type, {}))
    return limits


def count(payload: dict, layout: str) -> dict:
    """Count what the budget cares about, in the vocabulary of the layout."""

    def n(key: str) -> int:
        v = payload.get(key)
        return len(v) if isinstance(v, list) else 0

    if layout == "layered":
        return {"nodes": n("nodes"), "edges": n("edges")}
    if layout == "container":
        return {"nodes": n("nodes"), "edges": n("edges"), "groups": n("groups")}
    if layout == "table":
        entities = payload.get("entities")
        widest = 0
        if isinstance(entities, list):
            for e in entities:
                rows = e.get("rows") if isinstance(e, dict) else None
                if isinstance(rows, list):
                    widest = max(widest, len(rows))
        return {"entities": n("entities"), "relations": n("relations"), "rows": widest}
    if layout == "lifeline":
        return {"actors": n("actors"), "messages": n("messages")}
    if layout == "timeline":
        return {"tracks": n("tracks"), "spans": n("spans")}
    return {}


def check(graph: dict) -> list:
    """Every metric that is over its limit, as Violation objects.

    An override is not applied here. A caller decides what an override means
    for it: validate_graph turns violations into warnings when one is present,
    the generators do not care either way.
    """
    payload = graph.get("payload")
    if not isinstance(payload, dict):
        return []
    layout = graph.get("layout")
    limits = limits_for(graph.get("type"), layout)
    counts = count(payload, layout)
    return [
        Violation(metric, counts[metric], limits[metric])
        for metric in counts
        if metric in limits and counts[metric] > limits[metric]
    ]


def override_reason(graph: dict):
    """The reason attached to meta.budget_override, or None if there is none."""
    meta = graph.get("meta")
    if not isinstance(meta, dict):
        return None
    override = meta.get("budget_override")
    if isinstance(override, dict):
        reason = override.get("reason")
        if isinstance(reason, str) and reason.strip():
            return reason.strip()
    return None


def ladder_text(indent: str = "  ") -> str:
    """The ladder, formatted for an error message."""
    return "\n".join(f"{indent}{i}. {rung}" for i, rung in enumerate(LADDER, 1))

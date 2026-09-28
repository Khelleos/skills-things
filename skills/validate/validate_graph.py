"""Check a graph.json before anything is drawn from it.

This is the layer that catches most of what actually goes wrong, because the
mistake is nearly always in the intent and not in the writing down of it.
Four passes, in order of how much they matter:

  1. shape       -- schema.py: the payload matches its layout, ids are ids,
                    no edge points at nothing, no id is used twice
  2. budget      -- budget.py: 9 blocks and 12 links, plus per-type limits
  3. labels      -- text that will not survive escaping, or that reads as an
                    instruction rather than as a caption (plan section 9)
  4. readability -- blocks nothing joins to, a state machine with no entry

Errors block generation. Warnings do not: they are things a person should
look at, not things a script can decide.

Usage:
    python validate_graph.py <graph.json> [more.json ...] [--json] [--quiet]

Exit code 0 when every file is clean, 1 when any file has an error.

stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))

import budget  # noqa: E402
import escape  # noqa: E402
import schema  # noqa: E402

#: Phrasings that turn a caption into an attempt at a command. A hit is never
#: an error -- a legitimate diagram may well say "Ignore cache" -- but it gets
#: said out loud, because this is the exact shape of the attack in section 9.
_INJECTION = re.compile(
    r"\b("
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?)"
    r"|disregard\s+(the\s+)?(above|previous)"
    r"|you\s+are\s+now\s+"
    r"|system\s*prompt"
    r"|</?(system|assistant|human)>"
    r")",
    re.IGNORECASE,
)

_URL = re.compile(r"\bhttps?://", re.IGNORECASE)


def _walk_labels(graph: dict):
    """Yield (path, text) for every piece of free text a reader will see."""
    meta = graph.get("meta")
    if isinstance(meta, dict):
        for key in ("title", "scope"):
            if isinstance(meta.get(key), str):
                yield f"meta.{key}", meta[key]
        for i, d in enumerate(meta.get("dropped") or []):
            if isinstance(d, dict):
                for key in ("what", "why"):
                    if isinstance(d.get(key), str):
                        yield f"meta.dropped[{i}].{key}", d[key]

    payload = graph.get("payload")
    if not isinstance(payload, dict):
        return

    for collection in ("nodes", "edges", "groups", "actors", "messages", "tracks", "spans"):
        items = payload.get(collection)
        if not isinstance(items, list):
            continue
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            for key in ("label", "note"):
                if isinstance(item.get(key), str):
                    yield f"payload.{collection}[{i}].{key}", item[key]

    for i, entity in enumerate(payload.get("entities") or []):
        if not isinstance(entity, dict):
            continue
        for key in ("label", "note", "stereotype"):
            if isinstance(entity.get(key), str):
                yield f"payload.entities[{i}].{key}", entity[key]
        for j, row in enumerate(entity.get("rows") or []):
            if not isinstance(row, dict):
                continue
            for key in ("name", "type", "note"):
                if isinstance(row.get(key), str):
                    yield f"payload.entities[{i}].rows[{j}].{key}", row[key]

    for i, rel in enumerate(payload.get("relations") or []):
        if isinstance(rel, dict) and isinstance(rel.get("label"), str):
            yield f"payload.relations[{i}].label", rel["label"]

    for i, frag in enumerate(payload.get("fragments") or []):
        if isinstance(frag, dict) and isinstance(frag.get("label"), str):
            yield f"payload.fragments[{i}].label", frag["label"]


def check_labels(graph: dict, errors: list, warnings: list) -> None:
    for path, raw in _walk_labels(graph):
        clean = escape.normalize(raw)
        if not clean and raw:
            errors.append(f"{path}: nothing left after normalisation, the text is all control characters")
            continue
        if clean != raw:
            warnings.append(f"{path}: leading, trailing or control characters will be stripped")
        if len(clean) > escape.MAX_LABEL:
            warnings.append(
                f"{path}: {len(clean)} characters, will be clipped at {escape.MAX_LABEL}. "
                "A label this long usually means the block is doing too much"
            )
        if _INJECTION.search(clean):
            warnings.append(
                f"{path}: reads as an instruction, not a caption. It will be drawn as "
                "literal text and must not be acted on (plan section 9)"
            )
        if _URL.search(clean):
            warnings.append(f"{path}: contains a URL. It is drawn as text and is never opened")


def check_readability(graph: dict, warnings: list) -> None:
    payload = graph.get("payload")
    if not isinstance(payload, dict):
        return
    layout = graph.get("layout")
    graph_type = graph.get("type")

    if layout in ("layered", "container"):
        nodes = [n for n in payload.get("nodes") or [] if isinstance(n, dict)]
        edges = [e for e in payload.get("edges") or [] if isinstance(e, dict)]
        touched = {e.get("from") for e in edges} | {e.get("to") for e in edges}
        if len(nodes) > 1:
            for n in nodes:
                if n.get("id") not in touched:
                    warnings.append(
                        f"payload: block {n.get('id')!r} has no link to anything. "
                        "Either it belongs in the diagram and something connects it, or it does not"
                    )
        roles = [n.get("role") for n in nodes]
        if graph_type in ("state", "flowchart", "swimlane", "cicd"):
            if "start" not in roles:
                warnings.append(f"payload: a {graph_type} diagram with no block in role 'start'")
            if "end" not in roles:
                warnings.append(f"payload: a {graph_type} diagram with no block in role 'end'")
            if roles.count("start") > 1:
                warnings.append(
                    f"payload: {roles.count('start')} blocks in role 'start'. "
                    "One way in is what makes the diagram readable"
                )

        # 'subroutine' means "drawn somewhere else", and both formats give it
        # a shape of its own to say so. Without a note naming that other
        # diagram the shape is decoration, and a reader is left wondering why
        # this one box looks different.
        for node in nodes:
            if node.get("role") == "subroutine" and not node.get("note"):
                warnings.append(
                    f"payload: {node.get('id')!r} has role 'subroutine' but no note. "
                    "That role is for a step drawn in its own diagram -- name it in "
                    "'note', or use 'process'"
                )

        # A branch with no label is the commonest way one of these becomes
        # unreadable: the reader cannot tell which arm is which.
        for node in nodes:
            if node.get("role") not in ("decision", "gate", "choice"):
                continue
            out = [e for e in edges if e.get("from") == node.get("id")]
            if len(out) < 2:
                warnings.append(
                    f"payload: {node.get('role')} {node.get('id')!r} has {len(out)} way out. "
                    "A question with one answer is a step, not a decision"
                )
            unlabelled = [e for e in out if not e.get("label")]
            if len(out) > 1 and unlabelled:
                warnings.append(
                    f"payload: {len(unlabelled)} unlabelled branch(es) out of {node.get('id')!r}. "
                    "Label each with the answer: 'yes', 'no', 'expired'"
                )

    if layout == "table":
        entities = [e for e in payload.get("entities") or [] if isinstance(e, dict)]
        relations = [r for r in payload.get("relations") or [] if isinstance(r, dict)]
        touched = {r.get("from") for r in relations} | {r.get("to") for r in relations}
        if len(entities) > 1:
            for e in entities:
                if e.get("id") not in touched:
                    warnings.append(f"payload: entity {e.get('id')!r} takes part in no relation")
        # In draw.io a relation label sits in the gap between two tables, and
        # the gap grows to hold it. A sentence there pushes the whole page
        # apart; a verb is what the label is for.
        for i, r in enumerate(relations):
            label = r.get("label")
            if isinstance(label, str) and len(label) > 40:
                warnings.append(
                    f"payload.relations[{i}].label: {len(label)} characters. A relation "
                    "label is a verb read from one end to the other -- anything longer "
                    "belongs in a note or in the prose"
                )

        for e in entities:
            rows = [r for r in e.get("rows") or [] if isinstance(r, dict)]
            if graph_type in ("data-model", "db-schema") and rows:
                if not any(r.get("key") == "pk" for r in rows):
                    warnings.append(f"payload: entity {e.get('id')!r} has no row marked 'pk'")
                for j, r in enumerate(rows):
                    if not r.get("type"):
                        warnings.append(
                            f"payload.entities[{entities.index(e)}].rows[{j}]: no type. "
                            "Mermaid ER has no form without one and will print 'unknown'"
                        )

    if layout == "lifeline":
        actors = [a for a in payload.get("actors") or [] if isinstance(a, dict)]
        messages = [m for m in payload.get("messages") or [] if isinstance(m, dict)]
        speaking = {m.get("from") for m in messages} | {m.get("to") for m in messages}
        for a in actors:
            if a.get("id") not in speaking:
                warnings.append(f"payload: lifeline {a.get('id')!r} sends and receives nothing")

        # A message label is centred over its own arrow, and the lifelines it
        # spans are drawn straight through the text. Two crossed lifelines is
        # where that stops being readable. Order the actors so the pairs that
        # talk most sit next to each other.
        column = {a["id"]: i for i, a in enumerate(actors) if isinstance(a.get("id"), str)}
        for i, m in enumerate(messages):
            here, there = column.get(m.get("from")), column.get(m.get("to"))
            if here is None or there is None:
                continue
            crossed = abs(here - there) - 1
            if crossed >= 2:
                warnings.append(
                    f"payload.messages[{i}]: crosses {crossed} other lifelines, so its label "
                    "is drawn over them. Reorder the actors to put this pair closer, or split "
                    "the diagram"
                )

    if layout == "timeline":
        tracks = [t for t in payload.get("tracks") or [] if isinstance(t, dict)]
        spans = [s for s in payload.get("spans") or [] if isinstance(s, dict)]
        used = {s.get("track") for s in spans}
        for t in tracks:
            if t.get("id") not in used:
                warnings.append(f"payload: track {t.get('id')!r} holds nothing")


def _note_if_at_ceiling(graph: dict, warnings: list) -> None:
    """Sitting exactly on the limit is legal and usually a mistake.

    A diagram is finished when there is nothing left to remove, so a count
    that lands precisely on the ceiling is more often a diagram that was
    filled up to it than one that happened to fit.
    """
    payload = graph.get("payload")
    if not isinstance(payload, dict):
        return
    limits = budget.limits_for(graph.get("type"), graph.get("layout"))
    counts = budget.count(payload, graph.get("layout"))
    at = [m for m in counts if m in limits and counts[m] == limits[m]]
    if at:
        named = ", ".join(f"{m} {counts[m]}/{limits[m]}" for m in at)
        warnings.append(
            f"budget: exactly on the limit ({named}). The limit is a ceiling, not a "
            "target -- take one more pass down the ladder before generating"
        )


def check_budget(graph: dict, errors: list, warnings: list) -> None:
    violations = budget.check(graph)
    if not violations:
        _note_if_at_ceiling(graph, warnings)
        return
    reason = budget.override_reason(graph)
    if reason:
        for v in violations:
            warnings.append(f"{v}, allowed by meta.budget_override: {reason}")
        return
    for v in violations:
        errors.append(str(v))
    errors.append(
        "the budget is a refusal, not a suggestion. Reduce down the ladder, in order:\n"
        + budget.ladder_text()
        + "\nOr, if the limit is honestly in the way here, set meta.budget_override "
        'to {"reason": "..."} and the reason travels into the loss report.'
    )


def validate_graph(graph: object) -> tuple:
    """Run every pass over an already-parsed graph. Returns (errors, warnings).

    The shape pass runs alone first: with a broken shape the later passes
    would only produce noise about a graph that does not exist yet.
    """
    errors = schema.validate(graph)
    warnings: list = []
    if errors or not isinstance(graph, dict):
        return errors, warnings

    check_budget(graph, errors, warnings)
    check_labels(graph, errors, warnings)
    check_readability(graph, warnings)
    return errors, warnings


def validate_file(path) -> tuple:
    try:
        graph = schema.load(path)
    except ValueError as exc:
        return [str(exc)], []
    return validate_graph(graph)


def _report(path, errors: list, warnings: list, quiet: bool) -> None:
    if errors:
        print(f"FAIL  {path}")
    elif warnings:
        print(f"ok    {path}  ({len(warnings)} to look at)")
    elif not quiet:
        print(f"ok    {path}")
    for e in errors:
        for i, line in enumerate(str(e).splitlines()):
            print(f"  {'error:' if i == 0 else '      '} {line}")
    for w in warnings:
        print(f"  note:  {w}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate graph.json files before a diagram is generated from them."
    )
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--quiet", action="store_true", help="print only problems")
    args = parser.parse_args(argv)

    results = []
    failed = False
    for path in args.paths:
        errors, warnings = validate_file(path)
        failed = failed or bool(errors)
        results.append(
            {"path": str(path), "ok": not errors, "errors": [str(e) for e in errors], "warnings": warnings}
        )

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for r in results:
            _report(r["path"], r["errors"], r["warnings"], args.quiet)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

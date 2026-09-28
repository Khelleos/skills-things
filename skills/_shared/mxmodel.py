"""The intent a .drawio file carries, and the one wrapper draw.io puts round cells.

A file this toolchain writes carries its own graph.json. It rides on the
model's root cell as a data attribute, because that is the one place draw.io
keeps something of ours through an open-edit-save: XML comments are dropped
on save, and so is any attribute it does not know on <mxfile> or <diagram>.
Data on a cell is kept, and on the root cell it belongs to no shape a person
can select and delete.

Data on a cell is also why the wrapper exists. draw.io writes such a cell as
<object label=".." id=".." key="..."><mxCell .../></object> -- the id and the
label move to the wrapper. Anything reading a model by walking <mxCell>
elements has to undo that first, or a cell somebody gave a tooltip in draw.io
vanishes from it.

stdlib only.
"""

from __future__ import annotations

import json

#: The attribute on the root cell that holds the intent.
INTENT_ATTR = "intent"

_WRAPPERS = ("object", "UserObject")


def intent_attr(graph: dict) -> str:
    """The intent, as the value of an XML attribute.

    Compact JSON never contains a raw newline, so XML escaping is all it
    needs; sorted keys keep the file reproducible byte for byte.
    """
    text = json.dumps(graph, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    for char, entity in (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"), ('"', "&quot;")):
        text = text.replace(char, entity)
    return text


def unwrap(root) -> dict:
    """Replace every <object>/<UserObject> with the <mxCell> inside it.

    The cell takes the wrapper's id, and its label as 'value'. Works on the
    parsed tree in place and returns the wrappers' own attributes by cell id,
    for whoever wants the data draw.io kept there.
    """
    data = {}
    for parent in list(root.iter()):
        for index, child in enumerate(list(parent)):
            if child.tag not in _WRAPPERS:
                continue
            inner = child.find("mxCell")
            if inner is None:
                continue
            cell_id = child.get("id")
            if cell_id is not None:
                inner.set("id", cell_id)
            if child.get("label") is not None:
                inner.set("value", child.get("label"))
            data[cell_id] = dict(child.attrib)
            parent.remove(child)
            parent.insert(index, inner)
    return data


def embedded_intent(data: dict):
    """(graph, problem). The intent from the root cell, if there is one.

    'problem' is a sentence when an attribute is there and cannot be read;
    both are None when the file simply carries no intent.
    """
    for attrs in data.values():
        raw = attrs.get(INTENT_ATTR)
        if raw is None:
            continue
        try:
            graph = json.loads(raw)
        except json.JSONDecodeError as exc:
            return None, f"the embedded intent is not valid JSON: {exc.msg}"
        if not isinstance(graph, dict):
            return None, "the embedded intent is not a JSON object"
        return graph, None
    return None, None

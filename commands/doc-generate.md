---
description: Write documentation from this codebase - README, API reference, ADR or runbook - with the diagrams that belong in it.
argument-hint: [what to document, in a plain sentence]
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Agent
---

Write documentation for: **$ARGUMENTS**

You are the caller. `docs-writer` does the writing; your job is the two
things a subagent cannot do — settle the terms before it starts, and check
the result against a reader after it finishes.

## 1. Settle the four settings yourself

Do not pass an under-specified job down. Work each one out from what was
asked and from the repository; ask the user only where the answer genuinely
changes the document and cannot be inferred.

| Setting | Default when unstated |
|---|---|
| form | inferred from the request: README, API reference, ADR, runbook |
| format | Mermaid |
| scope | the files or subsystem the request points at |
| detail | `normal` |
| audience | `engineer` |

Two things to look up rather than assume: whether the target file already
exists, and — for an ADR — the next free number in `docs/adr/`.

## 2. Confirm in one line, then go

One sentence, before launching anything. Name the form, the scope, the
format, where the file lands, and the one thing that will not fit.

> Runbook for the `celery_worker_backlog` alert, from `celery/worker/`, one
> Mermaid flowchart, into `docs/runbooks/celery-worker-backlog.md`. The
> broker's own failure modes are out of scope and will be linked, not
> covered.

If a table would serve better than the document that was asked for, say so
in that same line. If the user still wants it, write it without arguing.

## 3. Launch `docs-writer` with the whole job

One call, everything in it: the form, the four settings, the paths to read,
the path to write, and anything already established in this conversation.
The subagent does not talk to the user and cannot come back for more.

## 4. Run the reader check

`docs-writer` returns three to five questions a reader will arrive with. For
each, start a **separate** agent that is given only the written document and
one question, and asked whether the document answers it. The writer cannot
run this on itself — that is the whole point of it.

Skip it for something short and disposable. Run it for anything anyone will
depend on.

## 5. Check the diagrams against their intents

The documents are written and the fences are in them, so the last thing to do
is ask whether they still say what their intents say:

```
python "$HOME/.claude/skills/validate/validate_mermaid.py" <each written .md> --paired
python "$HOME/.claude/skills/validate/validate_drawio.py" <each written .drawio> --graph <its intent>
```

`--paired` finds the intents in `<dir>/diagrams/` itself. It is cheap, it is
the only thing that catches a diagram edited by hand after it was generated,
and it is worth running again months later when nobody remembers which
document owns which intent.

## 6. Report

- The paths written, and which were written alongside an existing file
  rather than replacing it.
- What each diagram left out, in words.
- Any question from the reader check that came back unanswered — those are
  gaps, and say whether you closed them.
- That the diagram syntax has not been through a renderer, and where to
  preview it.

## Edge cases

- **The target file exists.** Never replace it. Write `<name>.new.md`
  alongside, show what differs, and let the user choose.
- **A hand-edited `.drawio` is in the way.** Regenerating recomputes every
  coordinate and destroys the manual layout. Warn before, not after.
- **The request names a diagram type that is not built yet.** Eleven of the
  seventeen types are not generated yet. Say which, offer the nearest of the
  six that are, or a table.
- **The repository has no `docs/`.** Create it. Say that you did.
- **The request is really two documents.** A README that also has to explain
  a decision is a README plus an ADR. Say so and write both, or write the one
  asked for and name the other.
- **Nothing in the code answers the question.** Say that. A document that
  invents an answer is worse than a gap someone can see.

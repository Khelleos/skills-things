# ADR — architecture decision record

**Answers:** why is it like this, and what did we turn down?

**Reader:** someone, often the author eighteen months later, about to change
something and wondering whether the current shape was a decision or an
accident.

**Format:** MADR. **Path:** `docs/adr/NNNN-slug.md`, four digits, sequential
across the whole project, never reused.

## Shape

```markdown
# NNNN. Short title, as a decision

- Status: Proposed | Accepted | Deprecated | Superseded by [NNNN](...) | Rejected
- Date: YYYY-MM-DD
- Deciders: roles, not names

## Context

What forces are in play. Written so someone who was not there can feel the
pressure: the constraint, the deadline, the thing that broke.

## Decision

What was decided, in the active voice. "We will ..." — one paragraph.

## Options considered

### The one chosen
Why it wins. What it costs.

### The others
One block each, with the reason it lost. A real reason, not a strawman.

## Consequences

What becomes easier. What becomes harder. What has to be revisited, and on
what trigger.
```

## The lifecycle

**Proposed → Accepted → Deprecated → Superseded**, plus **Rejected** off to
the side.

- **Proposed** while it is being argued.
- **Accepted** once it is in force. This is the only status that means "this
  is how things are".
- **Deprecated** when it no longer applies and nothing replaced it.
- **Superseded by NNNN** when something replaced it. Link both ways: the new
  record says what it supersedes.
- **Rejected** for a decision considered and turned down. Keep it. A rejected
  ADR is what stops the same idea being re-proposed every spring.

**Never delete or rewrite an accepted ADR.** It records what was decided and
what was known at the time. If it turns out to be wrong, that is a new record
superseding it. Editing history is how a decision log becomes worthless.

## Options considered is the section that matters

An ADR without real alternatives is a press release. The rejected option
needs enough detail that a reader can tell it was genuinely weighed, and the
reason it lost has to be a reason that was true at the time — not one
discovered later.

If only one option was ever considered, say that. "No alternative was
evaluated; the deadline was X" is honest and useful.

## What does not belong

- Implementation detail. The decision, not the patch.
- Anything that changes weekly. An ADR is for decisions expensive to reverse.
- Several decisions in one record. One record, one decision, one number.

## Diagram

Rarely. If the decision is about shape — a split, a boundary moving, a layer
added — one small `architecture` diagram inside **Options considered**, on
the chosen option, can carry what a paragraph struggles with.

Never draw the rejected options. Drawing them gives them a weight in the
reader's memory that the text then has to argue away.

## Checks before handing it over

- Is the title a decision, not a topic? "Use Postgres for the result store",
  not "Result store".
- Is the status one of the five, and is a superseding link two-way?
- Does at least one rejected option have a reason that was true at the time?
- Are the consequences honest about what got harder?

# Architecture overview

**Answers:** how does this system actually work, and why is it shaped this
way?

**Reader:** someone joining, or someone from another team about to depend on
this. They have read the README, it was not enough, and they need the whole
shape before they can be useful.

This is the one form built around its diagrams rather than around its
paragraphs. It arrives now because it needs both formats: the diagrams are
worth drawing twice — Mermaid inline for reading in the repository, draw.io
beside it for the version that ends up in a slide.

## Shape

1. **What the system does**, in one paragraph. Not the components. The job.
2. **The shape.** One `architecture` diagram, and the paragraph that says
   what to notice in it — the boundary, the store that everything depends on,
   the one queue that decouples the two halves.
3. **One path through it, end to end.** A `sequence` diagram of the single
   most representative run, and the prose that walks it. Pick the path a
   reader will meet first, not the most interesting one.
4. **What is stored.** A `data-model` diagram if the domain has shape; a
   table if it does not.
5. **The lifecycles that matter.** A `state` diagram per entity with a real
   lifecycle. Most systems have one or two. If it has none, say so and skip
   the section rather than inventing one.
6. **The decisions.** Not the arguments — links to the ADRs, with one line
   each on what was decided. If a decision has no ADR and should have, say
   that.
7. **What this document leaves out**, and where that is written down instead.

## Four diagrams is the ceiling

Sections 2 to 5 permit at most one diagram each, and only where the section
has something with a shape. A document with four diagrams is dense. A
document with seven is a gallery, and a reader stops looking at any of them.

If a subsystem needs its own set, it needs its own overview, linked from here.

## Both formats, deliberately

For each diagram: Mermaid inline in the Markdown, and the `.drawio` beside it
in `docs/diagrams/`, generated from the same `graph.json`.

```
docs/
  architecture.md
  diagrams/
    overview.graph.json     overview.drawio
    request-path.graph.json request-path.drawio
```

The Mermaid is what people read; the draw.io is what someone opens when they
need it on a slide. Both come from one intent, so they cannot disagree.

This is the only form where doing both is worth it. Everywhere else, pick one.

## What does not belong

- Installation and first run. That is the README.
- Endpoint and parameter detail. That is the API reference.
- The argument for a decision. That is an ADR — link it.
- Recovery procedures. Those are runbooks.

An overview that starts absorbing the other four forms is how a document
becomes the one nobody updates.

## Say what is true now

An overview goes stale faster than anything else here, because it describes a
shape rather than an interface, and shapes change without any signature
changing. Date it, name the commit or version it describes, and be specific
about the parts that are in flight: "the worker pool is being replaced; this
describes the current one" is worth more than a diagram that is quietly six
months old.

## Checks before handing it over

- Is there a paragraph saying what the system does, before any diagram?
- Does every diagram have prose saying what to notice in it?
- Four diagrams or fewer?
- Does each diagram name what it left out?
- Are the decisions linked rather than re-argued?
- Is there a date and a version this describes?

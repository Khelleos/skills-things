# Runbook

**Answers:** it is broken. What do I do?

**Reader:** on call, woken up, holding a phone, with an alert name and no
context. Assume tired, assume unfamiliar with this service, assume the clock
is running.

One runbook per **alert or symptom**, never per service. The reader arrives
with a symptom, not with an architecture.

## Shape

Order is not stylistic here. It is the order a tired person needs.

1. **Symptom, as the alert names it.** The exact string, so a search finds
   this page.
2. **Impact.** Who is affected and how badly, right now. This is what decides
   whether to keep reading or to escalate first.
3. **Stop the bleeding.** The mitigation, before any diagnosis. Restart,
   drain, roll back, raise the limit. Numbered, copy-pasteable, with what
   each command should print when it worked.
4. **Confirm it worked.** The check, and the number that says recovered.
5. **Then diagnose.** Where to look, in order: this dashboard, this query,
   this log filter. Real names, real queries.
6. **Known causes**, most frequent first. Each with its own fix.
7. **Escalate to whom**, with the trigger. "Still failing after step 3", not
   "if it seems serious".
8. **After it is over.** What to file, what to check tomorrow.

## Mitigation comes before diagnosis

The commonest defect in a runbook is a diagnostic tree before the fix. At
3am the job is to make it stop; understanding it is the morning's job.

If mitigation is genuinely unsafe without knowing the cause, say so in one
line at the top and say what the risk is. That is a decision the reader must
make consciously.

## Every step says what success looks like

A step with no expected output leaves the reader unable to tell whether it
worked. Show the line the command prints, the metric that should drop, the
status that should flip.

```
$ celery -A app inspect active | wc -l
0        # no tasks in flight; safe to restart the pool
```

## What does not belong

- How the system works. Link the README or the architecture overview.
- Why it is built this way. Link the ADR.
- Anything that cannot be done from a laptop with the usual access. If it
  needs someone else's permission, that is an escalation step.

## Keeping it true

A runbook goes stale silently and is discovered stale at the worst moment.
Put the date it was last exercised at the top, not just the date it was
written. A runbook nobody has run in a year is a hypothesis.

## Diagram

Usually none — a diagram is not what a tired person needs at step 3.

The exception is a genuinely branching diagnosis, where the next step depends
on the answer to the last. Then one `flowchart`, after the mitigation section
and before the known causes. Keep it small: every decision must have labelled
branches, and if it does not fit in nine blocks the runbook should be split
by symptom instead.

## Checks before handing it over

- Does mitigation come before diagnosis?
- Does every command show what it prints when it worked?
- Is the escalation trigger a condition, not a feeling?
- Is there a date the procedure was last actually run?
- Would this work for someone who has never seen this service?

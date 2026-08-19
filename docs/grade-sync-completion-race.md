# Grade sync can stick in `in_progress` forever

A `GradingSync` can be left permanently in `in_progress`, which then blocks **every** further
grade sync for that assignment. Recovery currently requires a human with an SSM session.

Observed once in production on 2026-08-16 (CA region, assignment 9253) — one stuck row against
150 `finished` and 52 `failed`, so it is rare but not theoretical. Operational recovery is in
the playbook: `docs/support-howtos/unblocking-a-stuck-grade-sync.md`.

## Impact

`create_grading_sync` refuses to start a new sync while a non-terminal one exists
(`lms/views/dashboard/api/grading.py:52`, `lms/services/auto_grading.py:18` matching
`["scheduled", "in_progress"]`):

```python
if self.auto_grading_service.get_in_progress_sync(assignment):
    self.request.response.status_int = 400
    return {"message": "There's already an auto-grade sync in progress"}
```

So a stuck row is not cosmetic. The instructor sees the sync hang, and every retry returns
`400`. There is no timeout, no reaper and no UI affordance to clear it — the assignment's grade
sync is dead until someone intervenes manually.

## Root cause: the completion task can observe a pre-commit snapshot

`sync_grade` runs entirely inside `with request.tm:` (`lms/tasks/grading.py:41`), so its write
to `grading_sync_grade.success` is not visible to other transactions until that block exits.

But the completion task is scheduled **inside** that same transaction, with a one-second
countdown (`lms/tasks/grading.py:67` and `:74`, via `_schedule_sync_grades_complete` at `:108`):

```python
grading_sync_grade.success = False
grading_sync_grade.error_details = {"exception": str(err)}
_schedule_sync_grades_complete(grading_sync.id, countdown=1)   # sent to broker immediately
LOG.exception("Syncing grade back to LMS failed")
return
```

`apply_async` reaches the broker straight away, not on commit. If the transaction takes longer
than the countdown to commit, `sync_grades_complete` runs against a snapshot where that grade
is still `success IS NULL`, its `~exists(... success.is_(None))` check
(`lms/tasks/grading.py:90`) evaluates to "not complete", it sets nothing
(`:105`), and it exits **successfully**. Nothing ever re-checks.

This is a transactional-outbox problem: a delayed message enqueued inside a transaction, with a
delay shorter than the commit latency.

### Production timeline

```
21:59:39,468  GradingSync 203 created (12 grades)
21:59:39,821 → 21:59:41,112   11 completion tasks run and correctly do nothing
                              (grade 12 still in flight)

              grade 12 → 403 Forbidden from brightspace.brocku.ca
21:59:50,153  sync_grade retry: "Retry in 11s"
22:00:01,587  final failure → success=False set in session,
                _schedule_sync_grades_complete(countdown=1)
22:00:02,575  sync_grades_complete SUCCEEDED           ← ran here
22:00:02,944  sync_grade SUCCEEDED — success=False COMMITS here
              (nothing runs again; row stays in_progress)
```

**The finaliser completed 369 ms before the commit it needed to see.**

### Why it is rare

On the happy path a whole sync commits in ~1.2 s and the one-second countdown is comfortably
enough. The race needs a grade that fails *after* exhausting its retries: `max_retries=2` with
`retry_backoff=10` (`lms/tasks/grading.py:33-36`) adds ~11 s, which pushes the scheduling call
to just before a comparatively slow commit. That is why it took 203 syncs to surface — and why
it will keep surfacing whenever an institution's LMS starts rejecting grade posts.

## Contributing factors

**`sync_grades_complete` has no retry policy.** It is a bare `@app.task()`
(`lms/tasks/grading.py:77`), unlike `sync_grade` which has `autoretry_for=(Exception,)`. Any
transient failure in the finaliser is terminal, and produces the same stuck state by a
different route.

**Nothing reconciles stale rows.** The design assumes the last completing grade always
successfully triggers a finaliser that sees a complete picture. There is no fallback if that
single trigger is lost, mistimed, or errors.

## Fixes

**3 is implemented** — `sweep_stale_grading_syncs` in `lms/tasks/grading.py`, scheduled every
15 minutes from `h-periodic` (`h_periodic/lms_beat.py`). 1 and 2 remain worthwhile follow-ups:
the reaper guarantees *recovery*, it does not reduce how often the race fires.

In increasing order of robustness — 3 is the one that actually closes the hole.

1. **Schedule after commit.** Register the `apply_async` on the transaction's commit hook
   rather than calling it inline, so the message is only sent once the write is durable.
   Removes this specific race, but still assumes the message is never lost.

2. **Make the finaliser self-healing.** Give `sync_grades_complete` a retry policy, and have it
   re-schedule itself when it finds the sync incomplete but recently updated. Converts "lost
   trigger" into "delayed trigger".

3. **Add a periodic reaper.** A scheduled task that finalises `scheduled` / `in_progress` syncs
   older than N minutes, using the same completion logic. This fixes the race, the missing
   retry policy, and any future lost task in one move — and it is the difference between a
   system that self-heals and one that needs an engineer with production access.

Note that `GradingSync` carries a partial unique index — `ix__grading_sync_assignment_status_unique`
on `assignment_id` where `status IN ('scheduled', 'in_progress')` — so at most one non-terminal
sync per assignment is possible, and `get_in_progress_sync`'s `.one_or_none()` is safe. It also
means a stuck row blocks at two layers: the view returns 400, and the database would reject a
second row anyway.

## Reproducing

Make `sync_grade`'s final failure path commit slowly — e.g. hold the transaction open past the
countdown — while a completion task is already in flight. The sync will be left in
`in_progress` with every `grading_sync_grade.success` populated, which is the signature to
assert on: **all grades terminal, parent non-terminal**. That invariant violation is also a
cheap thing to alert on in production.

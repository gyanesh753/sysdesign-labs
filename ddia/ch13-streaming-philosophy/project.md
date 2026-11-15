## Goal

Try the chapter's three claims at small scale: derived views can be rebuilt and checked, exactly-once must be enforced end to end, and a log can be made to show tampering.

All three labs are plain Python and run in under a second. No Docker needed.

## Lab 1: one log, many views

```bash
python lab1_derived_views.py
```

A log of 6,000 account events is the only stored data. Each view is a pure function of that list.

**What you should observe**

1. Balances, a memo search index and daily volumes all come from the same events.
2. A view nobody planned for, the largest withdrawal per account, is built from history with one more function.
3. A view with a bug, transfers that never credit the receiver, is hundreds of thousands off in total and wrong for all 20 accounts. Fixing the function and replaying gives the correct total, because the events were never touched.
4. Old and new versions of a view can be compared on the same events before anyone depends on the new one.
5. A single altered balance in a stored view is found by deriving the view again and comparing.

**Try**

1. Make `balances` incremental: keep the view and a position in the log, and apply only new events. Then check it against a full rebuild after adding 1,000 more events.
2. Add an event type `reversal` that cancels an earlier event by position. Which views need to change, and can they still be computed in one pass?

## Lab 2: end-to-end duplicate suppression

```bash
python lab2_end_to_end.py
```

10,000 users each transfer 1 unit. Fifteen percent of replies are lost, so the client retries. Half the retries go over the same connection and half over a new one.

**What you should observe**

- With no duplicate suppression, 11,760 units move: every retry is a second transfer.
- With suppression per connection, about half the duplicates are caught and 10,880 units move.
- With a request identifier checked by the database, exactly 10,000 units move.

**Try**

1. Give the request-ID store a limited memory, keeping only the last 100 identifiers. When does that become unsafe?
2. Move the identifier's creation from the client to the server, one per incoming request. What goes wrong?

## Lab 3: a tamper-evident log

```bash
python lab3_audit_log.py
```

Each of 50,000 entries stores a hash of its own content combined with the previous entry's hash. The final hash is treated as published somewhere the log's operator cannot alter.

**What you should observe**

- An untouched log verifies in a fraction of a second.
- Changing one amount, or deleting one entry, is reported at the exact position.
- An attacker who rewrites an entry and recomputes every later hash produces a log that verifies as intact on its own, and is caught only by comparison with the published final hash. Dropping the last ten entries is caught the same way.

**Try**

1. Verification reads the whole log. Publish a checkpoint hash every 1,000 entries and verify only the entries since the last checkpoint. What do you now have to trust?
2. Why does the chain alone, without any outside reference, protect against accidents but not against a determined insider?

## Write up in NOTES.md

Record the totals from lab 1 step 3, the three results from lab 2, and what each of the five checks in lab 3 reported. Then answer: pick an operation in a system you know that must not happen twice. Where is the duplicate check made, and does it cover a retry from the user's device?

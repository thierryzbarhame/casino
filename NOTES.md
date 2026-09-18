# Cassino — Development Notes

This file documents what was actually built, tested, and found during
development, and what was asked of the coding agent at each step.

## Initial Implementation — the Python Engine

The assignment repository arrived with `README.md` and
`tests/test_casino.py` already in place, specifying the Hungarian
two-player Cassino rules through 14 tests, but no implementation. The
request was to implement `casino.py` to satisfy those tests exactly,
without modifying or weakening them, and to actually implement the real
rules rather than special-casing the tests.

The engine (`value`, `Move`, `new_deal`, `legal_moves`, `play`,
`deal_over`, `score`) was written from a careful reading of the tests as
the rules specification: card values, dealing, optional captures via
matching value sums (single card, one card against a table combination,
or several hand cards combined), invalid-move rejection, sweeps, the
double-move-after-a-sweep rule, new rounds dealt from the talon, and the
end-of-deal cleanup that awards leftover table cards to the last
capturer.

### Problem Found — Turn Handed to a Player With No Cards

**Observation:** All 14 tests passed on the first implementation, but a
manual stress test (many simulated full random deals, not part of the
test file) crashed on one seed with `min() arg is an empty sequence`
inside the assignment's own whole-deal helper.

**Diagnosis:** The double-move-after-a-sweep rule can empty one player's
hand faster than the other's, since one player briefly gets two
consecutive moves. Over a long deal this occasionally left a player with
zero cards while it was still nominally their turn — and a player with no
cards has no legal move at all.

**Fix:** `play` now never hands control to a player with an empty hand
while their opponent can still act; it skips straight to whoever can
actually move. This was verified afterward with 500 simulated full
random deals — zero crashes, and all 52 cards correctly accounted for in
the piles every time.

## Browser Game

With the engine complete and all 14 tests passing, the request was to
build a browser table (`index.html`) for playing a full deal against a
simple computer opponent — no server, no build step, no typing card
names, click-based selection for hand and table cards, the same rules as
the tested engine, a full-screen layout with no page scrolling, and a
fallback for card images.

The rules were ported to JavaScript directly from the verified
`casino.py` logic (the browser can't run the Python module), then
stress-tested independently before wiring up any UI: 1000 simulated
random full deals against the bare ported engine, then 10 full deals
driven through the actual click handlers and Play button (not a
shortcut around them) with the computer opponent playing its real
moves — all with zero failures and correct card accounting.

### Problem Found — Status Badges Clipped on Narrow Windows

**Observation:** While checking the layout at different window widths,
the score/sweeps/talon status badges got clipped at the right edge
instead of wrapping, at some narrow widths.

**Diagnosis:** This traced back to a well-known CSS flex/grid behavior:
an item's automatic minimum size defaults to its content's natural
(unwrapped) width unless explicitly overridden, which was silently
overriding the intended responsive sizing at several levels of the
layout (the status row, its container, and the individual badges).

**Fix:** Explicitly set `min-width: 0` (with `overflow: hidden` and text
truncation on the labels) at each of those levels, and added a clean
breakpoint that stacks the title above a 3-column status grid on narrow
screens. While fixing this, two smaller issues were cleaned up too: a
decorative talon-count badge floating over the table area was removed as
redundant (the talon count is already shown clearly in the status bar,
and this floating copy was the actual source of some of the clipping),
and the score panel labels were consolidated so "sweeps" is shown
directly under each player's own score instead of as two separately
labeled panels that both just said "SWEEPS."

## Final Testing

Before finishing, the full Python test suite was re-run
(`python -m pytest`) and all 14 tests still passed, confirming the
browser work did not touch the engine's behavior. The browser game was
verified by: an automated 1000-deal engine stress test, a 10-deal test
driving the real UI code paths end to end (selection, Play button
validation, computer turn scheduling, game-over detection), and visual
checks of the layout at several window sizes, including right around the
responsive breakpoint. The final version was satisfactory.

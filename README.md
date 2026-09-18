# Cassino

## Overview

A complete, playable implementation of the Hungarian two-player Cassino
card game: a Python engine that enforces the rules (verified by a test
suite) and a self-contained browser table where you play a full deal
against a simple computer opponent. Like the project's earlier Snake
assignment, this was built with a vibe-coding workflow — natural-language
prompts, iterative testing, and agent-assisted implementation — but for
Cassino the tests came first: the Python engine was written to satisfy an
existing, unmodified test suite that doubled as the rules specification.

## Hungarian Two-Player Cassino Rules

Two players (here, you and the computer) play a 52-card French deck down
to nothing, capturing cards from a shared table:

- **Deal.** Each deal gives 3 cards to each player's hand, 4 cards face up
  on the table, and the rest becomes the talon (stock), drawn from the
  front.
- **Placing.** On your turn you may place a single hand card face up on
  the table without capturing anything. This is always allowed, even when
  a capture is available — captures are optional, never forced.
- **Capturing.** You may instead play one or more hand cards together
  against one or more table cards, as long as the values on both sides add
  up to the same total. This covers a plain match (a 5 taking a 5), one
  card taking a combination (a King taking a 4 and a 9), and combining
  several hand cards to match a combination on the table.
- **Sweeps.** Capturing every card on the table is a sweep, worth a bonus
  point. Because it leaves the table empty, the player who moves next gets
  two moves in a row instead of one — they have to rebuild the table
  themselves.
- **New rounds.** Once both hands are empty and the talon still has cards,
  a fresh 3 cards are dealt to each player. Whoever captured last draws
  first and leads the new round; the table is left as it was.
- **End of the deal.** Once both hands and the talon are empty, the deal
  is over. Any cards still left on the table go to whoever captured last.
- **Scoring**, per player: 3 points for holding the majority of the 52
  cards, 2 points for holding the majority of the spades, 1 point for each
  ace held, 2 points for holding the ten of diamonds, 1 point for holding
  the two of spades, plus 1 point per sweep.

## Python Engine (`casino.py`)

A single module implementing exactly the interface the tests import:

```python
from casino import value, Move, new_deal, legal_moves, play, deal_over, score
```

- `value(card)` — a card's numeric value (A=1, 2–10 face value, J=11,
  Q=12, K=13).
- `Move(hand, table)` — two frozensets: the cards played from hand, and
  the cards taken from the table (empty when placing).
- `new_deal(deck, first=0)` — deals a fresh state from a 52-card sequence.
- `legal_moves(state)` — every legal placement and capture for the player
  to move, found via a pruned subset-sum search rather than brute-forcing
  every possible table subset, so it stays fast regardless of how large
  the table grows.
- `play(state, move)` — the state after `move`, including sweeps, the
  double-move-after-a-sweep rule, new rounds dealt from the talon, and the
  end-of-deal cleanup described above. Raises `ValueError` for any illegal
  move (cards not held, cards not on the table, a capture whose values
  don't add up).
- `deal_over(state)` / `score(state)` — as described above.

A `state` exposes the fields the tests read: `hands`, `table`, `talon`,
`piles`, `sweeps`, `player` (plus two internal bookkeeping fields used
only by `play` itself, not part of the tested interface).

## Browser Game (`index.html`)

A single self-contained HTML file — open it directly, no server, no
build step, no install. It reimplements the same rules as `casino.py` in
JavaScript (the browser can't run the Python module directly), ported
function-for-function so the two stay in agreement, and adds:

- **Card table.** A green-felt table area with the current table cards,
  the computer's hand shown face down at the top, your hand face up at
  the bottom, and a status bar with both players' scores, sweep counts,
  and the talon count.
- **Selection-based play.** Click cards in your hand and, if capturing,
  cards on the table to select them (a clear highlighted/lifted state),
  then click Play. No typing card names or values.
- **Validation with explanations.** If your selection doesn't form a
  legal move, the game explains why (e.g. that the selected values don't
  add up, or that placing plays exactly one card) instead of silently
  rejecting it.
- **Full-screen, responsive layout.** The table fills the viewport with
  no page scrolling, and reflows for narrow windows (a breakpoint stacks
  the title above a 3-column status grid on narrow screens).
- **Game-over screen.** Final scores, sweep totals, and captured-card
  counts, with a Play Again button.

### Computer Opponent

Plays only legal moves (drawn from the same `legalMoves` used to validate
your own moves): it captures whenever a capture is available, preferring
the move that takes the most cards, and otherwise places a random legal
card. It waits briefly (under a second) before moving so its move is
visible, and the turn indicator clearly shows when it's thinking.

### Card Representation and Images

Cards are the same strings used by the Python engine: rank then suit
(`"AS"`, `"10D"`, `"QH"`; ranks `A 2 3 4 5 6 7 8 9 10 J Q K`, suits
`S H D C`). Card faces are loaded from Byron Knoll's public-domain SVG
playing-card set on Wikimedia Commons, as suggested by the original
assignment brief. If an image fails to load (no network access, for
instance), each card falls back to a clean CSS-drawn face — rank and
suit symbol, colored red or black — so the game is always fully playable
without external images.

## Tests

`tests/test_casino.py` (14 tests, unmodified) specifies the rules:
card values, dealing, single/combination/multi-card captures, invalid
moves, turn order, sweeps and the double-move rule, new rounds, and a
full simulated 200-move deal checking the final piles and score.

### Running the Python Tests

```sh
uv run pytest
```

Without `uv`:

```sh
python -m pip install pytest
python -m pytest
```

All 14 tests pass.

## How to Launch the Browser Game

Open `index.html` directly in a modern browser (double-click it, or drag
it into a browser window). No server, database, build step, or install
is required.

## Project Structure

```
casino/
├── .git/
├── .gitignore
├── README.md
├── NOTES.md
├── casino.py
├── index.html
├── pyproject.toml
└── tests/
    └── test_casino.py
```

## Technologies Used

- **Python 3.11+** for the engine, tested with **pytest**.
- **HTML, CSS, and vanilla JavaScript** for the browser game — no
  frameworks, no build tooling, no npm.
- Card face images from Wikimedia Commons (public domain), with a pure
  CSS fallback.

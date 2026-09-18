"""Hungarian two-player Cassino: the game engine.

Cards are strings: rank then suit. Ranks A 2 3 4 5 6 7 8 9 10 J Q K,
suits S H D C ("AS", "10D", "QH"). See README.md for the full interface
this module implements.
"""

from dataclasses import dataclass
from itertools import combinations

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
SUITS = "SHDC"

_RANK_VALUE = {rank: i + 1 for i, rank in enumerate(RANKS)}


def value(card: str) -> int:
    """The card's numeric value: A=1, 2..10 face value, J=11, Q=12, K=13."""
    return _RANK_VALUE[card[:-1]]


@dataclass(frozen=True)
class Move:
    """A move: cards played from hand, and (if capturing) cards taken from
    the table. Placing a card with nothing taken is `Move({card}, set())`.
    """

    hand: frozenset
    table: frozenset


@dataclass(frozen=True)
class State:
    """The state of a deal in progress.

    `hands`, `table`, `talon`, `piles`, `sweeps` and `player` are the public
    fields the tests read. `last_capturer` and `owed_extra_move` are internal
    bookkeeping needed to implement the "double move after a sweep" and
    "last capturer takes the rest" rules below.
    """

    hands: tuple
    table: tuple
    talon: tuple
    piles: tuple
    sweeps: tuple
    player: int
    last_capturer: int | None = None
    owed_extra_move: bool = False


def new_deal(deck, first: int = 0) -> State:
    """Deal a fresh hand from `deck`: 3 cards to `first`, 3 to the other
    player, 4 face up on the table, the rest becomes the talon (stock)."""
    deck = tuple(deck)
    hands = [None, None]
    hands[first] = deck[0:3]
    hands[1 - first] = deck[3:6]
    return State(
        hands=tuple(hands),
        table=deck[6:10],
        talon=deck[10:],
        piles=((), ()),
        sweeps=(0, 0),
        player=first,
    )


def _subsets_with_sum(cards, target: int):
    """Every distinct combination of `cards` whose values sum to `target`.

    Uses a pruned backtracking search rather than brute-force
    `itertools.combinations` over every subset size: the table can grow
    fairly large over a deal, but the targets we ever search for are hand
    subset sums (at most a handful of cards, so small totals), so sorting
    ascending and stopping once a single card's value already exceeds what's
    left keeps this cheap regardless of table size.
    """
    ordered = sorted(cards, key=value)
    n = len(ordered)

    def backtrack(start, remaining, chosen):
        if remaining == 0:
            yield frozenset(chosen)
            return
        for i in range(start, n):
            v = value(ordered[i])
            if v > remaining:
                break  # ascending order: nothing further can fit either
            chosen.append(ordered[i])
            yield from backtrack(i + 1, remaining - v, chosen)
            chosen.pop()

    yield from backtrack(0, target, [])


def legal_moves(state: State) -> list:
    """Every legal move for the player to move.

    Placing any single held card is always legal, even when a capture is
    also available (captures are optional, never forced). A capture is
    legal whenever some non-empty combination of played hand cards sums to
    the same value as some non-empty combination of table cards taken —
    this single rule covers a plain match, one card against a combination on
    the table, and combining several hand cards to match a combination.
    """
    hand = state.hands[state.player]
    table = state.table

    moves = [Move(frozenset({card}), frozenset()) for card in hand]

    table_subsets_for_sum = {}
    for size in range(1, len(hand) + 1):
        for combo in combinations(hand, size):
            target = sum(value(card) for card in combo)
            if target not in table_subsets_for_sum:
                table_subsets_for_sum[target] = list(_subsets_with_sum(table, target))
            for table_cards in table_subsets_for_sum[target]:
                moves.append(Move(frozenset(combo), table_cards))

    return moves


def play(state: State, move: Move) -> State:
    """The state after `move`. Raises `ValueError` if `move` is not legal."""
    player = state.player
    hand = state.hands[player]
    hand_set = set(hand)

    if not move.hand or not move.hand.issubset(hand_set):
        raise ValueError("cannot play cards that are not in hand")

    if move.table:
        if not move.table.issubset(state.table):
            raise ValueError("cannot take cards that are not on the table")
        if sum(value(c) for c in move.hand) != sum(value(c) for c in move.table):
            raise ValueError("the cards taken must add up to the cards played")
    elif len(move.hand) != 1:
        raise ValueError("placing a card without capturing plays exactly one card")

    new_hand = tuple(c for c in hand if c not in move.hand)
    hands = list(state.hands)
    hands[player] = new_hand

    piles = list(state.piles)
    sweeps = list(state.sweeps)
    last_capturer = state.last_capturer

    if move.table:
        new_table = tuple(c for c in state.table if c not in move.table)
        piles[player] = piles[player] + tuple(move.hand) + tuple(move.table)
        last_capturer = player
        caused_sweep = not new_table
        if caused_sweep:
            sweeps[player] += 1
    else:
        new_table = state.table + tuple(move.hand)
        caused_sweep = False

    # A sweep clears the table, so the player right after the sweeper gets
    # two moves in a row instead of one (they must rebuild the table alone).
    # `owed_extra_move` marks that the player about to move still owes one;
    # playing that move consumes it without passing the turn.
    flip_turn = not state.owed_extra_move
    next_player = (1 - player) if flip_turn else player
    owed_extra_move = caused_sweep

    new_talon = state.talon

    if not hands[0] and not hands[1]:
        if new_talon:
            # Both hands ran out but cards remain: a new round is dealt.
            # The last player to capture draws first and leads it.
            leader = last_capturer if last_capturer is not None else player
            other = 1 - leader
            redealt = [None, None]
            redealt[leader] = new_talon[0:3]
            redealt[other] = new_talon[3:6]
            hands = redealt
            new_talon = new_talon[6:]
            next_player = leader
            owed_extra_move = False
        elif new_table:
            # Nothing left in hand or talon: the deal is over. Whatever is
            # still on the table goes to whoever captured last.
            taker = last_capturer if last_capturer is not None else player
            piles[taker] = piles[taker] + new_table
            new_table = ()

    # The compensation move above can empty one hand faster than the other.
    # A player with no cards has no legal move at all, so play never hands
    # control to them while their opponent can still act.
    if not hands[next_player] and hands[1 - next_player]:
        next_player = 1 - next_player

    return State(
        hands=tuple(hands),
        table=new_table,
        talon=new_talon,
        piles=tuple(piles),
        sweeps=tuple(sweeps),
        player=next_player,
        last_capturer=last_capturer,
        owed_extra_move=owed_extra_move,
    )


def deal_over(state: State) -> bool:
    """True once every card has been taken: both hands and the talon are
    empty (any leftover table cards are swept away by `play` at that
    point, see above), so nothing remains to be played."""
    return not state.hands[0] and not state.hands[1] and not state.talon and not state.table


def score(state: State) -> tuple:
    """Each player's points for the deal: most cards (3), most spades (2),
    one point per ace, the ten of diamonds (2), the two of spades (1), and
    accumulated sweeps."""
    points = []
    for p in (0, 1):
        pile = state.piles[p]
        total = 0
        if len(pile) >= 27:
            total += 3
        if sum(c.endswith("S") for c in pile) >= 7:
            total += 2
        total += sum(c.startswith("A") for c in pile)
        if "10D" in pile:
            total += 2
        if "2S" in pile:
            total += 1
        total += state.sweeps[p]
        points.append(total)
    return tuple(points)

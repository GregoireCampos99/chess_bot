# engine/search.py
import math, time
from .movegen import generate_moves, in_check
from .board import *
from .eval import evaluate

TT = {}  # simple dict: hash->(depth, score, move)

"""
search(depth=3)
 ├─ move A → search(depth=2)
 │    ├─ move A1 → search(depth=1)
 │    │    ├─ move A1a → search(depth=0)
 │    │    │    └─ quiesce()  ← called here
 │    │    └─ move A1b → search(depth=0)
 │    │         └─ quiesce()
 │    └─ move A2 → ...
 └─ move B → ...

We call quiesce() in order to better evaluate the position. 
if we just look at the position statically, we might miss an obvious recapture next move.
thus, when we call search(depth=0), we actually call quiesce(), 
which means: “Let’s stabilize the position by exploring all captures and see what the final, quiet evaluation actually is.”
"""

MATE = 100_000
VAL = {P:100, N:320, B:330, R:500, Q:900, K:10_000} # to unify at the folder level

def static_eval(b: Board, params=None) -> int:
    s = evaluate(b, params=params)
    return s if b.state.side == WHITE else -s

def quiesce(b: Board, alpha: int, beta: int, params=None) -> int:
    # negamax
    stand = static_eval(b, params)
    if stand >= beta: return beta
    if stand > alpha: alpha = stand

    # captures only
    moves = [mv for mv in generate_moves(b) if ((mv >> 8) & 1)]
    moves.sort(key=lambda mv: (mv >> 4) & 0xF, reverse=True)

    for mv in moves:
        if not see_capture_is_ok(b,mv):
            continue
        b.make_move(mv)
        score = -quiesce(b, -beta, -alpha, params)
        b.unmake_move(mv)
        if score >= beta: return beta
        if score > alpha: alpha = score
    return alpha

def search(b: Board, depth: int, alpha: int, beta: int, params=None):
    if depth == 0:
        return quiesce(b, alpha, beta), None
    moves = generate_moves(b)
    if not moves:
        if in_check(b, b.state.side):
            return -MATE, None
        else:
            return 0, None
    moves.sort(key=lambda mv: ((mv >> 8) & 1), reverse=True)
    best_move = None
    for mv in moves:
        b.make_move(mv)
        score, _ = search(b, depth - 1, -beta, -alpha, params)
        score = -score
        b.unmake_move(mv)
        if score > alpha:
            alpha = score
            best_move = mv
            if alpha >= beta:
                break
    return alpha, best_move

def iterative_deepening(b: Board, time_ms=1000, max_depth=5, params=None):
    import time as _t
    start = _t.time()
    best = None
    val = -math.inf
    for d in range(1, max_depth + 1):
        if (_t.time() - start) * 1000 > time_ms: break
        v, mv = search(b, d, -math.inf, math.inf, params)
        if mv is not None:
            best, val = mv, v
    return best, val

def best_move(b: Board, time_ms=1000, max_depth=5):
    val, mv = iterative_deepening(b, time_ms=time_ms, max_depth=max_depth)
    return mv, val

def see_capture_is_ok(b: Board, mv: int) -> bool:
    """Allow capture if it doesn't obviously lose material on the square (cheap)."""
    # decode
    piece = (mv & 0xF)
    captured = (mv >> 4) & 0xF
    to = (mv >> 25) & 0x7F
    fr = (mv >> 18) & 0x7F
    # crude gate: don’t trade a more valuable attacker for a less valuable victim
    return VAL.get(piece, 0) <= VAL.get(captured, 0)

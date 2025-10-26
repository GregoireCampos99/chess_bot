# tuning/run_match.py
from engine.board import Board
from engine.search import iterative_deepening
from engine.movegen import generate_moves, in_check

def play_single_game(params_white, params_black, time_ms=200, max_depth=4, max_plies=200):
    """
    Plays a single self-play game.
    White uses `params_white`, Black uses `params_black`.
    Returns: +1 if White wins, -1 if Black wins, 0 for draw.
    """
    b = Board()
    b.set_startpos()

    for _ in range(max_plies):
        stm_white = (b.state.side == 0)
        params = params_white if stm_white else params_black

        mv, _val = iterative_deepening(b, time_ms=time_ms, max_depth=max_depth, params=params)
        if mv is None:
            # No legal moves: checkmate or stalemate
            if in_check(b, b.state.side):
                # Side to move is in check and has no moves -> checkmated
                return -1 if stm_white else +1  # if it was White to move and no moves, Black wins
            return 0  # stalemate
        b.make_move(mv)

        # Optional: early stop if no progress is likely (very basic)
        # if b.state.halfmove >= 100:  # if you track half-move clock for 50-move rule
        #     return 0

    # Hit ply limit -> treat as draw
    return 0


def play_match(candidate, baseline, n_games=8, time_ms=200, max_depth=4):
    """
    Plays a short match of `n_games`, alternating colors.
    Returns a score in [-1, +1], where positive favors the candidate.
    """
    score = 0
    for i in range(n_games):
        if i % 2 == 0:
            # Candidate as White
            res = play_single_game(candidate, baseline, time_ms=time_ms, max_depth=max_depth)
        else:
            # Candidate as Black
            res = play_single_game(baseline, candidate, time_ms=time_ms, max_depth=max_depth)
        score += res
    return score / n_games

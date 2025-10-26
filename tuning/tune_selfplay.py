# tuning/tune_selfplay.py
import random
from copy import deepcopy
from .params import BASE_PARAMS, save_params
from .run_match import play_match

def jitter_mult(x, scale=0.10):
    """Multiply by (1 ± scale * random)."""
    return x * (1 + scale * (2*random.random()-1))

def mutate(params, scalar_scale=0.10, pst_noise=5):
    """Return a slightly mutated copy of params."""
    q = deepcopy(params)

    # Scalar weights
    for d in ("VALUES", "SCALES"):
        for k in q[d]:
            q[d][k] = jitter_mult(q[d][k], scalar_scale)

    for k in ["W_BISH_MOB","W_ROOK_MOB","W_ROOK_OPEN",
              "W_ROOK_SEMI","W_BAD_BISH","W_TRAPPED_R"]:
        q[k] = jitter_mult(q[k], scalar_scale)

    # Piece-square table small additive noise (±pst_noise centipawns)
    for r in range(8):
        for c in range(8):
            q["KNIGHT_PST"][r][c] += random.randint(-pst_noise, pst_noise)

    return q

def evolutionary_tune(generations=30, games_per_match=8,
                      time_ms=200, max_depth=4,
                      scalar_scale=0.10, pst_noise=5):
    """
    Run a simple evolutionary self-play tuner.
    Each generation mutates params, plays games vs current best,
    and keeps the winner.
    """
    best = deepcopy(BASE_PARAMS)
    best_score = 0.0

    print(f"[tuner] Baseline ready. Starting evolution for {generations} generations.", flush=True)

    for gen in range(1, generations+1):
        cand = mutate(best, scalar_scale=scalar_scale, pst_noise=pst_noise)
        score = play_match(cand, best,
                           n_games=games_per_match,
                           time_ms=time_ms,
                           max_depth=max_depth)
        print(f"[tuner] Gen {gen:02d} — score(candidate vs best) = {score:+.3f}", flush=True)

        if score > best_score:
            best, best_score = cand, score
            print(f"[tuner]   ✔ New best! score={best_score:+.3f} — saving snapshot", flush=True)
            save_params(best)  # interim save

    print(f"[tuner] Finished. Best score vs previous best: {best_score:+.3f}", flush=True)
    return best

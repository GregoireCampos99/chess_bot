# import random
# from copy import deepcopy

# def mutate(p, scale=0.1):
#     q = deepcopy(p)
#     # We introduce noise in the parameters
#     def jitter(x): return x * (1 + scale*(2*random.random()-1))

#     # Scalar weights
#     for d in ("VALUES","SCALES"):
#         for k in q[d]:
#             q[d][k] = jitter(q[d][k])
#     for k in ["W_BISH_MOB","W_ROOK_MOB","W_ROOK_OPEN","W_ROOK_SEMI","W_BAD_BISH","W_TRAPPED_R"]:
#         q[k] = jitter(q[k])

#     # PST mutation: small random additive noise (±5 cp = centipawns = .05 pawns by default)
#     for r in range(8):
#         for c in range(8):
#             q["KNIGHT_PST"][r][c] += random.randint(-5, 5)

#     return q

# from tuning.params import BASE_PARAMS
# from engine.board import Board
# from engine.search import iterative_deepening

# cand = mutate(BASE_PARAMS)  # your evolutionary step
# b = Board(); b.set_startpos()
# mv, val = iterative_deepening(b, time_ms=300, max_depth=4, params=cand)

# cli/tune_selfplay.py
import argparse
import sys
from pathlib import Path

# Make sure project root is on sys.path when running as a module
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tuning.tune_selfplay import evolutionary_tune
from tuning.params import save_params

def main():
    ap = argparse.ArgumentParser(description="Self-play evolutionary tuner")
    ap.add_argument("--generations", type=int, default=20)
    ap.add_argument("--games", type=int, default=8, help="games per match (candidate vs best, colors alternate)")
    ap.add_argument("--time_ms", type=int, default=200, help="per-move time for search")
    ap.add_argument("--depth", type=int, default=4, help="max search depth")
    ap.add_argument("--scalar_scale", type=float, default=0.10, help="±% multiplicative jitter for scalar weights")
    ap.add_argument("--pst_noise", type=int, default=5, help="±cp additive noise per PST square")
    ap.add_argument("--out", type=str, default="data/tuned_params.json")
    args = ap.parse_args()

    print(f"[tuner] Starting: generations={args.generations} games={args.games} "
          f"time_ms={args.time_ms} depth={args.depth} "
          f"scalar_scale={args.scalar_scale} pst_noise=±{args.pst_noise}cp", flush=True)

    best = evolutionary_tune(
        generations=args.generations,
        games_per_match=args.games,
        time_ms=args.time_ms,
        max_depth=args.depth,
        scalar_scale=args.scalar_scale,
        pst_noise=args.pst_noise,
    )
    save_params(best, args.out)
    print(f"[tuner] Done. Saved best params to {args.out}", flush=True)

if __name__ == "__main__":
    main()


# Each generation = plays 8 full self-play games (n_games=8)
# Each game = up to ~200 moves
# × 200 ms per move (time control)
# × a depth-4 search
# Rough estimate: 1 generation might take 30–90 seconds. 20-generation run could take 20–30 minutes total.
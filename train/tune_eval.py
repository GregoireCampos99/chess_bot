# train/tune_eval.py
import random
from copy import deepcopy
from engine.board import Board
from engine.search import iterative_deepening
from engine import eval as E

def play_game(params, opp_params, time_ms=200, max_plies=200):
    # swap params based on side to move
    b=Board(); b.set_startpos()
    for ply in range(max_plies):
        if not b: break
        # install weights
        E.SCALES.update(params if b.state.side==0 else opp_params)
        _, mv = iterative_deepening(b, time_ms=time_ms, max_depth=4)
        if mv is None: break
        b.make_move(mv)
        # ended?
        fen = b.to_fen()
        if " w " in fen or " b " in fen:
            continue
        break
    # naive outcome proxy: material score
    sc = E.evaluate(b)
    return 1 if sc>20 else -1 if sc<-20 else 0

def train(steps=50, sigma=0.3):
    best = deepcopy(E.SCALES)
    for t in range(steps):
        trial = {k: max(0.05, v + random.gauss(0, sigma)) for k,v in best.items()}
        score = sum(play_game(trial, best) for _ in range(4))
        if score>0:
            best = trial
            print(f"[{t}] improved -> {best}")
        else:
            print(f"[{t}] keep -> {best}")
    print("Final:", best)

if __name__=="__main__":
    train()

# cli/human_vs_bot.py
from engine.board import Board, rf, print_board_with_coords, EMPTY, WHITE, BLACK
from engine.movegen import generate_moves, in_check
from engine.eval import evaluate
from engine.search import iterative_deepening

##### should be ~ 1300 elo
##### this script is just for fun. you can try to beat the bot. 
##### TO DO: create UI to improve the playability. Right now, pretty sad.

FILES = "abcdefgh"

def decode_move(m):
    piece    = (m & 0xF)
    captured = (m >> 4) & 0xF
    flags    = (m >> 8) & 0x7F
    promo    = (m >> 15) & 0x7
    fr       = (m >> 18) & 0x7F
    to       = (m >> 25) & 0x7F
    return piece, captured, flags, promo, fr, to

def sq_from_uci(s2: str) -> int:
    file = FILES.index(s2[0])
    rank = int(s2[1]) - 1
    return (rank << 4) | file

def find_move_from_uci(b: Board, uci: str):
    fr = sq_from_uci(uci[0:2])
    to = sq_from_uci(uci[2:4])
    want_promo = None
    if len(uci) == 5:
        promo_map = {'n':2, 'b':3, 'r':4, 'q':5}
        want_promo = promo_map.get(uci[4].lower())
    for mv in generate_moves(b):
        _, _, _, promo, mfr, mto = decode_move(mv)
        if mfr == fr and mto == to and (want_promo is None or promo == want_promo):
            return mv
    return None

def uci_of(m):
    _,_,_,_, fr, to = decode_move(m)
    r1,f1 = rf(fr); r2,f2 = rf(to)
    return f"{FILES[f1]}{r1+1}{FILES[f2]}{r2+1}"

def main():
    b = Board(); b.set_startpos()
    print_board_with_coords(b)

    # choose who moves first
    human_white = input("Play as white? (y/n): ").strip().lower().startswith("y")

    while True:
        # Human move (if it's their turn)
        if (b.state.side == 0 and human_white) or (b.state.side == 1 and not human_white):
            mv_txt = input("Your move (UCI: e2e4, e7e8q, or 'quit'): ").strip()
            if mv_txt == "quit":
                break
            m = find_move_from_uci(b, mv_txt)
            if m is None:
                print("Illegal move.")
                continue
            b.make_move(m)
            print(f"You played {mv_txt}")
            print_board_with_coords(b)
            print("Eval (white-centric):", evaluate(b))
        else:
            # Engine move
            mv, val = iterative_deepening(b, time_ms=800, max_depth=5)
            if mv is None:
                print("No legal moves. Game over.")
                break
            b.make_move(mv)
            print(f"Engine played {uci_of(mv)} (eval {val})")
            print_board_with_coords(b)

if __name__ == "__main__":
    main()

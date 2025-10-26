# tools/perft.py
from engine.board import Board
from engine.movegen import generate_moves

# Perft(depth) counts all legal positions reachable from the current board in exactly depth plies (half-moves), by recursively generating 
# and playing every legal move. It’s not searching for the best move — it’s purely counting nodes to check that move generation 
# and unmake logic are 100% correct.

def perft(b:Board, depth:int)->int:
    if depth==0: return 1
    nodes=0
    for mv in generate_moves(b):
        b.make_move(mv)
        nodes += perft(b, depth-1)
        b.unmake_move(mv)
    return nodes

if __name__=="__main__":
    b=Board(); b.set_startpos()
    for d, target in [(1,20),(2,400),(3,8902),(4,197281)]:
        n=perft(b,d); print(d,n, "OK" if n==target else f"(!) expect {target}")

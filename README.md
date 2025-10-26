Goal: 
Chess engine from scratch in Python (0x88). No third-party chess packages. Legal-move generator, perft, alpha-beta with quiescence, UCI, and self-play eval tuning.

Our current engine is classic rule-based / search-based, not ML-based.
It uses:
- a hand-crafted evaluation function (evaluate())
- a minimax / negamax search with alpha-beta pruning (search())
- optional quiescence and iterative deepening

Features checklist: 
0x88 board 
legal moves 
castling 
en-passant 
make/unmake 
perft 
search 
quiescence 
trainer


How to run:
python -m cli.human_vs_bot - for fun

Run tests:
python -m test.test_board
python -m test.test_movegen
python -m test.test_eval

Design notes: 
Why x88?
0<=(ranks=rangees),(files=columns)<=7. 
a square will be one binary number using 8-bits [rrrr][ffff]. cheaper arithmetic than doing a tuple (rank, file). 
So each square can go up to 16 ranks and 16 files: the theoretical grid is 16x16=256 squares. of course, a chess board is only 8x8 = 64 squares. 
the "ghost" positions - corresponding to files 8-15 (ranks 8-15 are just removed) are here 
for off-board detection (if first bit in [rrrr] or [ffff] is 1, i.e. sq & x88 != 0, then off bound) 
and computation power (16 x 8 better aligns with byte format)
Why FEN notation?
FEN notation is the standard string for a chess position.
it resembles: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBRQKBN w KQkq - 0 1"
    rnbqkbnr/.../RNBQKBNR → the board layout (8 ranks, from rank 8 down to rank 1) (for instance, rank 1 = rook, knight, bishop, king, bishop, knight, rook)
    NB: capital letters are for white pieces.
    w → White to move
    KQkq → Both sides can castle kingside/queenside
    - → No en passant target square
    0 → Halfmove clock (for the 50-move rule)
    1 → Fullmove number (it’s move 1)
Why Zobrist?

Zobrist stub: fill in engine/zobrist.py for TT. recommended by https://www.chessprogramming.org/Zobrist_Hashing.
The idea is it gives us a unique numeric ID for every position. this saves huge amounts of work.
We use XOR because:
    XORing the same thing twice cancels it out
    XORing with 0 changes nothing
    Order of XORing does not matter.
So when we move, we update the hash incrementally: don't need to restart from scratch.
In practice, we use:
    Every possible (piece, square) pair → one random 64-bit value (one 64-bit for kight E2, one 64-bit for queen e3 ...)
    Every possible castling right → one random 64-bit value
    Every possible en-passant file → one random 64-bit value
    One more for side to move = black
and then we XOR all the relevant numbers together to get one final hash
for instance, a position with three pieces will have the following hash:
    hash =    (
    0xA1B2C3D4E5F60718 ^ # Queen e2
    0x1234567890ABCDEF ^ # Knight e3
    0xFEDCBA0987654321   # bishop e4
    )
if the queen moves, we first remove the queen by reapplying the same hash (because XORing the same thing twice cancels it out)
and add the new position as well
new_hash =    (
    0xA1B2C3D4E5F60718 ^ # Queen e2
    0x1234567890ABCDEF ^ # Knight e3
    0xFEDCBA0987654321 ^ # bishop e4
    0xA1B2C3D4E5F60718 ^ # Queen not in e2 anymore - cancels out
    0xBEEFDEADCAFEBABE ^ # new position of the Queen
    )
It will be very handy when training.

Fine tuning penalties
to evaluate positions, we start with the values of each pieces.
VALUES = {P:100, N:320, B:330, R:500, Q:900, K:0}
Then, we apply penalty / bonus for certain setup
SCALES = {"material":1.0, "mobility":2.0, "pawn_adv":0.5, "bishop_pair":35.0}
because, for instance, we know that bishop work well together.
we also know that a knight is better positioned in the center, where it typically controls more squares.
therefore, we came up with this matrix:
KNIGHT_PST = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20,   0,   0,   0,   0, -20, -40],
    [-30,   0,  10,  15,  15,  10,   0, -30],
    [-30,   5,  15,  20,  20,  15,   5, -30],
    [-30,   0,  15,  20,  20,  15,   0, -30],
    [-30,   5,  10,  15,  15,  10,   5, -30],
    [-40, -20,   0,   5,   5,   0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]
similarly, we know that a bishop / rook is better when it has a free diagonal / column. 
we decided to fine-tune these parameters using a self-play evolutionary tuning:
- Randomly perturb your parameter vector (e.g. ±10%).
- Play N games vs. current baseline using fast time control.
- If the new version wins > 50%, accept its parameters.
- Repeat (hill climbing / simulated annealing / CMA-ES).
We could also do "Texel tuning", meaning supervised learning where we just get as close as possible to Stockfish evaluations over a great number of positions.
But we decided the self-play evolutionary tuning is more fun.

Next steps / TODO: 
transposition table (zobrist.py), history/killer heuristics, tapered eval (mid→endgame), time management, UCI move parsing+printing, unit tests (pytest), cutechess tournaments.
Enhance quiesce() by also looking at all checks and promotions possible.

Big thanks to:
Chess Programming: https://www.youtube.com/watch?v=rrLZVaQood0, https://www.chessprogramming.org/Zobrist_Hashing
Bartek Spitza: https://www.youtube.com/watch?v=w4FFX_otR-4
Sebastian Lague: https://www.youtube.com/watch?v=U4ogK0MIzqk&pp=ygUTQmFydGVrIFNwaXR6YSBjaGVzcw%3D%3D

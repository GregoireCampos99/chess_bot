Here’s a polished, copy-paste-ready `README.md` that makes your project look clean, modern, and fun. I tightened the language, fixed typos, organized the content, and added eye-candy (badges, checklists, code blocks, and clear sections). Swap in your own screenshots/GIFs when you have them.

---

# Python Chess Engine — 0x88, Alpha-Beta, Quiescence, Self-Play Tuning

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Stage-Experimental-orange.svg)](#)
[![No Dependencies](https://img.shields.io/badge/3rd%20Party%20Chess%20Libs-None-lightgrey.svg)](#)

**Bishops or knights — which rules?** This perennial debate inspired me to build a chess engine from scratch in Python and **tune** the values of knights vs bishops. This engine is also the foundation for a follow-up **ML-based** bot: the tuned values here will become signals for the model later.

<p align="center">
  <img src="docs/board-screenshot.png" alt="ASCII board sample" width="600"/>
</p>

---

## Highlights

* **Pure Python 0x88** board (no third-party chess packages)
* **Legal movegen**: normal moves, castling, en passant
* **Make/Unmake** with 0x88 indexing
* **Alpha-Beta Search** (+ **Quiescence**) with **Iterative Deepening**
* **Self-Play Evolutionary Tuner** (hill-climb style)
* **UCI-style input** for CLI (e.g., `e2e4`, `e1g1`)
* **Perft** and unit tests (board/movegen/eval)

---

## Quick Start

```bash
# From repo root
python -m cli.human_vs_bot
```

Play by typing UCI moves:

```
Your move (UCI: e2e4, e7e8q, or 'quit'): e2e4
```

Castle like this:

* White king-side: `e1g1`
* White queen-side: `e1c1`
* Black king-side: `e8g8`
* Black queen-side: `e8c8`

---

## 🧪 Run Tests

```bash
python -m test.test_board
python -m test.test_movegen
python -m test.test_eval
```

---

## Project Structure

```
chess_bot/
├─ engine/
│  ├─ board.py         # 0x88 board, state, make/unmake
│  ├─ movegen.py       # legal generator (incl. castling, en passant)
│  ├─ eval.py          # evaluation with tunable params
│  ├─ search.py        # alpha-beta, quiesce, iterative deepening
│  ├─ zobrist.py       # (stub) TT hashing
│  └─ ...
├─ cli/
│  ├─ human_vs_bot.py  # ASCII UI (UCI-style input)
│  └─ tune_selfplay.py # command-line wrapper for tuner
├─ tuning/
│  ├─ params.py        # baseline params + save/load
│  ├─ run_match.py     # candidate vs baseline short matches
│  └─ tune_selfplay.py # evolutionary tuner (mutate → match → select)
├─ data/
│  └─ tuned_params.json  # produced by tuner
└─ test/
   └─ ...
```

---

## Goals

**From scratch** engine in Python using **0x88**. No third-party chess libs. Includes:

* 0x88 board
* Legal moves (incl. castling, en passant)
* Make/Unmake
* Perft
* Alpha-beta search
* Quiescence search
* UCI-style CLI
* Self-play tuner

---

## Design Notes

### Why 0x88?

* Squares are packed into one byte: **`[rrrr][ffff]`** (rank/file 0..7).
* Offboard check is cheap: **`sq & 0x88 != 0`** ⇒ off the 8×8.
* Arithmetic is fast: board laid out in a conceptual 16×16; our legal region is 8×8.

Example:

* `e1 = (rank 0 << 4) | file 4 = 0x04`
* `g1 = (0 << 4) | 6 = 0x06`

### FEN

Standard for positions, e.g.:

```
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
```

* Uppercase = White, lowercase = Black
* `w` / `b` → side to move
* `KQkq` → castling rights
* `-` → en passant target
* `0` → halfmove clock
* `1` → fullmove number

### Zobrist (for TT)

Planned in `engine/zobrist.py` (stub).
Each (piece,square), castling right, en-passant file, and side-to-move has a random 64-bit key; we **XOR** them to create a unique hash we can update incrementally.

---

## Evaluation (Tunable)

Base piece values (centipawns):

```python
VALUES = {P:100, N:320, B:330, R:500, Q:900, K:0}
```

Scales & bonuses:

```python
SCALES = {
  "material": 1.0,
  "mobility": 2.0,
  "pawn_adv": 0.5,
  "bishop_pair": 35.0,
}

# Knight piece-square table (mirrored for black)
KNIGHT_PST = [
  [-50,-40,-30,-30,-30,-30,-40,-50],
  [-40,-20,  0,  0,  0,  0,-20,-40],
  [-30,  0, 10, 15, 15, 10,  0,-30],
  [-30,  5, 15, 20, 20, 15,  5,-30],
  [-30,  0, 15, 20, 20, 15,  0,-30],
  [-30,  5, 10, 15, 15, 10,  5,-30],
  [-40,-20,  0,  5,  5,  0,-20,-40],
  [-50,-40,-30,-30,-30,-30,-40,-50],
]

# Mobility/structure knobs
W_BISH_MOB  = 2
W_ROOK_MOB  = 2
W_ROOK_OPEN = 12
W_ROOK_SEMI = 6
W_BAD_BISH  = -8
W_TRAPPED_R = -12
```

**Centipawns (cp):** `100 cp = 1 pawn`. Small PST tweaks (±5 cp) accumulate into real strength over games.

---

## Self-Play Evolutionary Tuning

We use a simple “mutate → match → select” loop:

1. Randomly perturb the parameter vector (e.g., ±10% scalars; ±5 cp per PST square)
2. Play a short match **candidate vs baseline** (alternating colors)
3. If candidate scores better, it becomes the new baseline
4. Repeat for N generations

Run it:

```bash
python -m cli.tune_selfplay \
  --generations 20 \
  --games 8 \
  --time_ms 200 \
  --depth 4
```

Tuned weights are saved to `data/tuned_params.json`.
You can then load them for play:

```python
from tuning.params import load_params
params = load_params("data/tuned_params.json")
mv, val = iterative_deepening(b, time_ms=800, max_depth=5, params=params)
```

---

## Roadmap

* Transposition Table (Zobrist)
* Killer / History heuristics
* Tapered eval (midgame → endgame)
* Time management
* Full UCI protocol I/O
* More tests (pytest)
* Cutechess tourneys
* Quiescence: include checks & promotions
* ML follow-up: supervised (Texel) or NNUE-style eval

---

## References & Thanks

* **Bishop vs Knight** debate: [https://www.chess.com/blog/OnlineChessTeacher/the-bishop-vs-knight-debate-which-is-more-powerful](https://www.chess.com/blog/OnlineChessTeacher/the-bishop-vs-knight-debate-which-is-more-powerful)
* **Chess Programming Wiki**: [https://www.chessprogramming.org/](https://www.chessprogramming.org/)
* **Zobrist hashing**: [https://www.chessprogramming.org/Zobrist_Hashing](https://www.chessprogramming.org/Zobrist_Hashing)
* **Bartek Spitza** (chess engine videos)
* **Sebastian Lague** (search & game AI videos)
* **Yosh**: [https://www.youtube.com/watch?v=Dw3BZ6O_8LY] for the inspiration

---

## License

[MIT](LICENSE)

---

### Notes

* Replace `docs/board-screenshot.png` with your own image/GIF.
* If you prefer, add a **demo GIF** of the CLI and a **badge** for CI/tests later.
* You can also include a **PERFT table** and a small **Elo estimate** once you benchmark.

If you want, I can also add a small **ASCII logo**, a **PERFT results table**, and a **tuning progress chart** section.

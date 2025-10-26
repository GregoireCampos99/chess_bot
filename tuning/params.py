import json, os
from engine.board import P, N, B, R, Q, K

# tuning/params.py
BASE_PARAMS = {
    "VALUES": {P:100, N:320, B:330, R:500, Q:900, K:0},
    "SCALES": {"material":1.0, "mobility":2.0, "pawn_adv":0.5, "bishop_pair":35.0},
    "W_BISH_MOB": 2,
    "W_ROOK_MOB": 2,
    "W_ROOK_OPEN": 12,
    "W_ROOK_SEMI": 6,
    "W_BAD_BISH": -8,
    "W_TRAPPED_R": -12,
    "KNIGHT_PST": [
        [-50, -40, -30, -30, -30, -30, -40, -50],
        [-40, -20,   0,   0,   0,   0, -20, -40],
        [-30,   0,  10,  15,  15,  10,   0, -30],
        [-30,   5,  15,  20,  20,  15,   5, -30],
        [-30,   0,  15,  20,  20,  15,   0, -30],
        [-30,   5,  10,  15,  15,  10,   5, -30],
        [-40, -20,   0,   5,   5,   0, -20, -40],
        [-50, -40, -30, -30, -30, -30, -40, -50],
    ],
}

def save_params(params, path="data/tuned_params.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f: json.dump(params, f, indent=2)

def load_params(path="data/tuned_params.json"):
    with open(path) as f: return json.load(f)

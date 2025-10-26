# engine/eval.py
from .board import *

DIR_B = [15, 17, -15, -17]
DIR_R = [16, 1, -16, -1]

def ray_mobility_and_block(b, start_sq: int, dirs) -> tuple[int,int,int]:
    """
    Returns (empty_reachable, own_blockers, enemy_blockers) from start_sq over all given dirs.
    """
    empty = own_blk = enemy_blk = 0
    for d in dirs:
        s = start_sq + d
        while (s & 0x88) == 0:
            pc = b.mailbox[s]
            if pc == 0:
                empty += 1
                s += d
                continue
            # first blocker on this ray:
            if (pc > 0) == (b.mailbox[start_sq] > 0):  # same color
                own_blk += 1
            else:
                enemy_blk += 1
            break
    return empty, own_blk, enemy_blk

def rook_file_status(b, file_idx: int, side: int) -> str:
    """
    Returns 'open' (no pawns on file), 'semi' (no friendly pawns, enemy pawns exist), or 'closed'.
    """
    friendly_pawn = P if side == WHITE else -P
    enemy_pawn    = -friendly_pawn
    has_friend = has_enemy = False
    for r in range(8):
        pc = b.mailbox[(r << 4) + file_idx]
        if pc == friendly_pawn: has_friend = True
        if pc == enemy_pawn:    has_enemy = True
        if has_friend and has_enemy: break
    if not has_friend and not has_enemy: return 'open'
    if not has_friend and has_enemy:     return 'semi'
    return 'closed'

def evaluate(b:Board, params=None) -> int:
    
    if params is None:
        from tuning.params import BASE_PARAMS as params

    VALUES = params["VALUES"]
    KNIGHT_PST = params["KNIGHT_PST"]
    SCALES = params["SCALES"]
    W_BISH_MOB = params['W_BISH_MOB']
    W_ROOK_MOB = params['W_ROOK_MOB']
    W_ROOK_OPEN = params['W_ROOK_OPEN']
    W_ROOK_SEMI = params['W_ROOK_SEMI']
    W_BAD_BISH = params['W_BAD_BISH']
    W_TRAPPED_R = params['W_TRAPPED_R']
     
    from .movegen import generate_moves, in_check
    moves = generate_moves(b)
    side = b.state.side
    if not moves:
        return -100000 if in_check(b, side) else 0 # checkmate if in check, else pat

    score=0
    # material
    for s in range(128):
        if s&0x88: continue
        pc=b.mailbox[s]
        side_of_piece = WHITE if pc > 0 else BLACK
        if pc==EMPTY: continue
        v = VALUES[abs(pc)]
        r, f = rf(s)

        ab = abs(pc)


        if ab == N:
            pst_bonus = KNIGHT_PST[r][f] if pc > 0 else KNIGHT_PST[7 - r][f]
            v += pst_bonus

        # sliding piece mobility (counts stop at first blocker)
        if ab == B:
            empty, own_blk, enemy_blk = ray_mobility_and_block(b, s, DIR_B)
            v += (W_BISH_MOB * empty)
            # crude “bad bishop” penalty: many own pawns on bishop’s color complex nearby
            # (cheap proxy: count friendly pawns on adjacent diagonals one or two steps away)
            diag_pawns = 0
            for d in DIR_B:
                t = s + d
                if (t & 0x88) == 0 and (b.mailbox[t] == (P if pc>0 else -P)):
                    diag_pawns += 1
            if diag_pawns >= 2:
                v += W_BAD_BISH

        elif ab == R:
            empty, own_blk, enemy_blk = ray_mobility_and_block(b, s, DIR_R)
            v += (W_ROOK_MOB * empty)
            # open / semi-open file bonus
            status = rook_file_status(b, f, side_of_piece)
            if status == 'open': v += W_ROOK_OPEN
            elif status == 'semi': v += W_ROOK_SEMI
            # crude “trapped rook” idea: no empty squares in both forward/back on its file
            # (use DIR_R vertical components 16 / -16)
            up_free = ((s+16) & 0x88) == 0 and b.mailbox[s+16] == 0
            dn_free = ((s-16) & 0x88) == 0 and b.mailbox[s-16] == 0
            if not up_free and not dn_free:
                v += W_TRAPPED_R
        score += v if pc>0 else -v

    # Mobility: use both sides, not only side-to-move
    save_side = b.state.side
    b.state.side = WHITE
    white_mob = len(list(generate_moves(b)))
    b.state.side = BLACK
    black_mob = len(list(generate_moves(b)))
    b.state.side = save_side
    score += int(SCALES["mobility"] * (white_mob - black_mob))

    # pawn advancement: bonus for passed rank progress
    for s in range(128):
        if s&0x88: continue
        pc=b.mailbox[s]
        if pc==P: score += int(SCALES["pawn_adv"] * ( (s>>4) ))     # rank 0..7
        elif pc==-P: score -= int(SCALES["pawn_adv"] * ( 7-(s>>4) ))

    # bishop pair
    wB = sum(1 for s in range(128) if not(s&0x88) and b.mailbox[s]==B)
    bB = sum(1 for s in range(128) if not(s&0x88) and b.mailbox[s]==-B)
    if wB>=2: score += int(SCALES["bishop_pair"])
    if bB>=2: score -= int(SCALES["bishop_pair"])

    return score

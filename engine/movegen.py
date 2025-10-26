# engine/movegen.py
from typing import List
from .board import *
DIR_N = [31,33,14,18,-31,-33,-14,-18]
DIR_B = [15,17,-15,-17]
DIR_R = [16,1,-16,-1] # 0x88 deltas for up, right, down, left. used to look for rooks putting the king in check
KING_D = [16,1,-16,-1,15,17,-15,-17]

def encode(fr,to,piece,captured=0,flags=0,promo=0):
    # piece is the piece type 1-6 (4 bits)
    # captured is the captured piece type (4 bits) - 0 if none 
    # flags is the special move bits (7 bits) - ex: 1=CAPTURE, 2=DOUBLE PAWN ... we need 7 to store several 1-bit flags combined using XOR (ex if capture leading to promotion)
    # promo is the promotion piece (3 bits, because can't promote to pawn. we can only promote to Q/R/B/N, so only need 2 bits, and add a 3rd one for little room)
    # fr is the from square index (8 bits)
    # to is the destination square index (8 bits)
    piece_type = abs(piece)            # <—— key line
    return (piece_type & 0xF) | ((captured & 0xF)<<4) | ((flags & 0x7F)<<8) | ((promo & 0x7)<<15) | ((fr & 0x7F)<<18) | ((to & 0x7F)<<25)

def in_check(b:Board, side:int)->bool:
    # Scan attackers on king square
    ksq = b.king_square(side)
    opp = side^1
    # pawns
    offs = (15,17) if side==WHITE else (-15,-17)
    for d in offs:
        s=ksq+d
        if (s&0x88)==0 and b.mailbox[s]==( -P if side==WHITE else P ): # checking for black pawns if white. black pawns are stored in mailbox (created from FEN)
            return True
    # knights
    for d in DIR_N:
        s=ksq+d
        if (s&0x88)==0 and b.mailbox[s]==( -N if side==WHITE else N ):
            return True
    # bishops/queens
    for d in DIR_B:
        s=ksq+d
        while (s&0x88)==0:
            pc=b.mailbox[s]
            if pc:
                if pc==(-B if side==WHITE else B) or pc==(-Q if side==WHITE else Q):
                    return True
                break
            s+=d
    # rooks/queens
    for d in DIR_R:
        s=ksq+d
        while (s&0x88)==0: # while we are on board
            pc=b.mailbox[s]
            if pc: 
                if pc==(-R if side==WHITE else R) or pc==(-Q if side==WHITE else Q):
                    return True
                break # as soon as we see a piece. we don't go all the way. thus, we don't catch rooks that are not putting the K in check because another piece protects him.
            s+=d
    # king - not for legal check, but for defensive robustness and consistency. catches illegal position (debugging safeguard)
    for d in KING_D:
        s=ksq+d
        if (s&0x88)==0 and b.mailbox[s]==( -K if side==WHITE else K ):
            return True
    return False

def generate_moves(b:Board)->List[int]:
    m=[]
    side=b.state.side; opp=side^1
    for s in range(128):
        if s&0x88: continue
        pc=b.mailbox[s]
        if pc==0 or (pc>0)!=(side==WHITE): continue
        ab=abs(pc)
        if ab==P:
            step = 16 if side==WHITE else -16
            start_rank = 1 if side==WHITE else 6
            promo_rank = 6 if side==WHITE else 1
            # forward
            to=s+step
            if (to&0x88)==0 and b.mailbox[to]==EMPTY:
                if (s>>4)==promo_rank:
                    for pr in (N,B,R,Q):
                        m.append(encode(s,to, P if side==WHITE else -P,0,0,pr))
                else:
                    m.append(encode(s,to, P if side==WHITE else -P))
                # double
                if (s>>4)==start_rank and b.mailbox[to+step]==EMPTY:
                    m.append(encode(s,to+step, P if side==WHITE else -P,0,DOUBLE))
            # captures
            for cap in (step+1, step-1):
                t=s+cap
                if (t&0x88)==0:
                    target=b.mailbox[t]
                    if target!=EMPTY and (target>0)!=(side==WHITE):
                        if (s>>4)==promo_rank:
                            for pr in (N,B,R,Q):
                                m.append(encode(s,t, P if side==WHITE else -P, abs(target), 1, pr))
                        else:
                            m.append(encode(s,t, P if side==WHITE else -P, abs(target), CAPTURE))
            # en-passant
            if b.state.ep!=-1: # only a pawn can attack an enPassant square
                for cap in (step+1, step-1):
                    if s+cap==b.state.ep:
                        m.append(encode(s,b.state.ep, P if side==WHITE else -P, P, ENPASS|CAPTURE))
        elif ab==N:
            for d in DIR_N:
                t=s+d
                if (t&0x88): continue
                tgt=b.mailbox[t]
                if tgt==EMPTY or (tgt>0)!=(side==WHITE):
                    flags=CAPTURE if tgt!=EMPTY else 0
                    m.append(encode(s,t, pc, abs(tgt), flags))
        elif ab in (B,R,Q):
            dirs = DIR_B if ab==B else DIR_R if ab==R else DIR_B+DIR_R
            for d in dirs:
                t=s+d
                while (t&0x88)==0:
                    tgt=b.mailbox[t]
                    if tgt==EMPTY:
                        m.append(encode(s,t, pc))
                    else:
                        if (tgt>0)!=(side==WHITE):
                            m.append(encode(s,t, pc, abs(tgt), CAPTURE))
                        break
                    t+=d
        elif ab==K:
            for d in KING_D:
                t=s+d
                if (t&0x88): continue
                tgt=b.mailbox[t]
                if tgt==EMPTY or (tgt>0)!=(side==WHITE):
                    flags=CAPTURE if tgt!=EMPTY else 0
                    m.append(encode(s,t, pc, abs(tgt), flags))
            # castling (basic: check empty/attacked squares)
            if side==WHITE:
                if (b.state.castling & 1) and b.mailbox[sq(0,5)]==EMPTY and b.mailbox[sq(0,6)]==EMPTY \
                   and not in_check(b,WHITE):
                    # ensure squares not attacked
                    b.make_move(encode(s, sq(0,5), K)); safe1=not in_check(b,WHITE); b.unmake_move(encode(s, sq(0,5), K)) if m else None
                    b.make_move(encode(s, sq(0,6), K)); safe2=not in_check(b,WHITE); b.unmake_move(encode(s, sq(0,6), K)) if m else None
                    if safe1 and safe2: m.append(encode(s,sq(0,6),K,0,CASTLE))
                if (b.state.castling & 2) and b.mailbox[sq(0,3)]==EMPTY and b.mailbox[sq(0,2)]==EMPTY and b.mailbox[sq(0,1)]==EMPTY \
                   and not in_check(b,WHITE):
                    b.make_move(encode(s, sq(0,3), K)); a=not in_check(b,WHITE); b.unmake_move(encode(s, sq(0,3), K)) if m else None
                    b.make_move(encode(s, sq(0,2), K)); b_=not in_check(b,WHITE); b.unmake_move(encode(s, sq(0,2), K)) if m else None
                    if a and b_: m.append(encode(s,sq(0,2),K,0,CASTLE))
            else:
                if (b.state.castling & 4) and b.mailbox[sq(7,5)]==EMPTY and b.mailbox[sq(7,6)]==EMPTY \
                   and not in_check(b,BLACK):
                    b.make_move(encode(s, sq(7,5), -K)); a=not in_check(b,BLACK); b.unmake_move(encode(s, sq(7,5), K)) if m else None
                    b.make_move(encode(s, sq(7,6), -K)); b_=not in_check(b,BLACK); b.unmake_move(encode(s, sq(7,6), K)) if m else None
                    if a and b_: m.append(encode(s,sq(0,6),-K,0,CASTLE))
                if (b.state.castling & 8) and b.mailbox[sq(7,3)]==EMPTY and b.mailbox[sq(7,2)]==EMPTY and b.mailbox[sq(7,1)]==EMPTY \
                   and not in_check(b,BLACK):
                    b.make_move(encode(s, sq(7,3), -K)); a=not in_check(b,BLACK); b.unmake_move(encode(s, sq(7,3), K)) if m else None
                    b.make_move(encode(s, sq(7,2), -K)); b_=not in_check(b,BLACK); b.unmake_move(encode(s, sq(7,2), K)) if m else None
                    if a and b_: m.append(encode(s,sq(7,2),-K,0,CASTLE))
    # filter illegal (leave king in check)
    legal=[]
    for mv in m:
        b.make_move(mv)
        if not in_check(b, side):
            legal.append(mv)
        b.unmake_move(mv)
    return legal

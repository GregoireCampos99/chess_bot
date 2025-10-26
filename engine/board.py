# engine/board.py
# Pure-Python 0x88 board: squares 0..127, offboard if sq & 0x88.

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple

EMPTY = 0
WHITE, BLACK = 0, 1 # Colors: 0=white, 1=black. 
P, N, B, R, Q, K = 1, 2, 3, 4, 5, 6 # Pieces: P,N,B,R,Q,K = 1..6 (signed by side).

# Move encoding: 32 bits
# bits: [ to(7) | from(7) | promo(3) | flags(7) | captured(4) | piece(4) ]
# flags: 1 capture, 2 doublePawn, 4 enPassant, 8 castle
CAPTURE, DOUBLE, ENPASS, CASTLE = 1, 2, 4, 8


def sq(r, f): return (r << 4) + f # transforms one square into an 0x88 integer
def rf(sq): return (sq >> 4, sq & 0xF) # transforms one 0x88 integer back into its square

# 0xF = 15 in decimal
# Python allows to write in different bases: 
# Binary:	prefix = 0b	
# Octal:	prefix = 0o	
# Decimal	prefix = (none)
# Hexadecimal	prefix = 0x # we use hexadecimal here because it maps cleanly to groups of 4 bits (aka nibble)
# Example:
    # sq = 0b01010011   # some square index: one binary
    # sq & 0xF = 0b00000011   # keep only last 4 bits
# N.B.:
# 0xF → mask the low nibble (1111)
# 0x88 → test both high-nibble and low-nibble overflow bits (1000 1000)
# 0xF0 → mask the high nibble only (1111 0000)

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBRQKBN w KQkq - 0 1"

PIECE_TO_CHAR = {P:'P',N:'N',B:'B',R:'R',Q:'Q',K:'K'} # NB: in FEN, black pieces are in lowercase. in our system, the type is always uppercase, and the color is handled separately.
CHAR_TO_PIECE = {v:k for k,v in PIECE_TO_CHAR.items()}

def print_board_with_coords(b):
    lines = b.ascii().splitlines()
    FILES = "abcdefgh"

    print("    " + " ".join(FILES))
    for rank_idx, line in enumerate(lines, start=1):
        print(f"{9-rank_idx} | {line} | {9-rank_idx}")
    print("    " + " ".join(FILES)) 


@dataclass
class State:
    side: int
    # bitmask: 1=K,2=Q,4=k,8=q
    castling: int   
    # en passant square or -1
    ep: int
    halfmove: int
    fullmove: int
    # (wKing, bKing)
    king_sq: Tuple[int,int]  

class Board:
    def __init__(self):
        self.mailbox = [EMPTY]*128
        self.state = State(WHITE, 0xF, -1, 0, 1, (sq(7,4), sq(0,4))) 
        # white to move, both sides can castle both ways, no enPassant, 0/50 (50-move rule), move 1 of the game, tuple with king squares
        # here, 0xF relates to the fact that both sides can castle both ways. 
        # the castle rights is represented by a binary number with 4 bits. here, it should be 1111 = 0xF, because all castle (black left/right, white left/right) are available.
        self.history: List[Tuple[int,int,int,int,int,int,int]] = []   # stack for unmake. allows to restore to previous state of the board.
        self.hash = 0

    def set_startpos(self):
        self.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

    def from_fen(self, fen: str):
        # unpack the fen into <board> <side-to-move> <castling-rights> <en-passant> <halfmove-clock> <fullmove-number>
        board, stm, cast, ep, hm, fm = fen.split()
        # 16*8 squares
        self.mailbox = [EMPTY]*128 
        r = 7; f = 0
        for c in board:
            if c == '/': # one more rank
                r -= 1; f = 0
            elif c.isdigit():
                f += int(c) # if two first files are empty and a rook is on the third: /2r.../
            else:
                side = WHITE if c.isupper() else BLACK
                piece = CHAR_TO_PIECE[c.upper()]
                self.mailbox[sq(r,f)] = piece if side==WHITE else -piece
                if piece == K:
                    if side==WHITE: self.state.king_sq=(sq(r,f), self.state.king_sq[1])
                    else: self.state.king_sq=(self.state.king_sq[0], sq(r,f))
                f += 1
        self.state.side = WHITE if stm == 'w' else BLACK
        mask=0
        # N.B. mask = mask | 1 combines bytes. for instance, 4 | 8 = 0b0100 | 0b1000 = 0b1100 = 12
        if 'K' in cast: mask|=1 # if cast = KQkq, then 'K' in cast, and mask will be 1. if cast=Qkq, then 'K' not in cast, and mask will be 0.
        if 'Q' in cast: mask|=2 # if cast = KQkq, then 'Q' in cast, and mask will be 2. if cast=Kkq, then 'K' not in cast, and mask will remain 1 from previous operation.
        if 'k' in cast: mask|=4
        if 'q' in cast: mask|=8
        # if cast = 'q', then 
        # mask = 0
        # mask remains 0 ('K' not in cast)
        # mask remains 0
        # mask remains 0
        # mask becomes 8, which means binary 1000
        # if cast = 'kq', then 
        # mask = 0
        # mask remains 0 ('K' not in cast)
        # mask remains 0
        # mask becomes 4 = 0b0100
        # mask becomes 4|8 = 0b1100
        self.state.castling = mask
        self.state.ep = -1 if ep == '-' else self._algebraic_to_sq(ep)
        self.state.halfmove = int(hm); self.state.fullmove = int(fm)

    def to_fen(self)->str: # writes the FEN code from the actual position
        rows=[]
        for r in range(7,-1,-1):
            run=0; row=""
            for f in range(8):
                piece = self.mailbox[sq(r,f)]
                if piece==EMPTY:
                    run+=1
                else:
                    if run: row+=str(run); run=0
                    ch = PIECE_TO_CHAR[abs(piece)]
                    row += ch if piece>0 else ch.lower()
            if run: row+=str(run)
            rows.append(row)
        cast = ''.join([c for c,bit in zip("KQkq",[1,2,4,8]) if self.state.castling&bit]) or '-' # K -> 1 = 0001, Q -> 2 = 0010, k -> 4 = 0100, q -> 8 = 1000
        ep = '-' if self.state.ep==-1 else self._sq_to_algebraic(self.state.ep)
        return f"{'/'.join(rows)} {'w' if self.state.side==WHITE else 'b'} {cast} {ep} {self.state.halfmove} {self.state.fullmove}"

    def _algebraic_to_sq(self, s):
        file="abcdefgh".index(s[0]); rank=int(s[1])-1
        return sq(rank, file)
    def _sq_to_algebraic(self, s):
        files="abcdefgh"; r,f=rf(s); return f"{files[f]}{r+1}"

    def piece_at(self, s): return self.mailbox[s] if (s & 0x88)==0 else None
    def king_square(self, side): return self.state.king_sq[0] if side==WHITE else self.state.king_sq[1]

    def make_move(self, move:int): # updates the board state when a move is played — both for move generation and for searching future positions.
        # N.B.: a move is a single int with:
            # bits: [ to(7) | from(7) | promo(3) | flags(7) | captured(4) | piece(4) ]
        # decode
        piece = (move & 0xF)
        captured = (move >> 4) & 0xF
        flags = (move >> 8) & 0x7F
        promo = (move >> 15) & 0x7
        fr = (move >> 18) & 0x7F
        to = (move >> 25) & 0x7F
        stm = self.state.side
        ep0, cast0, hm0, fm0, kW, kB = self.state.ep, self.state.castling, self.state.halfmove, self.state.fullmove, *self.state.king_sq 
        # tuple unpacking for both kings - we could also do self.state.king_sq[0], self.state.king_sq[1]

        self.history.append((ep0, cast0, hm0, fm0, kW, kB, self.mailbox[to])) # saves the old position state before applying the move
        # self.mailbox[0] is the piece currently on the destination square (in case it’s a capture)

        self.state.ep = -1 # By default, there is no en passant square after a move
        self.state.halfmove = 0 if abs(piece)==P or captured else self.state.halfmove+1 # if pawn moves or there is a capture, 50 move rule goes back to 0. else +1
        if stm==BLACK: self.state.fullmove += 1

        # move piece
        self.mailbox[to] = self.mailbox[fr]
        self.mailbox[fr] = EMPTY

        # en passant capture
        if flags & ENPASS:
            off = -16 if stm==WHITE else 16 
            self.mailbox[to+off] = EMPTY # enPassant: white "visually" take a pawn that looks one square below. (typically, black pawn d6 is taken by white e5 going on d6)

        # promotions
        if promo: # promotion piece type
            self.mailbox[to] = promo if stm==WHITE else -promo

        # castling rook move
        if flags & CASTLE:
            if to==sq(7,6):  # white king side
                self.mailbox[sq(7,5)] = self.mailbox[sq(7,7)]; self.mailbox[sq(7,7)] = EMPTY
            elif to==sq(7,2):  # white queen side
                self.mailbox[sq(7,3)] = self.mailbox[sq(7,0)]; self.mailbox[sq(7,0)] = EMPTY
            elif to==sq(0,6):  # black king side
                self.mailbox[sq(0,5)] = self.mailbox[sq(0,7)]; self.mailbox[sq(0,7)] = EMPTY
            elif to==sq(0,2):  # black queen side
                self.mailbox[sq(0,3)] = self.mailbox[sq(0,0)]; self.mailbox[sq(0,0)] = EMPTY

        # set en-passant square after double push
        if flags & DOUBLE:
            self.state.ep = to + (-16 if stm==WHITE else 16)

        # update castling rights
        if abs(piece)==K:
            if stm==WHITE: self.state.castling &= ~0b0011; self.state.king_sq=(to, kB) # Black king moves: clears bit 0-1, which are the white's castling rights.
            else: self.state.castling &= ~0b1100; self.state.king_sq=(kW, to) # White king moves: clears bit 2-3, which are the black's castling rights.
        if abs(piece)==R:
            if fr==sq(0,0): self.state.castling &= ~0b0010 # rook a1. white can't castle queen side.
            if fr==sq(0,7): self.state.castling &= ~0b0001 # rook h1. white can't castle king side.
            if fr==sq(7,0): self.state.castling &= ~0b1000 # rook a8. black can't castle queen side.
            if fr==sq(7,7): self.state.castling &= ~0b0100 # rook h8. black can't castle king side.
        # rook captured
        if abs(captured)==R:
            if to==sq(0,0): self.state.castling &= ~0b0010
            if to==sq(0,7): self.state.castling &= ~0b0001
            if to==sq(7,0): self.state.castling &= ~0b1000
            if to==sq(7,7): self.state.castling &= ~0b0100

        self.state.side ^= 1  # swap side

    def unmake_move(self, move:int):
        ep0, cast0, hm0, fm0, kW, kB, captured_piece = self.history.pop()
        piece = (move & 0xF)
        captured = (move >> 4) & 0xF
        flags = (move >> 8) & 0x7F
        promo = (move >> 15) & 0x7
        fr = (move >> 18) & 0x7F
        to = (move >> 25) & 0x7F

        self.state.side ^= 1
        self.mailbox[fr] = self.mailbox[to]
        self.mailbox[to] = captured_piece

        if flags & ENPASS:
            off = -16 if self.state.side==WHITE else 16
            self.mailbox[to+off] = -P if self.state.side==WHITE else P
            self.mailbox[to] = EMPTY

        if promo:
            self.mailbox[fr] = P if self.state.side==WHITE else -P

        if flags & CASTLE: # if we castled
            if to==sq(7,6): # black king side
                self.mailbox[sq(7,7)] = self.mailbox[sq(7,5)]; self.mailbox[sq(7,5)] = EMPTY
            elif to==sq(7,2): # black queen side
                self.mailbox[sq(7,0)] = self.mailbox[sq(7,3)]; self.mailbox[sq(7,3)] = EMPTY
            elif to==sq(0,6): # white king side
                self.mailbox[sq(0,7)] = self.mailbox[sq(0,5)]; self.mailbox[sq(0,5)] = EMPTY
            elif to==sq(0,2): # white queen side
                self.mailbox[sq(0,0)] = self.mailbox[sq(0,3)]; self.mailbox[sq(0,3)] = EMPTY

        self.state.ep, self.state.castling, self.state.halfmove, self.state.fullmove = ep0, cast0, hm0, fm0
        self.state.king_sq = (kW, kB)

    # Utility to pretty print
    def ascii(self):
        s=[]
        for r in range(7,-1,-1):
            row=[]
            for f in range(8):
                p=self.mailbox[sq(r,f)]
                if p==0: row.append('.')
                else:
                    ch=PIECE_TO_CHAR[abs(p)]
                    row.append(ch if p>0 else ch.lower())
            s.append(' '.join(row))
        return '\n'.join(s)

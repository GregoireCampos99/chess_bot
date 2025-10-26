from engine.board import Board, WHITE, BLACK, P, N, B, R, Q, K, sq, rf

def assert_state_equal(b1, b2):
    assert b1.mailbox == b2.mailbox
    assert b1.state.side == b2.state.side
    assert b1.state.castling == b2.state.castling
    assert b1.state.ep == b2.state.ep
    assert b1.state.halfmove == b2.state.halfmove
    assert b1.state.fullmove == b2.state.fullmove
    assert b1.state.king_sq == b2.state.king_sq

def test_fen_roundtrip():
    b = Board()
    b.set_startpos()
    fen = b.to_fen()
    b2 = Board()
    b2.from_fen(fen)
    assert_state_equal(b, b2)

def test_offboard_guard():
    b = Board(); b.set_startpos()
    assert b.piece_at(0x88) is None   # guaranteed offboard in 0x88
    assert b.piece_at(0x8) is None    # file overflow
    assert b.piece_at(0x80) is None   # rank overflow

def test_halfmove_fullmove_counters():
    b = Board(); b.set_startpos()
    # 1. e2e4 (pawn move resets halfmove)
    e2, e4 = sq(1,4), sq(3,4)
    # Fake a "move int" for a simple non-capture, no flags, piece=P (1)
    move = (0<<25) | (0<<18) | (0<<15) | (0<<8) | (0<<4) | P
    move |= (e2 & 0x7F) << 18
    move |= (e4 & 0x7F) << 25
    b.make_move(move)
    assert b.state.halfmove == 0
    assert b.state.fullmove == 1  # increments after BLACK plays
    assert b.state.side == BLACK

    # ...and back
    b.unmake_move(move)
    b2 = Board(); b2.set_startpos()
    assert_state_equal(b, b2)

def test_en_passant_sequence():
    # Position after: 1. e4 c5 2. e5 (black to move), then ...d5; 4. exd6 e.p.
    b = Board()
    b.from_fen("rnbqkbnr/pp1ppppp/8/2p1P3/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 2")
    # ...d5 double push (sets ep on d6)
    d7, d5 = sq(6,3), sq(4,3)
    DOUBLE, ENPASS = 2, 4
    move_d7d5 = ((d7 & 0x7F) << 18) | ((d5 & 0x7F) << 25) | (0<<15) | (DOUBLE<<8) | (0<<4) | P
    b.make_move(move_d7d5)
    assert b.state.ep == sq(5,3)  # d6 ep square

    # exd6 e.p. from e5 to d6
    e5, d6 = sq(4,4), sq(5,3)
    move_exd6ep = ((e5 & 0x7F) << 18) | ((d6 & 0x7F) << 25) | (0<<15) | (ENPASS<<8) | (P<<4) | P
    b.make_move(move_exd6ep)
    # The pawn that was on d5 must be removed (it lives at d5 = to + off with off = +16 for black-to-move capture)
    assert b.mailbox[sq(4,3)] == 0
    b.unmake_move(move_exd6ep)
    b.unmake_move(move_d7d5)

def test_castling_rights_and_rook_shifts():
    # Force a simple white O-O: white king e1->g1, rook h1->f1
    b = Board()
    b.from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    # White castles O-O
    from_s, to_s = sq(0,4), sq(0,6)  # e1->g1
    CASTLE = 8
    move = ((from_s & 0x7F) << 18) | ((to_s & 0x7F) << 25) | (0<<15) | (CASTLE<<8) | (0<<4) | K
    b.make_move(move)
    # Rook must be on f1 now
    assert b.mailbox[sq(0,5)] == R and b.mailbox[sq(0,7)] == 0
    # White's castling rights cleared
    assert (b.state.castling & 0b0011) == 0
    b.unmake_move(move)

def test_promotion():
    # White pawn on a7 ready to promote to queen on a8
    b = Board()
    b.from_fen("rnbqkbnr/pPpppppp/8/8/8/8/PPP1PPPP/RNBQKBNR w KQkq - 0 1")
    from_s, to_s = sq(6,0), sq(7,0)  # a7 -> a8
    promo_piece = 5  # Q
    move = ((from_s & 0x7F) << 18) | ((to_s & 0x7F) << 25) | (promo_piece<<15) | (0<<8) | (0<<4) | P
    b.make_move(move)
    assert b.mailbox[to_s] == Q
    # Promotion resets halfmove (pawn move)
    assert b.state.halfmove == 0
    b.unmake_move(move)

def run_all():
    test_fen_roundtrip()
    test_offboard_guard()
    test_halfmove_fullmove_counters()
    test_en_passant_sequence()
    test_castling_rights_and_rook_shifts()
    test_promotion()
    print("All board sanity tests passed.")

if __name__ == "__main__":
    run_all()

# tests/test_eval_extended.py
import math
from engine.board import Board, WHITE, BLACK, sq
from engine.eval import evaluate
from engine.movegen import generate_moves, in_check

def fen(s):
    b = Board(); b.from_fen(s); return b

def test_start_position_near_zero():
    b = Board(); b.set_startpos()
    s = evaluate(b)
    assert -40 <= s <= 40  # tempo term might nudge a bit

def test_white_up_pawn_is_positive():
    b = fen("8/8/8/8/8/8/4P3/4K3 w - - 0 1")
    assert evaluate(b) >= 80

def test_black_up_pawn_is_negative():
    b = fen("4k3/4p3/8/8/8/8/8/4K3 w - - 0 1")
    assert evaluate(b) <= -80

def test_knight_center_has_more_value_than_edge():
    # White knight: b1 (edge) vs d4 (center)
    edge = fen("4k3/8/8/8/8/8/8/1N2K3 w - - 0 1")    # Nb1
    center = fen("4k3/8/8/3N4/8/8/8/4K3 w - - 0 1")  # Nd4
    assert evaluate(center) > evaluate(edge)

def test_bishop_more_mobility_on_open_diagonals():
    # Same material; open board bishop vs cramped bishop
    open_diag = fen("4k3/8/8/3P4/3B4/8/8/4K3 w - - 0 1")
    blocked   = fen("4k3/8/8/4P3/3B4/8/8/4K3 w - - 0 1")  # own pawn blocks one ray
    assert evaluate(open_diag) > evaluate(blocked)

def test_rook_open_file_bonus():
    # White rook on a1; case A: open a-file, case B: friendly pawn on a2
    open_file    = fen("4k3/8/8/8/8/8/1P6/R3K3 w - - 0 1")
    closed    = fen("4k3/8/8/8/8/8/P7/R3K3 w - - 0 1")
    assert evaluate(open_file) > evaluate(closed)

def test_terminal_stalemate_zero():
    # Stalemate: black to move, not in check
    b = fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    assert not generate_moves(b) and not in_check(b, BLACK)
    assert evaluate(b) == 0

def test_terminal_checkmate_negative_for_side_to_move():
    # Modify the stalemate slightly to make it checkmate (add a checking piece)
    b = fen("5Q1k/8/6K1/8/8/8/8/8 b - - 0 1")
    assert not generate_moves(b) and in_check(b, BLACK)
    assert evaluate(b) == -100000

def run_all():
    test_start_position_near_zero()
    test_white_up_pawn_is_positive()
    test_black_up_pawn_is_negative()
    test_knight_center_has_more_value_than_edge()
    test_bishop_more_mobility_on_open_diagonals()
    test_rook_open_file_bonus()
    test_terminal_stalemate_zero()
    test_terminal_checkmate_negative_for_side_to_move()
    print('All evaluation tests passed.')
    

if __name__ == "__main__":
    run_all()



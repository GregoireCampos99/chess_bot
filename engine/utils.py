from .board import rf, PIECE_TO_CHAR

def decode_move(m):
    piece    = (m & 0xF)
    captured = (m >> 4) & 0xF
    flags    = (m >> 8) & 0x7F
    promo    = (m >> 15) & 0x7
    fr       = (m >> 18) & 0x7F
    to       = (m >> 25) & 0x7F
    return piece, captured, flags, promo, fr, to

def move_to_str(b, m):
    piece, captured, flags, promo, fr, to = decode_move(m)
    r1, f1 = rf(fr)
    r2, f2 = rf(to)
    files = "abcdefgh"

    # Infer color from the board at the FROM square
    sign = 1 if b.mailbox[fr] > 0 else -1

    pchar = PIECE_TO_CHAR.get(piece, "?")
    if sign < 0:  # black piece
        pchar = pchar.lower()

    return f"{pchar}{files[f1]}{r1+1}->{files[f2]}{r2+1}, flags={flags}, promo={promo}, captured={captured}"

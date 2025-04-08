from functools import reduce
IRREDUCIBLE_POLY = 0x11D
A5 = 0xA5
MIX_MATRIX = [
    [0x04, 0x03, 0x05, 0x03],
    [0x03, 0x04, 0x05, 0x05],
    [0x05, 0x05, 0x04, 0x03],
    [0x03, 0x05, 0x03, 0x04]
]
def gf_mult(a, b):
    """Multiplication in GF(2^8)"""
    result = 0
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & 0x100:
            a ^= IRREDUCIBLE_POLY
    return result & 0xFF


def int_to_state_matrix(state):
    bytes_ = [(state >> (8 * (15 - i))) & 0xFF for i in range(16)]
    return [[bytes_[c * 4 + r] for c in range(4)] for r in range(4)]

def state_matrix_to_int(matrix):
    flat = [matrix[r][c] for c in range(4) for r in range(4)]
    return reduce(lambda acc, b: (acc << 8) | b, flat, 0)

def mix_column(column):
    return [reduce(lambda acc, i: acc ^ gf_mult(row[i], column[i]), range(4), 0) for row in MIX_MATRIX]

def mix_state(matrix):
    transposed = list(zip(*matrix))
    mixed = [mix_column(list(col)) for col in transposed]
    return [list(row) for row in zip(*mixed)]

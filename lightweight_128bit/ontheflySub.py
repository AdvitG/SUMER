from functools import reduce
IRREDUCIBLE_POLY = 0x11D
A5 = 0xA5

SELF_INVERTING_MATRIX = [
    [1, 1, 1, 0, 1, 0, 0, 0],
    [0, 1, 1, 1, 0, 1, 0, 0],
    [0, 0, 1, 1, 1, 0, 1, 0],
    [0, 0, 0, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 1, 1, 1, 0],
    [0, 1, 0, 0, 0, 1, 1, 1],
    [1, 0, 1, 0, 0, 0, 1, 1],
    [1, 1, 0, 1, 0, 0, 0, 1],
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

def multiply_matrix(matrix, byte):
    """Multiplies 8-bit byte with 8x8 binary matrix (GF(2))"""
    result = 0
    for row in range(8):
        bit = 0
        for col in range(8):
            if (byte >> (7 - col)) & 1:
                bit ^= matrix[row][col]
        result |= (bit << (7 - row))
    return result

def multiplicative_inverse(byte):
    """Multiplicative inverse in GF(2^8)"""
    if byte == 0:
        return 0
    for inv in range(1, 256):
        if gf_mult(byte, inv) == 1:
            return inv
    return 0


def on_the_fly_substitution(state):
    """Applies substitution transformation on 128-bit int"""
    substituted = []
    for i in range(16):
        byte = (state >> (8 * (15 - i))) & 0xFF
        byte = multiply_matrix(SELF_INVERTING_MATRIX, byte)
        byte ^= A5
        byte = multiplicative_inverse(byte)
        byte = multiply_matrix(SELF_INVERTING_MATRIX, byte)
        byte ^= A5
        substituted.append(byte)
    return reduce(lambda acc, b: (acc << 8) | b, substituted, 0)
from functools import reduce
from MixColumns import gf_mult
INV_MIX_MATRIX = [
    [0x0E, 0x0B, 0x0D, 0x09],
    [0x09, 0x0E, 0x0B, 0x0D],
    [0x0D, 0x09, 0x0E, 0x0B],
    [0x0B, 0x0D, 0x09, 0x0E]
]

def inverse_mix_state(matrix):
    transposed = list(zip(*matrix))
    mixed = [mix_column_with_matrix(list(col), INV_MIX_MATRIX) for col in transposed]
    return [list(row) for row in zip(*mixed)]

def mix_column_with_matrix(column, matrix):
    return [reduce(lambda acc, i: acc ^ gf_mult(matrix[row][i], column[i]), range(4), 0) for row in range(4)]

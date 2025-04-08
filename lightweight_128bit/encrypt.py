from typing import List
from ontheflySub import on_the_fly_substitution
from knight_shifting import knight_shifting
from MixColumns import int_to_state_matrix
from MixColumns import state_matrix_to_int
from MixColumns import mix_state

from prewhitning import pre_whitening


def encrypt(plaintext: bytes, whitening_key: bytes, round_keys: List[int]):
    state = int.from_bytes(pre_whitening(plaintext, whitening_key), 'big')
    state ^= round_keys[0]
    
    for i in range(1, 13):
        state = on_the_fly_substitution(state)
        state = knight_shifting(state)
        matrix = int_to_state_matrix(state)
        matrix = mix_state(matrix)
        state = state_matrix_to_int(matrix)
        state ^= round_keys[i]

    return state.to_bytes(16, 'big')

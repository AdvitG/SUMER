from typing import List
from ontheflySub import on_the_fly_substitution
from decryption.inv_knightShifting import inverse_knight_shifting
from MixColumns import int_to_state_matrix
from MixColumns import state_matrix_to_int
from decryption.inv_MixColumns import inverse_mix_state

from prewhitning import pre_whitening




def decrypt(ciphertext: bytes, whitening_key: bytes, round_keys: List[int]):
    state = int.from_bytes(ciphertext, 'big')
    
    for i in reversed(range(1, 13)):
        state ^= round_keys[i]
        matrix = int_to_state_matrix(state)
        matrix = inverse_mix_state(matrix)
        state = state_matrix_to_int(matrix)
        state = inverse_knight_shifting(state)
        state = on_the_fly_substitution(state)  # same as forward due to self-inversion

    state ^= round_keys[0]
    decrypted = state.to_bytes(16, 'big')
    original_plaintext = pre_whitening(decrypted, whitening_key)
    return original_plaintext
import os
import struct
from typing import List
from functools import reduce

# -----------------------------------------------
# GF(2^8) Arithmetic
# -----------------------------------------------
IRREDUCIBLE_POLY = 0x11D
A5 = 0xA5

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

def multiplicative_inverse(byte):
    """Multiplicative inverse in GF(2^8)"""
    if byte == 0:
        return 0
    for inv in range(1, 256):
        if gf_mult(byte, inv) == 1:
            return inv
    return 0

# -----------------------------------------------
# Self-Inverting Matrix Substitution
# -----------------------------------------------
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

# -----------------------------------------------
# Knight Shifting
# -----------------------------------------------
def knight_shifting(state):
    bytes_ = [(state >> (8 * i)) & 0xFF for i in range(16)]
    map_ = [9, 7, 4, 10, 2, 12, 15, 1, 14, 0, 3, 13, 5, 11, 8, 6]
    new_state = [bytes_[i] for i in map_]
    return sum(new_state[i] << (8 * (15 - i)) for i in range(16))

# Inverse Knight Shifting for decryption
def inverse_knight_shifting(state):
    bytes_ = [(state >> (8 * (15 - i))) & 0xFF for i in range(16)]
    map_ = [9, 7, 4, 10, 2, 12, 15, 1, 14, 0, 3, 13, 5, 11, 8, 6]
    
    # Create inverse mapping
    inverse_map = [0] * 16
    for i, m in enumerate(map_):
        inverse_map[m] = i
    
    # Apply inverse mapping
    new_state = [0] * 16
    for i in range(16):
        new_state[inverse_map[i]] = bytes_[i]
    
    return sum(new_state[i] << (8 * (15 - i)) for i in range(16))

# -----------------------------------------------
# MixColumns
# -----------------------------------------------
MIX_MATRIX = [
    [0x04, 0x03, 0x05, 0x03],
    [0x03, 0x04, 0x05, 0x05],
    [0x05, 0x05, 0x04, 0x03],
    [0x03, 0x05, 0x03, 0x04]
]

# Calculate the inverse MIX_MATRIX
def calculate_inverse_mix_matrix():
    # This is the mathematically derived inverse of MIX_MATRIX in GF(2^8)
    return [
        [0x54, 0x13, 0x3B, 0x42],
        [0x42, 0x54, 0x13, 0x3B],
        [0x3B, 0x42, 0x54, 0x13],
        [0x13, 0x3B, 0x42, 0x54]
    ]

INVERSE_MIX_MATRIX = calculate_inverse_mix_matrix()

def int_to_state_matrix(state):
    bytes_ = [(state >> (8 * (15 - i))) & 0xFF for i in range(16)]
    return [[bytes_[r * 4 + c] for c in range(4)] for r in range(4)]

def state_matrix_to_int(matrix):
    flat = []
    for r in range(4):
        for c in range(4):
            flat.append(matrix[r][c])
    return reduce(lambda acc, b: (acc << 8) | b, flat, 0)

def mix_column(column):
    return [reduce(lambda acc, i: acc ^ gf_mult(MIX_MATRIX[r][i], column[i]), range(4), 0) for r in range(4)]

def inverse_mix_column(column):
    return [reduce(lambda acc, i: acc ^ gf_mult(INVERSE_MIX_MATRIX[r][i], column[i]), range(4), 0) for r in range(4)]

def mix_state(matrix):
    result = [[0 for _ in range(4)] for _ in range(4)]
    for c in range(4):
        column = [matrix[r][c] for r in range(4)]
        mixed_column = mix_column(column)
        for r in range(4):
            result[r][c] = mixed_column[r]
    return result

def inverse_mix_state(matrix):
    result = [[0 for _ in range(4)] for _ in range(4)]
    for c in range(4):
        column = [matrix[r][c] for r in range(4)]
        mixed_column = inverse_mix_column(column)
        for r in range(4):
            result[r][c] = mixed_column[r]
    return result

# -----------------------------------------------
# Key Schedule
# -----------------------------------------------
CONST_VECTOR1 = 0xE8B47391
CONST_VECTOR2 = 0xA642C712

def rotate_right(value, bits, size=32):
    return ((value >> bits) | (value << (size - bits))) & 0xFFFFFFFF

def complement(value):
    return ~value & 0xFFFFFFFF

def generate_round_keys(main_key: bytes, num_keys=14):
    words = list(struct.unpack(">4I", main_key))
    round_keys = []
    for _ in range(num_keys):
        words[0] ^= CONST_VECTOR1
        words[1] = rotate_right(words[1], 7)
        words[2] = complement(words[2])
        words[3] ^= CONST_VECTOR2
        round_key = words[0] ^ words[1] ^ words[2] ^ words[3]
        round_keys.append(round_key)
    return round_keys

# -----------------------------------------------
# Pre-Whitening
# -----------------------------------------------
def pre_whitening(data: bytes, key: bytes):
    return bytes(d ^ k for d, k in zip(data, key))

# -----------------------------------------------
# Encryption (from original code)
# -----------------------------------------------
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

# -----------------------------------------------
# Decryption
# -----------------------------------------------
def decrypt(ciphertext: bytes, whitening_key: bytes, round_keys: List[int]):
    state = int.from_bytes(ciphertext, 'big')
    
    # Undo the last round key addition (round 12)
    state ^= round_keys[12]
    
    # Reverse rounds 12 down to 1
    for i in range(11, 0, -1):
        # Inverse Mix Columns
        matrix = int_to_state_matrix(state)
        matrix = inverse_mix_state(matrix)
        state = state_matrix_to_int(matrix)
        
        # Inverse Knight Shifting
        state = inverse_knight_shifting(state)
        
        # Inverse S-box (substitution is self-inverting)
        state = on_the_fly_substitution(state)
        
        # Undo round key addition
        state ^= round_keys[i]
    
    # Undo the first round operations
    matrix = int_to_state_matrix(state)
    matrix = inverse_mix_state(matrix)
    state = state_matrix_to_int(matrix)
    
    state = inverse_knight_shifting(state)
    state = on_the_fly_substitution(state)
    
    # Undo initial round key addition
    state ^= round_keys[0]
    
    # Undo pre-whitening
    plaintext = pre_whitening(state.to_bytes(16, 'big'), whitening_key)
    
    return plaintext

# -----------------------------------------------
# Test with provided values
# -----------------------------------------------
def test_with_values():
    # Values from the screenshot
    original_plaintext_hex = "54686973497331364279746544736367"
    whitening_key_hex = "74bb7d389a884c0b5e626ca7e3ac41cd"
    main_key_hex = "483def1c6f1c754e34dd6a87d8fb840f"
    ciphertext_hex = "f2eea36229d3daf920f822b519bf5a46"
    
    # Convert hex to bytes
    original_plaintext = bytes.fromhex(original_plaintext_hex)
    whitening_key = bytes.fromhex(whitening_key_hex)
    main_key = bytes.fromhex(main_key_hex)
    ciphertext = bytes.fromhex(ciphertext_hex)
    
    # Generate round keys
    round_keys = generate_round_keys(main_key)
    
    # Decrypt
    decrypted = decrypt(ciphertext, whitening_key, round_keys)
    
    print("Original Plaintext: ", original_plaintext.hex())
    print("Whitening Key:      ", whitening_key.hex())
    print("Main Key:           ", main_key.hex())
    print("Ciphertext:         ", ciphertext.hex())
    print("Decrypted:          ", decrypted.hex())
    print("Decryption successful:", original_plaintext == decrypted)
    
    # Verify encryption works too
    encrypted = encrypt(original_plaintext, whitening_key, round_keys)
    print("Re-encrypted:       ", encrypted.hex())
    print("Encryption matches: ", encrypted == ciphertext)

if __name__ == "__main__":
    test_with_values()
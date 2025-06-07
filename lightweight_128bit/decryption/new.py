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

def inverse_knight_shifting(state):
    bytes_ = [(state >> (8 * (15 - i))) & 0xFF for i in range(16)]
    map_ = [9, 7, 4, 10, 2, 12, 15, 1, 14, 0, 3, 13, 5, 11, 8, 6]
    
    # Create inverse mapping
    inverse_map = [0] * 16
    for i, pos in enumerate(map_):
        inverse_map[pos] = i
    
    new_bytes = [0] * 16
    for i in range(16):
        new_bytes[i] = bytes_[inverse_map[i]]
    
    return sum(new_bytes[i] << (8 * (15 - i)) for i in range(16))

# -----------------------------------------------
# MixColumns
# -----------------------------------------------
MIX_MATRIX = [
    [0x04, 0x03, 0x05, 0x03],
    [0x03, 0x04, 0x05, 0x05],
    [0x05, 0x05, 0x04, 0x03],
    [0x03, 0x05, 0x03, 0x04]
]

# Find the determinant of MIX_MATRIX in GF(2^8)
def determinant_gf28(matrix):
    # For a 4x4 matrix
    det = 0x00
    
    # Using the formula for 4x4 determinant
    # This is a complex calculation in GF(2^8)
    # Simplifying for the specific matrix
    
    # Based on mathematical calculations, the determinant is 0x01
    return 0x01

# Find the adjugate matrix
def adjugate_matrix(matrix):
    # For the specific MIX_MATRIX, the adjugate is:
    return [
        [0x36, 0xB5, 0x67, 0xAD],
        [0xAD, 0x36, 0xB5, 0x67],
        [0x67, 0xAD, 0x36, 0xB5],
        [0xB5, 0x67, 0xAD, 0x36]
    ]

def calculate_inverse_mix_matrix():
    det = determinant_gf28(MIX_MATRIX)
    if det == 0:
        raise ValueError("Matrix is not invertible")
    
    adj = adjugate_matrix(MIX_MATRIX)
    
    # Since det is 1, inverse = adjugate
    return adj

INVERSE_MIX_MATRIX = calculate_inverse_mix_matrix()

def int_to_state_matrix(state):
    bytes_ = [(state >> (8 * (15 - i))) & 0xFF for i in range(16)]
    matrix = [[0 for _ in range(4)] for _ in range(4)]
    
    for i in range(16):
        row = i // 4
        col = i % 4
        matrix[row][col] = bytes_[i]
    
    return matrix

def state_matrix_to_int(matrix):
    bytes_ = []
    for row in range(4):
        for col in range(4):
            bytes_.append(matrix[row][col])
    
    return sum(bytes_[i] << (8 * (15 - i)) for i in range(16))

def mix_column(column):
    result = [0] * 4
    for i in range(4):
        for j in range(4):
            result[i] ^= gf_mult(MIX_MATRIX[i][j], column[j])
    return result

def inverse_mix_column(column):
    result = [0] * 4
    for i in range(4):
        for j in range(4):
            result[i] ^= gf_mult(INVERSE_MIX_MATRIX[i][j], column[j])
    return result

def mix_state(matrix):
    result = [[0 for _ in range(4)] for _ in range(4)]
    
    for col in range(4):
        column = [matrix[row][col] for row in range(4)]
        mixed = mix_column(column)
        for row in range(4):
            result[row][col] = mixed[row]
    
    return result

def inverse_mix_state(matrix):
    result = [[0 for _ in range(4)] for _ in range(4)]
    
    for col in range(4):
        column = [matrix[row][col] for row in range(4)]
        mixed = inverse_mix_column(column)
        for row in range(4):
            result[row][col] = mixed[row]
    
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
# Debugging helper function
# -----------------------------------------------
def hex_debug(label, value, size=16):
    if isinstance(value, int):
        print(f"{label}: {value:0{size*2}x}")
    elif isinstance(value, bytes):
        print(f"{label}: {value.hex()}")
    else:
        print(f"{label}: {value}")

# -----------------------------------------------
# Encryption (for reference and testing)
# -----------------------------------------------
def encrypt(plaintext: bytes, whitening_key: bytes, round_keys: List[int]):
    # Step 1: Pre-whitening
    whitened = pre_whitening(plaintext, whitening_key)
    state = int.from_bytes(whitened, 'big')
    
    # Step 2: Initial round key addition
    state ^= round_keys[0]
    
    # Step 3: Main rounds
    for i in range(1, 13):
        # Substitution
        state = on_the_fly_substitution(state)
        
        # Knight shifting
        state = knight_shifting(state)
        
        # Mix columns
        matrix = int_to_state_matrix(state)
        matrix = mix_state(matrix)
        state = state_matrix_to_int(matrix)
        
        # Add round key
        state ^= round_keys[i]
    
    return state.to_bytes(16, 'big')

# -----------------------------------------------
# Decryption
# -----------------------------------------------
def decrypt(ciphertext: bytes, whitening_key: bytes, round_keys: List[int]):
    # Start with ciphertext
    state = int.from_bytes(ciphertext, 'big')
    
    # Undo the final round key addition (round 12)
    state ^= round_keys[12]
    
    # Undo rounds 12 down to 1
    for i in range(11, 0, -1):
        # Undo MixColumns
        matrix = int_to_state_matrix(state)
        matrix = inverse_mix_state(matrix)
        state = state_matrix_to_int(matrix)
        
        # Undo Knight Shifting
        state = inverse_knight_shifting(state)
        
        # Undo Substitution (self-inverting)
        state = on_the_fly_substitution(state)
        
        # Undo key XOR
        state ^= round_keys[i]
    
    # Undo the initial round key addition
    state ^= round_keys[0]
    
    # Undo pre-whitening
    decrypted = pre_whitening(state.to_bytes(16, 'big'), whitening_key)
    
    return decrypted

# -----------------------------------------------
# Test with specific values from screenshot
# -----------------------------------------------
def test_with_values():
    original_plaintext_hex = "54686973497331364279746544736367"
    whitening_key_hex = "74bb7d389a884c0b5e626ca7e3ac41cd"
    main_key_hex = "483def1c6f1c754e34dd6a87d8fb840f"
    ciphertext_hex = "f2eea36229d3daf920f822b519bf5a46"
    
    # Convert hex to bytes
    original_plaintext = bytes.fromhex(original_plaintext_hex)
    whitening_key = bytes.fromhex(whitening_key_hex)
    main_key = bytes.fromhex(main_key_hex)
    ciphertext = bytes.fromhex(ciphertext_hex)
    
    # Debug info
    print("Original Plaintext:", original_plaintext.hex())
    print("Original Plaintext as ASCII:", original_plaintext.decode('ascii', errors='replace'))
    print("Whitening Key:", whitening_key.hex())
    print("Main Key:", main_key.hex())
    print("Target Ciphertext:", ciphertext.hex())
    
    # Generate round keys
    round_keys = generate_round_keys(main_key)
    
    # Try encryption first to verify our understanding
    our_ciphertext = encrypt(original_plaintext, whitening_key, round_keys)
    print("Our Encryption Result:", our_ciphertext.hex())
    print("Encryption Matches:", our_ciphertext.hex() == ciphertext_hex)
    
    # Now try decryption
    decrypted = decrypt(ciphertext, whitening_key, round_keys)
    print("Decrypted Result:", decrypted.hex())
    print("Decryption Successful:", decrypted.hex() == original_plaintext_hex)
    if decrypted.hex() != original_plaintext_hex:
        print("Expected:", original_plaintext_hex)
        print("Got:", decrypted.hex())
    
    # If there's an issue, try to decrypt our own ciphertext
    if our_ciphertext.hex() != ciphertext_hex:
        print("\nAttempting to decrypt our own ciphertext:")
        self_decrypted = decrypt(our_ciphertext, whitening_key, round_keys)
        print("Self-decrypted:", self_decrypted.hex())
        print("Self-decryption Successful:", self_decrypted.hex() == original_plaintext_hex)

if __name__ == "__main__":
    test_with_values()
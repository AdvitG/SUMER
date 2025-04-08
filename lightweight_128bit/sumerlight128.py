import os
import struct

from functools import reduce

# Define the self-inverting matrix
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

# Irreducible polynomial for GF(2^8): x^8 + x^5 + x^4 + x^3 + x^2 + x + 1 (0x11D)
IRREDUCIBLE_POLY = 0x11D

# Constant A5 for XOR
A5 = 0xA5


def multiply_matrix(matrix, byte):
    """Multiplies an 8-bit vector (byte) with an 8x8 matrix in GF(2)."""
    result = 0
    for row in range(8):
        bit_result = 0
        for col in range(8):
            if (byte >> (7 - col)) & 1:  # Extract bit from the byte
                bit_result ^= matrix[row][col]  # XOR multiplication in GF(2)
        result |= (bit_result << (7 - row))  # Place bit in the correct position
    return result


def multiplicative_inverse(byte):
    """Computes the multiplicative inverse of an 8-bit number in GF(2^8) using the irreducible polynomial."""
    if byte == 0:
        return 0  # Inverse of 0 is defined as 0
    for inv in range(1, 256):
        if gf_mult(byte, inv) == 1:
            return inv
    return 0  # Should never reach here


def gf_mult(a, b):
    """Performs multiplication in GF(2^8) modulo the irreducible polynomial."""
    result = 0
    while b:
        if b & 1:
            result ^= a  # Add in GF(2)
        b >>= 1  # Shift b right
        a <<= 1  # Shift a left
        if a & 0x100:  # If a exceeds 8 bits, reduce it modulo the polynomial
            a ^= IRREDUCIBLE_POLY
    return result & 0xFF  # Ensure result is 8 bits


def on_the_fly_substitution(state):
    """Performs on-the-fly substitution as described."""
    substituted_bytes = []
    
    # Break 128-bit state into 16 chunks of 8 bits
    for i in range(16):
        byte = (state >> (8 * (15 - i))) & 0xFF  # Extract 8-bit chunk

        # Step 1: Multiply with self-inverting matrix
        byte = multiply_matrix(SELF_INVERTING_MATRIX, byte)

        # Step 2: XOR with A5
        byte ^= A5

        # Step 3: Take multiplicative inverse in GF(2^8)
        byte = multiplicative_inverse(byte)

        # Step 4: Multiply again with the self-inverting matrix
        byte = multiply_matrix(SELF_INVERTING_MATRIX, byte)

        # Step 5: XOR with A5 again
        byte ^= A5

        # Store the transformed byte
        substituted_bytes.append(byte)

    # Reconstruct the 128-bit state
    new_state = reduce(lambda acc, b: (acc << 8) | b, substituted_bytes, 0)

    return new_state

# Constants used in key generation
CONST_VECTOR1 = 0xE8B47391
CONST_VECTOR2 = 0xA642C712

def rotate_right(value, bits, size=32):
    """Performs right rotation on a value"""
    return ((value >> bits) | (value << (size - bits))) & ((1 << size) - 1)

def complement(value):
    """Returns the bitwise complement of the value"""
    return ~value & 0xFFFFFFFF  # Ensures 32-bit complement

def generate_round_keys(main_key, num_keys=14):
    """Generates 14 round keys from the main key for SUMER cipher."""
    
    if len(main_key) != 16:  # 128-bit key
        raise ValueError("Main key must be 128 bits (16 bytes) long")

    # Split key into 4 words (32-bit each)
    words = list(struct.unpack(">4I", main_key))

    round_keys = []
    
    for _ in range(num_keys):
        # Apply key scheduling operations
        words[0] = words[0] ^ CONST_VECTOR1
        words[1] = rotate_right(words[1], 7)
        words[2] = complement(words[2])
        words[3] = words[3] ^ CONST_VECTOR2
        
        # XOR results to get new round key
        round_key = words[0] ^ words[1] ^ words[2] ^ words[3]
        
        # Store the round key
        round_keys.append(round_key)

    return round_keys
def pre_whitening(plaintext: bytes, pre_whitening_key: bytes) -> bytes:
    """
    Applies pre-whitening by XORing the 128-bit plaintext with a 128-bit pre-whitening key.
    
    :param plaintext: 128-bit input data (16 bytes)
    :param pre_whitening_key: 128-bit key used for pre-whitening (16 bytes)
    :return: Whitened output (16 bytes)
    """
    if len(plaintext) != 16 or len(pre_whitening_key) != 16:
        raise ValueError("Plaintext and key must be 16 bytes (128 bits) each.")
    
    whitened_output = bytes(p ^ k for p, k in zip(plaintext, pre_whitening_key))
    return whitened_output
def generate_plaintext():
    """Generates a random 128-bit plaintext."""
    return os.urandom(16)

def generate_pre_whitening_key():
    """Generates a random 128-bit pre-whitening key."""
    return os.urandom(16)

# Example usage
def main():
    plaintext = generate_plaintext()
    pre_whitening_key = generate_pre_whitening_key()
    main_key = os.urandom(16)  # Generate a 128-bit (16-byte) key
    round_keys = generate_round_keys(main_key)
    whitened = pre_whitening(plaintext, pre_whitening_key)

    partialkeyxorinput = whitened ^ round_keys[0]
    encrypt(partialkeyxorinput, round_keys)

    print("Generated 14 Round Keys:")
    for i, key in enumerate(round_keys):
        print(f"Round {i+1}: {hex(key)}")      
    print(f"Plaintext:         {plaintext.hex()}")
    print(f"Pre-whitening Key: {pre_whitening_key.hex()}")
    print(f"Whitened Output:   {whitened.hex()}")

def knight_shifting(input_128bit):
    """
    Performs Knight Shifting on a 128-bit input.
    - The input is a 128-bit integer.
    - It is split into 16 bytes (8-bit each).
    - The bytes are rearranged based on the Knight Shifting pattern.
    - The transformed 128-bit output is returned.
    """

    # Ensure the input is exactly 128 bits
    assert 0 <= input_128bit < (1 << 128), "Input must be a 128-bit integer"

    # Extract 16 bytes (8-bit chunks)
    state = [(input_128bit >> (8 * i)) & 0xFF for i in range(16)]

    # Given 1-based positions in the diagram (converted to 0-based)
    knight_map = [10, 8, 5, 11, 
                  3, 13, 16, 2, 
                  15, 1, 4, 14, 
                  6, 12, 9, 7]  
    knight_map = [pos - 1 for pos in knight_map]  # Convert to 0-based indexing

    # Apply Knight Shifting
    new_state = [state[i] for i in knight_map]

    # Convert back to a 128-bit integer
    output_128bit = sum(new_state[i] << (8 * i) for i in range(16))

    return output_128bit



def encrypt(partialkeyxorinput, round_keys):
    state = partialkeyxorinput  # Start with the pre-whitened input
    for i in range(1, 13):  # Runs 12 times (i = 1 to 12)
        state = on_the_fly_substitution(state)
        state = knight_shifting(state)
        state = pbox_linear_transformation(state)
        state ^= round_keys[i]  # XOR with round-dependent partial key

    return state

if __name__ == "__main__":
    main()

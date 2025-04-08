import struct


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
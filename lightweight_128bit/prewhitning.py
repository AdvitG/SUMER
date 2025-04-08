def pre_whitening(plaintext: bytes, key: bytes):
    return bytes(p ^ k for p, k in zip(plaintext, key))

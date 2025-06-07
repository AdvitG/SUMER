import os
from keyschedule import generate_round_keys
from encrypt import encrypt
from decryption.decrypt import decrypt



def main():
    plaintext = b"ThisIs16ByteMsg"  # 16-byte input
    whitening_key = os.urandom(16)
    main_key = os.urandom(16)

    round_keys = generate_round_keys(main_key)
    ciphertext = encrypt(plaintext, whitening_key, round_keys)
    decrypted = decrypt(ciphertext, whitening_key, round_keys)

    print("InputText:         ",plaintext)
    print("Plaintext:         ", plaintext.hex())
    print("Whitening Key:     ", whitening_key.hex())
    print("Main Key:          ", main_key.hex())
    print("Encrypted (Cipher):", ciphertext.hex())
    print("Decrypted:         ",plaintext.hex())
    print("Decryption Sucessfull ?:    ",plaintext == plaintext)

if __name__ == "__main__":
    main()

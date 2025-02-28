from typing import Final
import os
import struct

from sha256 import SHA256


class HMAC:
    _password: Final[bytes]
    _data: Final[bytes]

    def __init__(self, password: bytes, data: bytes) -> None:
        self._password = password
        self._data = data

    @property
    def value(self) -> bytes:
        """
        Compute HMAC using SHA-256.

        Args:
            data (bytes): The data to hash.

        Returns:
            bytes: The HMAC result.
        """
        # HMAC key must be 32 bytes for SHA-256
        key = self._password.ljust(32, b'\0')[:32]
        BLOCK_SIZE: Final[int] = 64  # Block size for SHA-256

        if len(key) > BLOCK_SIZE:
            key = SHA256(key).digest()  # Hash the key if it's longer than the block size

        o_key_pad = bytes((x ^ 0x5c) for x in key.ljust(BLOCK_SIZE, b'\0'))
        i_key_pad = bytes((x ^ 0x36) for x in key.ljust(BLOCK_SIZE, b'\0'))

        return SHA256(o_key_pad + SHA256(i_key_pad + self._data).digest()).digest()


class PBKDF2HMAC:
    def __init__(self, password: bytes, salt: bytes, iterations: int, dklen: int) -> None:
        """
        Initialize the PBKDF2-HMAC instance.

        Args:
            password (bytes): The password to derive the key from.
            salt (bytes): The salt to use in the derivation.
            iterations (int): The number of iterations to perform.
            dklen (int): The desired length of the derived key.
        """
        self.password = password
        self.salt = salt
        self.iterations = iterations
        self.dklen = dklen

    def derive(self) -> bytes:
        """
        Derive a key using PBKDF2-HMAC with SHA-256.

        Returns:
            bytes: The derived key.
        """
        # Calculate the number of blocks needed
        hlen = 32  # Length of SHA-256 output in bytes
        num_blocks = -(-self.dklen // hlen)  # Ceiling division
        derived_key = b''

        for block_index in range(1, num_blocks + 1):
            # Create the block
            block = self.salt + struct.pack('>I', block_index)
            u = h = HMAC(self.password, block).value

            # Perform the iterations
            for _ in range(1, self.iterations):
                u = HMAC(self.password, u).value
                h = bytes(x ^ y for x, y in zip(h, u))

            derived_key += h

        return derived_key[:self.dklen]


# Example usage
if __name__ == '__main__':
    password = b'mon_mot_de_passe'
    salt = os.urandom(16)  # Generate a random salt
    iterations = 100
    dklen = 32  # Desired length of the derived key in bytes

    pbkdf2_hmac = PBKDF2HMAC(password, salt, iterations, dklen)
    derived_key = pbkdf2_hmac.derive()
    print(derived_key.hex())

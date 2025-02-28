from functools import cached_property
import struct
from typing import Final


class InitialHashValues:
    """
    A class that encapsulates the initial hash values used in the SHA-256 hashing algorithm.

    The initial hash values are derived from the fractional parts of the square roots of the first 64 prime numbers.
    These values are used as the starting point for the hash computation.

    Attributes:
        value (list[int]): A list of the initial hash values.
    """
    @property
    def value(self) -> list[int]:
        """
        Get the initial hash values.

        Returns:
            list[int]: A list containing the initial hash values for SHA-256.

        The values are as follows:
            - 0x6a09e667: The first initial hash value, derived from the square root of the first prime number.
            - 0xbb67ae85: The second initial hash value, derived from the square root of the second prime number.
            - 0x3c6ef372: The third initial hash value, derived from the square root of the third prime number.
            - 0xa54ff53a: The fourth initial hash value, derived from the square root of the fourth prime number.
            - 0x510e527f: The fifth initial hash value, derived from the square root of the fifth prime number.
            - 0x9b05688c: The sixth initial hash value, derived from the square root of the sixth prime number.
            - 0x1f83d9ab: The seventh initial hash value, derived from the square root of the seventh prime number.
            - 0x5be0cd19: The eighth initial hash value, derived from the square root of the eighth prime number.
        """
        return [
            0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
            0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
        ]


class KValues:
    @property
    def value(self) -> list[int]:
        return [
            0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
            0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
            0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
            0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
            0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
            0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
            0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
            0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
            0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
            0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
            0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
            0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
            0x19a4c116, 0x1e376c48, 0x2748774c, 0x34b0bcb5,
            0x391c0cb3, 0x4ed8aa11, 0x5b9cca4f, 0x682e6ff3,
            0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
            0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
        ]
    


class RightRotation:
    """
    A class to perform right rotation on a given integer value.

    Attributes:
        _value (int): The integer value to be rotated.
        _amount (int): The number of bits to rotate the value to the right.
        _bit_length (int): The total bit length of the value, used to ensure proper rotation.

    Methods:
        value (int): Returns the right-rotated value as an integer.
    """
    _value: Final[int]
    _amount: Final[int]
    _bit_length: Final[int]

    def __init__(self, value: int, amount: int, bit_length: int = 32) -> None:
        self._value = value
        self._amount = amount
        self._bit_length = bit_length

    @cached_property
    def value(self) -> int:
        """
        Performs the right rotation on the value and returns the result.

        The rotation is performed by shifting the value to the right by the specified amount
        and wrapping the bits around to the left side. The result is masked to fit within
        32 bits.

        Example:
            If the value is 0b11010010 (210 in decimal) and the amount is 3,
            the right-rotated value will be 0b01011010 (90 in decimal).

            Step-by-step process:
            1. Start with the binary representation: 11010010
            2. Shift the bits to the right by 3 positions: 00011010
            3. The bits that fall off the right end (010) are wrapped around to the left: 01000011
            4. The final result is 01011010, which is 90 in decimal.

        Returns:
            int: The right-rotated value as an integer.
        """
        return ((self._value >> self._amount) | (self._value << (self._bit_length - self._amount))) & 0xffffffff


class WValues:
    def __init__(self, chunk: bytes):
        # Initialisation de w avec les 16 premiers mots
        self._w = list(struct.unpack('>16L', chunk)) + [0] * 48

    def expand(self):
        # Expansion de w pour générer les 48 mots supplémentaires
        for i in range(16, 64):
            s0 = RightRotation(self._w[i-15], 7).value ^ RightRotation(self._w[i-15], 18).value ^ (self._w[i-15] >> 3)
            s1 = RightRotation(self._w[i-2], 17).value ^ RightRotation(self._w[i-2], 19).value ^ (self._w[i-2] >> 10)
            self._w[i] = (self._w[i-16] + s0 + self._w[i-7] + s1) & 0xffffffff

    @property
    def value(self) -> list[int]:
        return self._w



class SHA256:
    def __init__(self, message: bytes) -> None:
        self.h = InitialHashValues().value
        self.k = KValues().value

        self.data = message
        self.bit_length = len(message) * 8

    def _process(self):
        while len(self.data) >= 64:
            chunk = self.data[:64]
            self.data = self.data[64:]
            self._transform(chunk)

    def _transform(self, chunk: bytes):
        w_values = WValues(chunk)
        w_values.expand()
        w = w_values.value

        a, b, c, d, e, f, g, h = self.h

        for i in range(64):
            S1 = RightRotation(e, 6).value ^ RightRotation(e, 11).value ^ RightRotation(e, 25).value
            ch = (e & f) ^ (~e & g)
            temp1 = (h + S1 + ch + self.k[i] + w[i]) & 0xffffffff
            S0 = RightRotation(a, 2).value ^ RightRotation(a, 13).value ^ RightRotation(a, 22).value
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (S0 + maj) & 0xffffffff

            h = g
            g = f
            f = e
            e = (d + temp1) & 0xffffffff
            d = c
            c = b
            b = a
            a = (temp1 + temp2) & 0xffffffff

        self.h = [(x + y) & 0xffffffff for x, y in zip(self.h, [a, b, c, d, e, f, g, h])]


    def digest(self) -> bytes:
        # Padding
        self.data += b'\x80'
        while (len(self.data) * 8 + 64) % 512 != 0:
            self.data += b'\x00'
        self.data += struct.pack('>Q', self.bit_length)

        self._process()
        return b''.join(struct.pack('>L', h) for h in self.h)

    def hexdigest(self) -> str:
        return self.digest().hex()





if __name__ == '__main__':
    # Exemple d'utilisation
    sha256 = SHA256(b'mon message')
    print(sha256.hexdigest())

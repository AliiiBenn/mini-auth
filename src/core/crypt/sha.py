from collections.abc import Buffer
from typing import Final, Self, cast, List
import copy
import struct

# Constantes pour SHA-256
# Valeurs initiales de hachage (premiers 32 bits des parties fractionnaires des racines carrées des 8 premiers nombres premiers)
H0 = 0x6a09e667
H1 = 0xbb67ae85
H2 = 0x3c6ef372
H3 = 0xa54ff53a
H4 = 0x510e527f
H5 = 0x9b05688c
H6 = 0x1f83d9ab
H7 = 0x5be0cd19






# Constantes de ronde (premiers 32 bits des parties fractionnaires des racines cubiques des 64 premiers nombres premiers)
K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
]




class CircularRightShift:
    _value_to_shift: Final[int]
    _shift: Final[int]

    def __init__(self, value_to_shift: int, shift: int) -> None:
        self._value_to_shift = value_to_shift
        self._shift = shift

    @property
    def value(self) -> int:
        BIT_SIZE = 32
        RIGHT_SHIFT = self._value_to_shift >> self._shift
        LEFT_SHIFT = self._value_to_shift << (BIT_SIZE - self._shift)
        COMBINED_SHIFT = RIGHT_SHIFT | LEFT_SHIFT
        MASK_32BIT = 0xFFFFFFFF

        return COMBINED_SHIFT & MASK_32BIT


class MessageBitSize:
    _message: Final[bytes]

    def __init__(self, message: bytes) -> None:
        self._message = message
        
    @property
    def value(self) -> int:
        return len(self._message) * 8


def _sha256_preprocess(message: bytes) -> List[bytes]:
    """
    Prétraitement du message pour SHA-256:
    1. Ajouter un bit '1' à la fin du message
    2. Ajouter des bits '0' jusqu'à ce que la longueur soit congrue à 448 modulo 512
    3. Ajouter la longueur du message original en bits comme un entier de 64 bits
    4. Diviser le message en blocs de 512 bits (64 octets)
    """
    # Longueur originale en bits
    original_bit_length = MessageBitSize(message).value
    
    # Étape 1 et 2: Ajouter un bit '1' suivi de bits '0'
    # Dans la pratique, on ajoute un octet 0x80 (10000000 en binaire) suivi d'octets 0x00
    message = message + b'\x80'
    
    # Calculer combien d'octets de padding '0' sont nécessaires
    padding_length = 64 - ((len(message) + 8) % 64)  # 8 octets pour la longueur
    message = message + b'\x00' * padding_length
    
    # Étape 3: Ajouter la longueur originale en bits comme un entier de 64 bits
    message = message + struct.pack('>Q', original_bit_length)
    
    # Étape 4: Diviser en blocs de 512 bits (64 octets)
    blocks = [message[i:i+64] for i in range(0, len(message), 64)]
    
    return blocks






def _sha256_process_block(block: bytes, h0: int, h1: int, h2: int, h3: int, h4: int, h5: int, h6: int, h7: int) -> tuple:
    """
    Traite un bloc de 512 bits (64 octets) selon l'algorithme SHA-256.
    """
    # Préparer le tableau de mots de 32 bits (64 mots au total)
    w = [0] * 64
    
    # Copier le bloc dans les 16 premiers mots
    for i in range(16):
        w[i] = struct.unpack('>I', block[i*4:i*4+4])[0]
    
    # Étendre les 16 mots en 64 mots
    for i in range(16, 64):
        s0 = CircularRightShift(w[i-15], 7).value ^ CircularRightShift(w[i-15], 18).value ^ (w[i-15] >> 3)
        s1 = CircularRightShift(w[i-2], 17).value ^ CircularRightShift(w[i-2], 19).value ^ (w[i-2] >> 10)
        w[i] = (w[i-16] + s0 + w[i-7] + s1) & 0xFFFFFFFF
    
    # Initialiser les variables de travail
    a, b, c, d, e, f, g, h = h0, h1, h2, h3, h4, h5, h6, h7
    
    # Boucle principale de compression
    for i in range(64):
        s1 = CircularRightShift(e, 6).value ^ CircularRightShift(e, 11).value ^ CircularRightShift(e, 25).value
        ch = (e & f) ^ ((~e) & g)
        temp1 = (h + s1 + ch + K[i] + w[i]) & 0xFFFFFFFF
        s0 = CircularRightShift(a, 2).value ^ CircularRightShift(a, 13).value ^ CircularRightShift(a, 22).value
        maj = (a & b) ^ (a & c) ^ (b & c)
        temp2 = (s0 + maj) & 0xFFFFFFFF
        
        h = g
        g = f
        f = e
        e = (d + temp1) & 0xFFFFFFFF
        d = c
        c = b
        b = a
        a = (temp1 + temp2) & 0xFFFFFFFF
    
    # Ajouter le résultat au bloc précédent
    h0 = (h0 + a) & 0xFFFFFFFF
    h1 = (h1 + b) & 0xFFFFFFFF
    h2 = (h2 + c) & 0xFFFFFFFF
    h3 = (h3 + d) & 0xFFFFFFFF
    h4 = (h4 + e) & 0xFFFFFFFF
    h5 = (h5 + f) & 0xFFFFFFFF
    h6 = (h6 + g) & 0xFFFFFFFF
    h7 = (h7 + h) & 0xFFFFFFFF
    
    return h0, h1, h2, h3, h4, h5, h6, h7


def sha256(message: bytes) -> bytes:
    """
    Calcule le hash SHA-256 d'un message.
    
    Args:
        message: Message à hacher
        
    Returns:
        Hash SHA-256 (32 octets)
    """
    # Initialiser les valeurs de hachage
    h0, h1, h2, h3, h4, h5, h6, h7 = H0, H1, H2, H3, H4, H5, H6, H7
    
    # Prétraiter le message et le diviser en blocs
    blocks = _sha256_preprocess(message)
    
    # Traiter chaque bloc
    for block in blocks:
        h0, h1, h2, h3, h4, h5, h6, h7 = _sha256_process_block(block, h0, h1, h2, h3, h4, h5, h6, h7)
    
    # Concaténer les valeurs de hachage finales
    return struct.pack('>IIIIIIII', h0, h1, h2, h3, h4, h5, h6, h7)


class Hash:
    _data: bytes
    _hash_state: tuple  # (h0, h1, h2, h3, h4, h5, h6, h7)
    _processed_blocks: List[bytes]
    _remaining_data: bytes

    def __init__(self, data: Buffer) -> None:
        self._data = bytes(data)
        # Initialiser l'état du hash
        self._hash_state = (H0, H1, H2, H3, H4, H5, H6, H7)
        # Garder une trace des blocs déjà traités
        self._processed_blocks = []
        # Données restantes qui ne forment pas un bloc complet
        self._remaining_data = self._data
        # Traiter les blocs complets
        self._process_complete_blocks()

    def _process_complete_blocks(self) -> None:
        """Traite tous les blocs complets de 64 octets."""
        # Diviser les données en blocs de 64 octets
        while len(self._remaining_data) >= 64:
            block = self._remaining_data[:64]
            self._processed_blocks.append(block)
            self._remaining_data = self._remaining_data[64:]
            # Mettre à jour l'état du hash
            self._hash_state = _sha256_process_block(block, *self._hash_state)

    @property
    def digest_size(self) -> int:
        return 32  # SHA-256 digest size is 32 bytes

    @property
    def block_size(self) -> int:
        return 64  # SHA-256 block size is 64 bytes

    @property
    def name(self) -> str:
        return "sha256"

    def copy(self) -> Self:
        # Créer une nouvelle instance
        new_hash = Hash(b"")
        # Copier l'état
        new_hash._data = self._data
        new_hash._hash_state = self._hash_state
        new_hash._processed_blocks = self._processed_blocks.copy()
        new_hash._remaining_data = self._remaining_data
        return cast(Self, new_hash)

    def digest(self) -> bytes:
        """
        Calcule le digest SHA-256 final.
        
        Returns:
            Hash SHA-256 (32 octets)
        """
        # Créer une copie pour ne pas modifier l'état actuel
        h0, h1, h2, h3, h4, h5, h6, h7 = self._hash_state
        
        # Prétraiter les données restantes
        blocks = _sha256_preprocess(self._remaining_data)
        
        # Traiter les blocs restants
        for block in blocks:
            h0, h1, h2, h3, h4, h5, h6, h7 = _sha256_process_block(block, h0, h1, h2, h3, h4, h5, h6, h7)
        
        # Concaténer les valeurs de hachage finales
        return struct.pack('>IIIIIIII', h0, h1, h2, h3, h4, h5, h6, h7)

    def hexdigest(self) -> str:
        """
        Calcule le digest SHA-256 final en hexadécimal.
        
        Returns:
            Hash SHA-256 en hexadécimal (64 caractères)
        """
        return self.digest().hex()

    def update(self, data: Buffer) -> None:
        """
        Met à jour le hash avec de nouvelles données.
        
        Args:
            data: Données à ajouter
        """
        # Convertir en bytes
        data_bytes = bytes(data)
        # Mettre à jour les données
        self._data = self._data + data_bytes
        # Ajouter aux données restantes
        self._remaining_data = self._remaining_data + data_bytes
        # Traiter les blocs complets
        self._process_complete_blocks()


class SHA256:
    _string: bytes
    _usedforsecurity: bool
    _hash: Hash

    def __init__(self, string: Buffer = b"", *, usedforsecurity: bool = True) -> None:
        self._string = bytes(string)
        self._usedforsecurity = usedforsecurity
        self._hash = Hash(self._string)

    @property
    def value(self) -> Hash:
        return self._hash.copy()

    def update(self, data: Buffer) -> None:
        """
        Update the hash object with the bytes in data.
        """
        data_bytes = bytes(data)
        self._string = self._string + data_bytes
        self._hash.update(data_bytes)

    def digest(self) -> bytes:
        """
        Return the digest of the bytes passed to the update() method so far.
        """
        return self._hash.digest()

    def hexdigest(self) -> str:
        """
        Return the digest as a string of hexadecimal digits.
        """
        return self._hash.hexdigest()

    def copy(self) -> 'SHA256':
        """
        Return a copy of the hash object.
        """
        new_sha = SHA256(self._string, usedforsecurity=self._usedforsecurity)
        new_sha._hash = self._hash.copy()
        return new_sha

    @property
    def digest_size(self) -> int:
        """
        Return the digest size of the hash algorithm in bytes.
        """
        return self._hash.digest_size

    @property
    def block_size(self) -> int:
        """
        Return the internal block size of the hash algorithm in bytes.
        """
        return self._hash.block_size

    @property
    def name(self) -> str:
        """
        Return the canonical name of the hash algorithm.
        """
        return self._hash.name



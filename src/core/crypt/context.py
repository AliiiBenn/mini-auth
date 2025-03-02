import os
import hashlib
import hmac
import base64
import secrets
from typing import Optional, Dict, List, Callable, Any, Union, cast
from datetime import datetime, timedelta, timezone

from core.crypt.sha import SHA256

# Constantes pour les algorithmes supportés
SUPPORTED_HASH_ALGORITHMS = ["bcrypt", "argon2", "pbkdf2_sha256", "sha256", "sha512"]
DEFAULT_ALGORITHM = "bcrypt"


class CryptContext:
    """
    Contexte de cryptographie personnalisé qui gère différentes méthodes de hachage
    et permet de migrer entre elles.
    """

    def __init__(
        self,
        schemes: Optional[List[str]] = None,
        default_scheme: str = DEFAULT_ALGORITHM,
        deprecated: Optional[Union[str, List[str]]] = None,
        rounds: Optional[Dict[str, int]] = None,
    ):
        """
        Initialise le contexte de cryptographie.
        
        Args:
            schemes: Liste des algorithmes de hachage supportés
            default_scheme: Algorithme par défaut à utiliser
            deprecated: Algorithmes dépréciés (à migrer)
            rounds: Nombre d'itérations pour chaque algorithme
        """
        self.schemes = schemes or [DEFAULT_ALGORITHM]
        self.default_scheme = default_scheme
        
        if default_scheme not in self.schemes:
            raise ValueError(f"L'algorithme par défaut '{default_scheme}' n'est pas dans la liste des algorithmes supportés")
        
        # Vérifier que tous les algorithmes sont supportés
        for scheme in self.schemes:
            if scheme not in SUPPORTED_HASH_ALGORITHMS:
                raise ValueError(f"Algorithme non supporté: {scheme}")
        
        # Gérer les algorithmes dépréciés
        if deprecated == "auto":
            # Tous les algorithmes sauf celui par défaut sont dépréciés
            self.deprecated = [s for s in self.schemes if s != default_scheme]
        elif isinstance(deprecated, list):
            self.deprecated = deprecated
        elif isinstance(deprecated, str):
            self.deprecated = [deprecated]
        else:
            self.deprecated = []
        
        # Nombre d'itérations par défaut pour chaque algorithme
        self.rounds = {
            "bcrypt": 12,
            "argon2": 3,
            "pbkdf2_sha256": 100000,
            "sha256": 1,
            "sha512": 1,
        }
        
        # Mettre à jour avec les valeurs personnalisées
        if rounds:
            self.rounds.update(rounds)
        
        # Fonctions de hachage pour chaque algorithme
        self._hash_funcs = {
            "bcrypt": self._hash_bcrypt,
            "argon2": self._hash_argon2,
            "pbkdf2_sha256": self._hash_pbkdf2_sha256,
            "sha256": self._hash_sha256,
            "sha512": self._hash_sha512,
        }
        
        # Fonctions de vérification pour chaque algorithme
        self._verify_funcs = {
            "bcrypt": self._verify_bcrypt,
            "argon2": self._verify_argon2,
            "pbkdf2_sha256": self._verify_pbkdf2_sha256,
            "sha256": self._verify_sha256,
            "sha512": self._verify_sha512,
        }

    def hash(self, password: str) -> str:
        """
        Hache un mot de passe avec l'algorithme par défaut.
        
        Args:
            password: Mot de passe à hacher
            
        Returns:
            Mot de passe haché avec identifiant d'algorithme
        """
        return self._hash_with_scheme(password, self.default_scheme)

    def verify(self, password: str, hash_value: str) -> bool:
        """
        Vérifie si un mot de passe correspond à un hash.
        
        Args:
            password: Mot de passe à vérifier
            hash_value: Hash à comparer
            
        Returns:
            True si le mot de passe correspond, False sinon
        """
        # Extraire l'algorithme du hash
        if "$" not in hash_value:
            return False
        
        scheme = hash_value.split("$")[1]
        
        if scheme not in self.schemes:
            return False
        
        verify_func = self._verify_funcs.get(scheme)
        if not verify_func:
            return False
        
        return verify_func(password, hash_value)

    def needs_update(self, hash_value: str) -> bool:
        """
        Vérifie si un hash doit être mis à jour.
        
        Args:
            hash_value: Hash à vérifier
            
        Returns:
            True si le hash doit être mis à jour, False sinon
        """
        if "$" not in hash_value:
            return True
        
        scheme = hash_value.split("$")[1]
        
        # Si l'algorithme est déprécié, il faut mettre à jour
        if scheme in self.deprecated:
            return True
        
        # Si ce n'est pas l'algorithme par défaut, il faut mettre à jour
        if scheme != self.default_scheme:
            return True
        
        # Vérifier le nombre d'itérations pour certains algorithmes
        if scheme in ["bcrypt", "pbkdf2_sha256"]:
            try:
                current_rounds = int(hash_value.split("$")[2])
                if current_rounds < self.rounds[scheme]:
                    return True
            except (IndexError, ValueError):
                return True
        
        return False

    def _hash_with_scheme(self, password: str, scheme: str) -> str:
        """
        Hache un mot de passe avec un algorithme spécifique.
        
        Args:
            password: Mot de passe à hacher
            scheme: Algorithme à utiliser
            
        Returns:
            Mot de passe haché
        """
        hash_func = self._hash_funcs.get(scheme)
        if not hash_func:
            raise ValueError(f"Algorithme non supporté: {scheme}")
        
        return hash_func(password)

    # Implémentations des fonctions de hachage
    
    def _hash_bcrypt(self, password: str) -> str:
        """Hache un mot de passe avec bcrypt."""
        try:
            import bcrypt
            
            rounds = self.rounds["bcrypt"]
            salt = bcrypt.gensalt(rounds=rounds)
            hashed = bcrypt.hashpw(password.encode(), salt)
            return f"$bcrypt${rounds}${hashed.decode()}"
        except ImportError:
            raise ImportError("Le module bcrypt n'est pas installé. Installez-le avec 'pip install bcrypt'.")

    def _hash_argon2(self, password: str) -> str:
        """Hache un mot de passe avec argon2."""
        try:
            # Import conditionnel pour éviter l'erreur de linter
            argon2 = __import__('argon2')
            PasswordHasher = argon2.PasswordHasher
            
            time_cost = self.rounds["argon2"]
            ph = PasswordHasher(time_cost=time_cost)
            hashed = ph.hash(password)
            return f"$argon2${time_cost}${hashed}"
        except ImportError:
            raise ImportError("Le module argon2-cffi n'est pas installé. Installez-le avec 'pip install argon2-cffi'.")

    def _hash_pbkdf2_sha256(self, password: str) -> str:
        """Hache un mot de passe avec PBKDF2-SHA256."""
        iterations = self.rounds["pbkdf2_sha256"]
        salt = secrets.token_bytes(16)
        salt_b64 = base64.b64encode(salt).decode()
        
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
        dk_b64 = base64.b64encode(dk).decode()
        
        return f"$pbkdf2_sha256${iterations}${salt_b64}${dk_b64}"

    def _hash_sha256(self, password: str) -> str:
        """Hache un mot de passe avec SHA-256 (non recommandé pour les mots de passe)."""
        salt = secrets.token_hex(16)
        hashed = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"$sha256$1${salt}${hashed}"

    def _hash_sha512(self, password: str) -> str:
        """Hache un mot de passe avec SHA-512 (non recommandé pour les mots de passe)."""
        salt = secrets.token_hex(16)
        # Convertir la chaîne en bytes avant de la passer à SHA256
        hashed = SHA256((password + salt).encode()).hexdigest()
        return f"$sha512$1${salt}${hashed}"

    # Implémentations des fonctions de vérification
    
    def _verify_bcrypt(self, password: str, hash_value: str) -> bool:
        """Vérifie un mot de passe avec bcrypt."""
        try:
            import bcrypt
            
            # Format: $bcrypt$rounds$hash
            parts = hash_value.split("$")
            if len(parts) < 4:
                return False
            
            # Extraire le hash bcrypt
            bcrypt_hash = "$".join(parts[3:])
            
            return bcrypt.checkpw(password.encode(), bcrypt_hash.encode())
        except ImportError:
            raise ImportError("Le module bcrypt n'est pas installé. Installez-le avec 'pip install bcrypt'.")

    def _verify_argon2(self, password: str, hash_value: str) -> bool:
        """Vérifie un mot de passe avec argon2."""
        try:
            # Import conditionnel pour éviter l'erreur de linter
            argon2 = __import__('argon2')
            PasswordHasher = argon2.PasswordHasher
            VerifyMismatchError = argon2.exceptions.VerifyMismatchError
            
            # Format: $argon2$time_cost$hash
            parts = hash_value.split("$")
            if len(parts) < 4:
                return False
            
            # Extraire le hash argon2
            argon2_hash = "$".join(parts[3:])
            
            ph = PasswordHasher()
            try:
                return ph.verify(argon2_hash, password)
            except VerifyMismatchError:
                return False
        except ImportError:
            raise ImportError("Le module argon2-cffi n'est pas installé. Installez-le avec 'pip install argon2-cffi'.")

    def _verify_pbkdf2_sha256(self, password: str, hash_value: str) -> bool:
        """Vérifie un mot de passe avec PBKDF2-SHA256."""
        # Format: $pbkdf2_sha256$iterations$salt$hash
        parts = hash_value.split("$")
        if len(parts) != 5:
            return False
        
        try:
            iterations = int(parts[2])
            salt = base64.b64decode(parts[3])
            stored_hash = base64.b64decode(parts[4])
            
            dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
            return hmac.compare_digest(dk, stored_hash)
        except (ValueError, IndexError):
            return False

    def _verify_sha256(self, password: str, hash_value: str) -> bool:
        """Vérifie un mot de passe avec SHA-256."""
        # Format: $sha256$1$salt$hash
        parts = hash_value.split("$")
        if len(parts) != 5:
            return False
        
        salt = parts[3]
        stored_hash = parts[4]
        
        computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return hmac.compare_digest(computed_hash, stored_hash)

    def _verify_sha512(self, password: str, hash_value: str) -> bool:
        """Vérifie un mot de passe avec SHA-512."""
        # Format: $sha512$1$salt$hash
        parts = hash_value.split("$")
        if len(parts) != 5:
            return False
        
        salt = parts[3]
        stored_hash = parts[4]
        
        computed_hash = hashlib.sha512((password + salt).encode()).hexdigest()
        return hmac.compare_digest(computed_hash, stored_hash)


# Exemple d'utilisation
if __name__ == "__main__":
    # Créer un contexte avec bcrypt comme algorithme par défaut
    context = CryptContext(
        schemes=["bcrypt", "pbkdf2_sha256", "sha256"],
        default_scheme="bcrypt",
        deprecated=["sha256"],
        rounds={"bcrypt": 12, "pbkdf2_sha256": 150000}
    )
    
    # Hacher un mot de passe
    hashed = context.hash("mot_de_passe_secret")
    print(f"Hashed: {hashed}")
    
    # Vérifier un mot de passe
    is_valid = context.verify("mot_de_passe_secret", hashed)
    print(f"Valid: {is_valid}")
    
    # Vérifier si le hash doit être mis à jour
    needs_update = context.needs_update(hashed)
    print(f"Needs update: {needs_update}")

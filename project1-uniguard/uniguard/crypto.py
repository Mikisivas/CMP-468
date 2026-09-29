"""Key management and authenticated encryption.

Design:
  * A passphrase is stretched with scrypt (memory-hard, slows brute force).
  * HKDF splits the master key into two independent keys:
      - enc_key for AES-256-GCM (confidentiality + integrity of every blob)
      - mac_key for HMAC-SHA256 (object names that leak nothing about content)
  * Each encryption uses a fresh random 96-bit nonce.
  * Associated data (AAD) binds a ciphertext to its name, so an attacker
    cannot swap one encrypted object for another without detection.
"""

import hashlib
import hmac
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

NONCE_SIZE = 12
KEY_CHECK_PLAINTEXT = b"UniGuard key check v1"

# scrypt cost. n=2**15 takes roughly 100 ms and 32 MiB per guess.
SCRYPT_N = 2**15
SCRYPT_R = 8
SCRYPT_P = 1


class IntegrityError(Exception):
    """Raised when data fails authentication (tampered, corrupted or wrong key)."""


def _hkdf(master: bytes, info: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(master)


def derive_master_key(passphrase: str, salt: bytes, n: int = SCRYPT_N) -> bytes:
    kdf = Scrypt(salt=salt, length=32, n=n, r=SCRYPT_R, p=SCRYPT_P)
    return kdf.derive(passphrase.encode("utf-8"))


class KeyRing:
    def __init__(self, master: bytes):
        self._aes = AESGCM(_hkdf(master, b"uniguard-encryption"))
        self._mac_key = _hkdf(master, b"uniguard-object-id")

    @classmethod
    def from_passphrase(cls, passphrase: str, salt: bytes, n: int = SCRYPT_N) -> "KeyRing":
        return cls(derive_master_key(passphrase, salt, n))

    def encrypt(self, plaintext: bytes, aad: bytes = b"") -> bytes:
        nonce = os.urandom(NONCE_SIZE)
        return nonce + self._aes.encrypt(nonce, plaintext, aad)

    def decrypt(self, blob: bytes, aad: bytes = b"") -> bytes:
        if len(blob) < NONCE_SIZE + 16:
            raise IntegrityError("ciphertext too short")
        nonce, ct = blob[:NONCE_SIZE], blob[NONCE_SIZE:]
        try:
            return self._aes.decrypt(nonce, ct, aad)
        except InvalidTag as exc:
            raise IntegrityError("authentication failed: data was modified or the key is wrong") from exc

    def object_id(self, data: bytes) -> str:
        """Keyed content address. Equal chunks deduplicate, but names reveal nothing."""
        return hmac.new(self._mac_key, data, hashlib.sha256).hexdigest()

    def mac(self, data: bytes) -> str:
        return hmac.new(self._mac_key, b"mac:" + data, hashlib.sha256).hexdigest()

    def verify_mac(self, data: bytes, tag: str) -> bool:
        return hmac.compare_digest(self.mac(data), tag)


def sha256_file(path, bufsize: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(bufsize):
            h.update(chunk)
    return h.hexdigest()

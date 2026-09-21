import logging

logger = logging.getLogger(__name__)
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import unpad


class CryptoManager:
    """handle all crypto related functions"""
    # --------------constant--------------
    AES_LEN = 32
    AES_BLOCK_SIZE = 16



    @staticmethod
    def generate_aes_key() -> bytes:
        """generate aes (256 bit) key"""
        return get_random_bytes(CryptoManager.AES_LEN)

    @staticmethod
    def encrypt_aes_key(public_key: bytes, aes_key: bytes) -> bytes | None:
        """encrypt aes key using the rsa public key"""
        try:
            rsa_key = RSA.importKey(public_key)
            cipher_rsa = PKCS1_OAEP.new(rsa_key)
            return cipher_rsa.encrypt(aes_key)
        except ValueError as ve:
            logger.error(f"failed to encrypt aes key: {ve}")
            return None
        except Exception as e: # noqa: BLE001
            logger.error(f"unexpected error: {e}")
            return None

    @staticmethod
    def decrypt_aes_key(aes_key: bytes, encrypted_data: bytes) -> bytes | None:
        """decrypt file content using the AES key"""
        try:

            iv = bytes(CryptoManager.AES_BLOCK_SIZE)

            aes_code = AES.new(aes_key, AES.MODE_CBC, iv)
            # decrypt all the data
            decrypted_padded = aes_code.decrypt(encrypted_data)
            # remove extra padding
            decrypted_data = unpad(decrypted_padded, AES.block_size)

            return decrypted_data
        except ValueError as ve:
            logger.error(f"failed to decrypt file: {ve}")
            return None
        except Exception as e: # noqa: BLE001
            logger.error(f"unexpected error during file decryption: {e}")
            return None

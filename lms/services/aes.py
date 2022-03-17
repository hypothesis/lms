from typing import Union

from Cryptodome import Random
from Cryptodome.Cipher import AES


class AESService:
    """
    Service to encrypt/decrypt strings with AES CFB.

    CFB uses an "initialization vector", IV  which needs to:
        - Have the same value in encrypt and decrypt
        - Be a random value.

    For those reason IV can't be an application setting (unlike secret) and needs to be stored separately.
    """

    def __init__(self, secret):
        self.secret = secret

    def decrypt(self, aes_iv, encrypted) -> bytes:
        cipher = AES.new(self.secret, AES.MODE_CFB, aes_iv)
        return cipher.decrypt(encrypted)

    def encrypt(self, aes_iv, plain_text: Union[str, bytes]):
        if isinstance(plain_text, str):
            plain_text = plain_text.encode("utf-8")

        return AES.new(self.secret, AES.MODE_CFB, aes_iv).encrypt(plain_text)

    @staticmethod
    def build_iv():
        """
        Return a random initialization vector (IV).

        The same value must be used for encryption and decryption but not reused for different messages.
        """
        # Using the cryptographic secure Cryptodome.Random instead of the stlib random package.
        return Random.new().read(AES.block_size)


def factory(_context, request):
    return AESService(secret=request.registry.settings["aes_secret"])

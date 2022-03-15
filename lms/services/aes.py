from typing import Union

from Cryptodome import Random
from Cryptodome.Cipher import AES


class AESService:
    def __init__(self, secret):
        self.secret = secret

    def decrypt(self, aes_iv, encrypted):
        cipher = AES.new(self.secret, AES.MODE_CFB, aes_iv)
        return cipher.decrypt(encrypted)

    def encrypt(self, aes_iv, plain_text: Union[str, bytes]):
        if isinstance(plain_text, str):
            plain_text = plain_text.encode("utf-8")

        return AES.new(self.secret, AES.MODE_CFB, aes_iv).encrypt(plain_text)

    @staticmethod
    def build_iv():
        return Random.new().read(AES.block_size)


def factory(_context, request):
    return AESService(secret=request.registry.settings["aes_secret"])

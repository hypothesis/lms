from typing import Union

from Cryptodome import Random
from Cryptodome.Cipher import AES


def decrypt(secret, iv, encrypted):
    cipher = AES.new(secret, AES.MODE_CFB, iv)
    return cipher.decrypt(encrypted)


def encrypt(secret, iv, plain_text: Union[str, bytes]):
    if isinstance(plain_text, str):
        plain_text = plain_text.encode("utf-8")

    return AES.new(secret, AES.MODE_CFB, iv).encrypt(plain_text)


def build_iv():
    return Random.new().read(AES.block_size)

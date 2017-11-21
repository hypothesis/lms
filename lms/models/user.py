import hashlib
import os

import binascii
import sqlalchemy as sa
from sqlalchemy import Column, Integer, Text
from lms.db import BASE


class User(BASE):
    """ The SQLAlchemy declarative model class for a User object. """
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text)
    salt = Column(Text)

    def set_password(self, pw):
        self.password_hash = self._hash_it(pw)

    def check_password(self, candidate):
        candidate_hash = self._hash_it(candidate)
        return self.password_hash == candidate_hash

    def _hash_it(self, password):
        salt = os.urandom(8)
        pw_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf8'),
            salt,
            1000000)
        return binascii.hexlify(pw_hash)

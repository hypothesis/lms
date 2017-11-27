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

    # hash_iterations = 1000000
    #
    # def set_new_password_and_salt(self, pw):
    #     self.salt = os.urandom(8)
    #     self.password_hash = self.get_password_hash(pw, self.salt)
    #
    # def check_password(self, candidate, salt):
    #     candidate_hash = self.get_password_hash(candidate, salt)
    #     return self.password_hash == candidate_hash
    #
    # def get_password_hash(self, password, salt):
    #     pw_hash = hashlib.pbkdf2_hmac(
    #         'sha256',
    #         password.encode('utf8'),
    #         salt,
    #         self.hash_iterations)
    #     return binascii.hexlify(pw_hash)

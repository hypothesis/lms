"""
A CLI command for inserting standard dev data into the DB.

Usage:

    devdata conf/development.ini
"""
import base64
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

from pyramid.paster import bootstrap

import lms
from lms import models


__all__ = ["devdata"]


class DevDataFactory:
    """Factory class for inserting standard dev data into the DB."""

    def __init__(self, request, devdata_):
        self.db = request.db
        self.tm = request.tm
        self.devdata = devdata_

    def create_all(self):
        """
        Create all the standard dev data in the DB.

        Create standard dev data objects (users, groups, etc) if they don't
        exist. If objects with the same identifier already exist in the DB
        (e.g. a user with the same name as a standard dev data user, or a group
        with the same pubid, etc) but those objects have different values for
        some fields, then overwrite those incorrect values with the standard
        values.
        """
        for data_dict in self.devdata:
            type_ = data_dict.pop("type")

            if type_ == "application_instance":
                self.upsert_application_instance(data_dict)
            else:
                raise RuntimeError(f"Unrecognized type: {type_}")

        self.tm.commit()

    def upsert_application_instance(self, data):
        application_instance = (
            self.db.query(models.ApplicationInstance)
            .filter_by(consumer_key=data["consumer_key"])
            .one_or_none()
        )

        if not application_instance:
            application_instance = models.ApplicationInstance()
            self.db.add(application_instance)

        base64_encoded_developer_secret_bytes = data.pop(
            "base64_encoded_developer_secret_bytes", None
        )
        base64_encoded_aes_cipher_iv_bytes = data.pop(
            "base64_encoded_aes_cipher_iv_bytes", None
        )
        if base64_encoded_developer_secret_bytes:
            assert base64_encoded_aes_cipher_iv_bytes

            application_instance.developer_secret = base64.b64decode(
                base64_encoded_developer_secret_bytes
            )
            application_instance.aes_cipher_iv = base64.b64decode(
                base64_encoded_aes_cipher_iv_bytes
            )

        self.setattrs(application_instance, data)

    @staticmethod
    def setattrs(object_, attrs):
        for name, value in attrs.items():
            setattr(object_, name, value)


def devdata():
    with bootstrap(sys.argv[1]) as env:
        with tempfile.TemporaryDirectory() as tmpdirname:
            # The directory that we'll clone the devdata git repo into.
            git_dir = os.path.join(tmpdirname, "devdata")

            subprocess.check_call(
                ["git", "clone", "git@github.com:hypothesis/devdata.git", git_dir]
            )

            # Copy devdata env file into place.
            shutil.copyfile(
                os.path.join(git_dir, "lms", "devdata.env"),
                os.path.join(pathlib.Path(lms.__file__).parent.parent, ".devdata.env"),
            )

            DevDataFactory(
                env["request"],
                json.loads(
                    open(os.path.join(git_dir, "lms", "devdata.json"), "r").read()
                ),
            ).create_all()

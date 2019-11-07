import json
import os

from pkg_resources import resource_stream


class TestBaseClass:
    """A base class for handy test fixture functions"""

    FIXTURE_DIR = "functional/fixtures"

    @classmethod
    def json_fixture(cls, filename):
        path = os.path.join(cls.FIXTURE_DIR, filename)
        with resource_stream("tests", path) as handle:
            return json.load(handle)

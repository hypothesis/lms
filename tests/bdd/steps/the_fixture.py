"""Load and manipulate fixtures."""

import os.path

from pkg_resources import resource_filename


class TheFixture:
    context_key = "the_fixture"

    def __init__(self, **kwargs):
        self.base_dir = None
        self.fixtures = {}

    def set_base_dir(self, base_dir):
        base_dir = base_dir.lstrip("/")
        path = os.path.join("bdd/fixtures", base_dir)

        self.base_dir = resource_filename("tests", path)

        if not os.path.isdir(self.base_dir):
            raise EnvironmentError(f"Cannot find fixture dir: {self.base_dir}")

    def set_fixture(self, name, value):
        self.fixtures[name] = value

        return value

    def get_fixture(self, name):
        return self.fixtures[name]

    def load_ini(self, filename, fixture_name):
        values = {}
        with open(self.get_path(filename)) as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                key, value = line.split("=", 1)
                values[key] = value

        return self.set_fixture(fixture_name, values)

    def get_path(self, filename):
        return os.path.join(self.base_dir, filename)

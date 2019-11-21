"""
    Given fixtures are located in "fixtures/lti_certification_1_1"
    Given I load the fixture "wat.json" as "params"
    And I set the fixture "params" value "resource_link_id" to "*MISSING*"

"""
import json
import os.path

from behave import step
from pkg_resources import resource_filename


class TheFixture:
    MISSING = "*MISSING*"
    NONE = "*NONE*"

    def __init__(self):
        self.base_dir = None
        self.fixtures = {}

    def set_base_dir(self, base_dir):
        base_dir = base_dir.lstrip("/")
        path = os.path.join("bdd/fixtures", base_dir)

        self.base_dir = resource_filename("tests", path)

    def teardown(self):
        self.fixtures = {}

    def set_fixture(self, name, value):
        self.fixtures[name] = value

    def get_fixture(self, name):
        return self.fixtures[name]

    def load_ini(self, filename, fixture_name):
        values = {}
        with open(self._get_path(filename)) as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                key, value = line.split("=", 1)
                values[key] = value

        self.set_fixture(fixture_name, values)

    def load_json(self, filename, fixture_name):
        with open(self._get_path(filename)) as handle:
            self.set_fixture(fixture_name, json.load(handle))

    def _get_path(self, filename):
        return os.path.join(self.base_dir, filename)

    @classmethod
    def register(cls, context):
        context.the_fixture = TheFixture()


@step("fixtures are located in '{location}'")
def fixture_location(context, location):
    context.the_fixture.set_base_dir(location)


@step("I define the fixture '{fixture_name}' to be '{data}'")
def define_fixture(context, fixture_name, data):
    if data[0] in {"[", "{", '"'}:
        data = json.loads(data)

    context.the_fixture.set_fixture(fixture_name, data)


@step("I load the fixture '{fixture_file}.json' as '{fixture_name}'")
def load_json_fixture(context, fixture_file, fixture_name):
    context.the_fixture.load_json(fixture_file + ".json", fixture_name)


@step("I load the fixture '{fixture_file}.ini' as '{fixture_name}'")
def load_ini_fixture(context, fixture_file, fixture_name):
    context.the_fixture.load_ini(fixture_file + ".ini", fixture_name)


@step("I set the '{fixture_name}' fixture value '{key}' to '{value}'")
def set_value(context, fixture_name, key, value):
    fixture = context.the_fixture.get_fixture(fixture_name)

    if value == TheFixture.MISSING:
        fixture.pop(key, None)
        return

    fixture[value] = None if value == TheFixture.NONE else value


@step("I dump the fixture '{fixture_name}'")
def dump_fixture(context, fixture_name):
    fixture = context.the_fixture.get_fixture(fixture_name)

    print(f"Fixture '{fixture_name}'")
    print(json.dumps(fixture, indent=4))

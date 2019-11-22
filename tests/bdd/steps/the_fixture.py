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

    def load_json(self, filename, fixture_name):
        with open(self.get_path(filename)) as handle:
            self.set_fixture(fixture_name, json.load(handle))

    def get_path(self, filename):
        return os.path.join(self.base_dir, filename)

    @classmethod
    def register(cls, context):
        context.the_fixture = TheFixture()


@step("fixtures are located in '{location}'")
def fixture_location(context, location):
    context.the_fixture.set_base_dir(location)


@step("I load the fixture '{fixture_file}.json' as '{fixture_name}'")
def load_json_fixture(context, fixture_file, fixture_name):
    context.the_fixture.load_json(fixture_file + ".json", fixture_name)


@step("I load the fixture '{fixture_file}.ini' as '{fixture_name}'")
def load_ini_fixture(context, fixture_file, fixture_name):
    context.the_fixture.load_ini(fixture_file + ".ini", fixture_name)


@step("I define the fixture '{fixture_name}' to be '{data}'")
def define_fixture(context, fixture_name, data):
    if data[0] in {"[", "{", '"'}:
        data = json.loads(data)

    context.the_fixture.set_fixture(fixture_name, data)


@step("I set the fixture '{fixture_name}' key '{key}' to '{value}'")
def set_fixture_value(context, fixture_name, key, value):
    fixture = context.the_fixture.get_fixture(fixture_name)

    if value == TheFixture.MISSING:
        fixture.pop(key, None)
        return

    fixture[key] = None if value == TheFixture.NONE else value


@step("I update the fixture '{fixture_name}' with")
def update_fixture_from_table(context, fixture_name):
    for row in context.table:
        set_fixture_value(context, fixture_name, row[0].strip(), row[1].strip())


@step("I update the fixture '{fixture_name}' from fixture '{other_fixture}'")
def update_fixture_from_fixture(context, fixture_name, other_fixture):
    the_fixture = context.the_fixture
    the_fixture.get_fixture(fixture_name).update(the_fixture.get_fixture(other_fixture))


@step("the fixture '{fixture_name}' key '{key}' is the value")
def set_fixture_key_to_the_value(context, fixture_name, key):
    context.the_value = context.the_fixture.get_fixture(fixture_name)[key]


@step("I dump the fixture '{fixture_name}'")
def dump_fixture(context, fixture_name):
    fixture = context.the_fixture.get_fixture(fixture_name)

    print(f"Fixture '{fixture_name}'")
    print(json.dumps(fixture, indent=4))

"""Load and manipulate fixtures."""

import json
import os.path

import importlib_resources
from behave import given, step, then  # pylint:disable=no-name-in-module

from tests.bdd.step_context import StepContext


class TheFixture(StepContext):
    MISSING = "*MISSING*"
    NONE = "*NONE*"
    context_key = "the_fixture"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_dir = None
        self.fixtures = {}

    def set_base_dir(self, base_dir):
        base_dir = base_dir.lstrip("/")

        self.base_dir = str(
            importlib_resources.files("tests") / "bdd/fixtures" / base_dir
        )

        if not os.path.isdir(self.base_dir):
            raise EnvironmentError(f"Cannot find fixture dir: {self.base_dir}")

    def set_fixture(self, name, value):
        self.fixtures[name] = value

        return value

    def set_fixture_value(self, name, key, value):
        fixture = self.get_fixture(name)

        if value == self.MISSING:
            fixture.pop(key, None)
            return

        fixture[key] = None if value == self.NONE else value

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

    def do_teardown(self):
        self.fixtures = {}


@given("fixtures are located in '{location}'")
def fixture_location(context, location):
    context.the_fixture.set_base_dir(location)


@given("I load the fixture '{fixture_file}.ini' as '{fixture_name}'")
def load_ini_fixture(context, fixture_file, fixture_name):
    context.the_fixture.load_ini(fixture_file + ".ini", fixture_name)


@given("I set the fixture '{fixture_name}' key '{key}' to '{value}'")
def set_fixture_value(context, fixture_name, key, value):
    context.the_fixture.set_fixture_value(fixture_name, key, value)


@given("I update the fixture '{fixture_name}' with")
def update_fixture_from_table(context, fixture_name):
    for row in context.table:
        set_fixture_value(context, fixture_name, row[0].strip(), row[1].strip())


@given("I update the fixture '{fixture_name}' from fixture '{other_fixture}'")
def update_fixture_from_fixture(context, fixture_name, other_fixture):
    the_fixture = context.the_fixture
    the_fixture.get_fixture(fixture_name).update(the_fixture.get_fixture(other_fixture))


@then("the fixture '{fixture_name}' key '{key}' is the value")
def set_fixture_key_to_the_value(context, fixture_name, key):
    context.the_value = context.the_fixture.get_fixture(fixture_name)[key]


def diff_dicts(a, b, missing=KeyError):
    return {
        key: (a.get(key, missing), b.get(key, missing))
        for key in dict(set(a.items()) ^ set(b.items())).keys()
    }


@then("the fixture '{fixture_name}' matches the fixture '{other_fixture}'")
def compare_fixtures(context, fixture_name, other_fixture):
    diff = diff_dicts(
        context.the_fixture.get_fixture(fixture_name),
        context.the_fixture.get_fixture(other_fixture),
        missing=TheFixture.MISSING,
    )

    if not diff:
        return

    for key, (value_found, value_expected) in diff.items():
        print(f"Key {key} is different. Found {value_found} expected {value_expected}")

    assert diff == {}, "The fixtures differ"


@step("I dump the fixture '{fixture_name}'")
def dump_fixture(context, fixture_name):
    fixture = context.the_fixture.get_fixture(fixture_name)

    print(f"Fixture '{fixture_name}'")
    print(json.dumps(fixture, indent=4))

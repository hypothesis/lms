"""Entry point and hooks for behave."""

from pkg_resources import resource_filename

from lms.app import create_app
from tests.bdd.higher_order_gherkin import Injector
from tests.bdd.step_context import StepContextManager
from tests.bdd.steps.lms_db import TEST_DATABASE_URL
from tests.conftest import TEST_SETTINGS

TEST_SETTINGS["sqlalchemy.url"] = TEST_DATABASE_URL


# Create the compiled step file before steps are read
Injector.create_step_file(
    source_dir=resource_filename("tests", "bdd/steps/feature_steps/"),
    target_file=resource_filename("tests", "bdd/steps/_compiled_feature_steps.py"),
)


def before_all(context):
    StepContextManager.before_all(context, app=create_app(None, **TEST_SETTINGS))


def before_scenario(context, _scenario):
    StepContextManager.before_scenario(context)


def after_scenario(context, _scenario):
    StepContextManager.after_scenario(context)

from lms.app import create_app
from tests.bdd.higher_order_gherkin import Injector
from tests.bdd.steps import *
from tests.conftest import TEST_SETTINGS

TEST_SETTINGS["session_cookie_secret"] = "notasecret"


def compile_feature_steps():
    Injector.create_step_file(
        source_dir=resource_filename("tests", "bdd/steps/feature_steps/"),
        target_file=resource_filename("tests", "bdd/steps/_compiled_feature_steps.py"),
    )


def before_all(context):
    compile_feature_steps()

    arguments = {"app": create_app(None, **TEST_SETTINGS)}

    for step_context in STEP_CONTEXTS:
        if step_context.singleton:
            step_context.register(context, **arguments)


def before_scenario(context, scenario):
    for step_context in STEP_CONTEXTS:
        step_context.setup(context)


def after_scenario(context, scenario):
    for step_context in STEP_CONTEXTS:
        step_context.teardown(context)

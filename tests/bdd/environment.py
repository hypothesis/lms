"""Entry point and hooks for behave."""

from lms.app import create_app
from tests.bdd.step_context import StepContextManager
from tests.conftest import TEST_SETTINGS

TEST_SETTINGS["session_cookie_secret"] = "notasecret"


def before_all(context):
    # This will actually take effect the next time you run the tests, but it
    # still keeps you mostly up to date when developing
    StepContextManager.before_all(context, app=create_app(None, **TEST_SETTINGS))


def before_scenario(context, scenario):
    try:
        StepContextManager.before_scenario(context)
    except Exception as e:
        print('PUP', e)
        raise


def after_scenario(context, scenario):
    try:
        StepContextManager.after_scenario(context)
    except Exception as e:
        print('WUP', e)
        raise


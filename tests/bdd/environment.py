from lms.app import create_app
from tests.bdd.steps import LMSDBContext, OAuth1Context, TheApp, TheFixture, TheRequest
from tests.conftest import TEST_SETTINGS

TEST_SETTINGS["session_cookie_secret"] = "notasecret"


def before_all(context):
    LMSDBContext.register(context)

    TheApp.register(context, create_app(None, **TEST_SETTINGS))
    OAuth1Context.register(context)
    TheFixture.register(context)
    TheRequest.register(context)


def before_scenario(context, scenario):
    context.db.setup()


def after_scenario(context, scenario):
    context.db.teardown()
    context.the_fixture.teardown()

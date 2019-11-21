from lms.app import create_app
from tests.bdd.feature_steps import FeatureStepGenerator
from tests.bdd.steps import (
    LMSDBContext,
    OAuth1Context,
    TheApp,
    TheFixture,
    TheRequest,
    resource_filename,
)
from tests.conftest import TEST_SETTINGS

TEST_SETTINGS["session_cookie_secret"] = "notasecret"


def compile_feature_steps():
    FeatureStepGenerator.generate(
        source_dir=resource_filename("tests", "bdd/feature_steps/"),
        target_file=resource_filename("tests", "bdd/steps/_compiled_feature_steps.py"),
    )


def before_all(context):
    compile_feature_steps()

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

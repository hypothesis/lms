from tests.bdd.steps.lms_db import *
from tests.bdd.steps.oauth1 import *
from tests.bdd.steps.the_app import *
from tests.bdd.steps.the_fixture import *
from tests.bdd.steps.the_request import *
from tests.bdd.steps.the_response import *

STEP_CONTEXTS = {
    LMSDBContext,
    OAuth1Context,
    TheApp,
    TheFixture,
    TheRequest,
    TheURL,
    WebTestResponse,
}

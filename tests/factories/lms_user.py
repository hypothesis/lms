from factory import make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories.attributes import H_USERID, USER_ID

LMSUser = make_factory(
    models.LMSUser,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    lti_user_id=USER_ID,
    h_userid=H_USERID,
)

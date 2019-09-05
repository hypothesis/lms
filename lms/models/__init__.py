from lms.models.application_instance import ApplicationInstance
from lms.models.lis_result_sourcedid import LISResultSourcedId
from lms.models.lti_launches import LtiLaunches
from lms.models.module_item_configuration import ModuleItemConfiguration
from lms.models.oauth2_token import OAuth2Token


__all__ = (
    "ApplicationInstance",
    "LISResultSourcedId",
    "LtiLaunches",
    "ModuleItemConfiguration",
    "OAuth2Token",
)


def includeme(config):  # pylint: disable=unused-argument
    pass

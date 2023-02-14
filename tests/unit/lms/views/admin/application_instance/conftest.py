from unittest.mock import sentinel

import pytest

from tests import factories


@pytest.fixture
def with_lti_13_ai(application_instance, db_session):
    lti_registration = factories.LTIRegistration()
    # Get a valid ID for the registration
    db_session.flush()
    application_instance.lti_registration_id = lti_registration.id
    application_instance.deployment_id = "ID"


@pytest.fixture
def ai_from_matchdict(
    pyramid_request, application_instance_service, application_instance
):
    pyramid_request.matchdict["id_"] = sentinel.id_
    application_instance_service.get_by_id.return_value = application_instance

    return application_instance

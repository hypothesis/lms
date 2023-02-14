import pytest

from tests import factories


@pytest.fixture
def with_lti_13_ai(application_instance, db_session):
    lti_registration = factories.LTIRegistration()
    # Get a valid ID for the registration
    db_session.flush()
    application_instance.lti_registration_id = lti_registration.id
    application_instance.deployment_id = "ID"

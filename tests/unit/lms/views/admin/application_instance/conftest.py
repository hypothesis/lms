from unittest.mock import sentinel

import pytest


@pytest.fixture
def ai_from_matchdict(
    pyramid_request, application_instance_service, application_instance
):
    pyramid_request.matchdict["id_"] = sentinel.id_
    application_instance_service.get_by_id.return_value = application_instance

    return application_instance

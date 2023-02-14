from unittest.mock import sentinel

import pytest

from lms.validation import ValidationError
from lms.views.admin.application_instance.move_organization import (
    MoveOrgApplicationInstanceView,
)
from tests.matchers import temporary_redirect_to


@pytest.mark.usefixtures("application_instance_service")
class TestAdminApplicationInstanceViews:
    def test_move_application_instance_org(
        self, view, pyramid_request, ai_from_matchdict, application_instance_service
    ):
        pyramid_request.params["org_public_id"] = "PUBLIC_ID"

        response = view.move_application_instance_org()

        application_instance_service.update_application_instance.assert_called_once_with(
            ai_from_matchdict, organization_public_id="PUBLIC_ID"
        )
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instance", id_=ai_from_matchdict.id)
        )

    @pytest.mark.usefixtures("ai_from_matchdict")
    def test_move_application_instance_org_invalid_organization_id(
        self, view, pyramid_request, application_instance_service
    ):
        pyramid_request.params["org_public_id"] = "PUBLIC_ID"
        application_instance_service.update_application_instance.side_effect = (
            ValidationError(messages=sentinel.messages)
        )

        response = view.move_application_instance_org()

        assert pyramid_request.session.peek_flash("validation")
        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.instance",
                id_=application_instance_service.get_by_id.return_value.id,
            )
        )

    @pytest.fixture
    def view(self, pyramid_request):
        return MoveOrgApplicationInstanceView(pyramid_request)

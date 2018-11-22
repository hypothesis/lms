import pytest

from lms.views.module_item_configurations import create_module_item_configuration
from lms.models import ModuleItemConfiguration


class TestModuleItemConfiguration:
    def test_it_creates_a_module_item_configuration(self, authenticated_request):
        initial_count = authenticated_request.db.query(ModuleItemConfiguration).count()
        create_module_item_configuration(authenticated_request)
        new_count = authenticated_request.db.query(ModuleItemConfiguration).count()
        assert new_count == initial_count + 1

    def test_bad_jwt_fails_authentication(self, authenticated_request):
        initial_count = authenticated_request.db.query(ModuleItemConfiguration).count()
        authenticated_request.params["jwt_token"] = "wrongjwttoken"

        response = create_module_item_configuration(authenticated_request)

        new_count = authenticated_request.db.query(ModuleItemConfiguration).count()
        assert new_count == initial_count
        assert "Unauthenticated Request" in str(response.body)

    def test_missing_jwt_fails_authentication(self, authenticated_request):
        initial_count = authenticated_request.db.query(ModuleItemConfiguration).count()
        authenticated_request.params["jwt_token"] = "wrongjwttoken"
        authenticated_request.params.pop("jwt_token")

        response = create_module_item_configuration(authenticated_request)

        new_count = authenticated_request.db.query(ModuleItemConfiguration).count()
        assert new_count == initial_count
        assert "Unauthenticated Request" in str(response.body)

    def test_it_passes_the_right_via_url_to_the_template(
        self, authenticated_request, via_url
    ):
        template_context = create_module_item_configuration(authenticated_request)

        via_url.assert_called_once_with(
            authenticated_request, authenticated_request.params["document_url"]
        )
        assert template_context["via_url"] == via_url.return_value

    @pytest.fixture
    def authenticated_request(self, authenticated_request):
        authenticated_request.params[
            "document_url"
        ] = "https://www.example.com/document"
        authenticated_request.params["resource_link_id"] = "test_resource_link_id"
        return authenticated_request

    @pytest.fixture(autouse=True)
    def via_url(self, patch):
        return patch("lms.views.module_item_configurations.via_url")

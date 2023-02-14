import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.exc import IntegrityError

from lms.models.public_id import InvalidPublicId
from lms.views.admin.application_instance.create import CreateApplicationInstanceViews

REDIRECT_TO_NEW_AI = Any.instance_of(HTTPFound).with_attrs(
    {"location": Any.string.containing("/admin/instance/new")}
)


@pytest.mark.usefixtures("application_instance_service", "lti_registration_service")
class TestCreateApplicationInstanceViews:
    @pytest.mark.parametrize("lti_registration_id", ("123", "  123   "))
    def test_new_instance_start_v13(
        self, views, pyramid_request, lti_registration_service, lti_registration_id
    ):
        pyramid_request.params = {
            "lti_registration_id": lti_registration_id,
            "key_1": "value_1",
            "key_2": "value_2",
        }

        response = views.new_instance_start()

        lti_registration_service.get_by_id.assert_called_once_with("123")
        assert response == dict(
            pyramid_request.params,
            lti_registration=lti_registration_service.get_by_id.return_value,
        )

    def test_new_instance_start_v11(self, views, pyramid_request):
        pyramid_request.params["lti_registration_id"] = None

        response = views.new_instance_start()

        assert not response["lti_registration"]

    @pytest.mark.usefixtures("ai_new_params_v13")
    def test_new_instance_callback_v13(self, views, application_instance_service):
        application_instance_service.create_application_instance.return_value.id = 12345

        response = views.new_instance_callback()

        application_instance_service.create_application_instance.assert_called_once_with(
            name="NAME",
            lms_url="http://example.com",
            email="test@example.com",
            deployment_id="22222",
            developer_key="DEVELOPER_KEY",
            developer_secret="DEVELOPER_SECRET",
            organization_public_id="us.lms.org.ID",
            lti_registration_id=54321,
        )
        assert response == Any.instance_of(HTTPFound).with_attrs(
            {"location": Any.string.containing("/admin/instance/12345")}
        )

    @pytest.mark.usefixtures("ai_new_params_v11")
    def test_new_instance_callback_v11(self, views):
        response = views.new_instance_callback()

        assert response == Any.instance_of(HTTPFound).with_attrs(
            {"location": Any.string.containing("/admin/instance/")}
        )

    @pytest.mark.usefixtures("ai_new_params_v13")
    @pytest.mark.parametrize(
        "exception", (IntegrityError(Any(), Any(), Any()), InvalidPublicId)
    )
    def test_new_instance_callback_with_errors(
        self, views, application_instance_service, exception
    ):
        application_instance_service.create_application_instance.side_effect = exception

        response = views.new_instance_callback()

        assert response == REDIRECT_TO_NEW_AI

    _V11_NEW_AI_BAD_FIELDS = [
        ("lms_url", "not a url"),
        ("email", "not an email"),
        ("organization_public_id", None),
        ("name", None),
    ]

    @pytest.mark.parametrize(
        "param,bad_value", _V11_NEW_AI_BAD_FIELDS + [("deployment_id", None)]
    )
    def test_new_instance_callback_v13_required_fields(
        self, views, ai_new_params_v13, param, bad_value
    ):
        ai_new_params_v13[param] = bad_value

        response = views.new_instance_callback()

        assert response == REDIRECT_TO_NEW_AI

    @pytest.mark.parametrize("param,bad_value", _V11_NEW_AI_BAD_FIELDS)
    def test_new_instance_callback_v11_required_fields(
        self, views, ai_new_params_v11, param, bad_value
    ):
        ai_new_params_v11[param] = bad_value

        response = views.new_instance_callback()

        assert response == REDIRECT_TO_NEW_AI

    @pytest.fixture
    def ai_new_params_v13(self, ai_new_params_v11):
        ai_new_params_v11["deployment_id"] = "  22222  "
        ai_new_params_v11["lti_registration_id"] = "  54321 "
        return ai_new_params_v11

    @pytest.fixture
    def ai_new_params_v11(self, pyramid_request):
        params = {
            "name": "  NAME  ",
            "lms_url": "http://example.com",
            "email": "test@example.com",
            "developer_key": "DEVELOPER_KEY",
            "developer_secret": "DEVELOPER_SECRET",
            "organization_public_id": "   us.lms.org.ID   ",
        }
        pyramid_request.POST = pyramid_request.params = params
        return params

    @pytest.fixture
    def views(self, pyramid_request):
        return CreateApplicationInstanceViews(pyramid_request)

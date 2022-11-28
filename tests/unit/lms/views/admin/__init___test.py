import pytest

from lms.validation._base import PyramidRequestSchema, ValidationError
from lms.views.admin import EmptyStringInt, index, logged_out, notfound
from tests.matchers import temporary_redirect_to


def test_logged_out_redirects_to_login(pyramid_request):
    response = logged_out(pyramid_request)

    assert response.status_code == 302

    assert response == temporary_redirect_to(
        pyramid_request.route_url(
            "pyramid_googleauth.login", _query={"next": pyramid_request.url}
        )
    )


def test_not_found_view(pyramid_request):
    response = notfound(pyramid_request)

    assert response.status_code == 404


def test_index(pyramid_request):
    response = index(pyramid_request)

    assert response == temporary_redirect_to(
        pyramid_request.route_url("admin.instances")
    )


class TestEmptyStringInt:
    @pytest.mark.parametrize("value", ["1", "", "   "])
    def test_valid(self, pyramid_request, value, TestSchema):
        pyramid_request.POST["id"] = value

        assert TestSchema(pyramid_request).parse()

    @pytest.mark.parametrize("value", ["not a number"])
    def test_invalid(self, pyramid_request, value, TestSchema):
        pyramid_request.POST["id"] = value

        with pytest.raises(ValidationError):
            TestSchema(pyramid_request).parse()

    @pytest.fixture
    def TestSchema(self):
        class _TestSchema(PyramidRequestSchema):
            location = "form"

            id = EmptyStringInt()

        return _TestSchema

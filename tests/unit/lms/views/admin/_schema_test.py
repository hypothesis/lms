import pytest

from lms.validation._base import PyramidRequestSchema, ValidationError
from lms.views.admin._schemas import EmptyStringInt


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

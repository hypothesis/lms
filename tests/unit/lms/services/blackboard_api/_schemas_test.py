import pytest

from lms.services.blackboard_api._schemas import BlackboardListFilesSchema
from lms.validation._exceptions import ValidationError
from tests import factories


class TestBlackboardListFilesSchema:
    def test_valid(self, json_data):
        schema = BlackboardListFilesSchema(
            factories.requests.Response(json_data=json_data)
        )

        result = schema.parse()

        assert result == [
            {
                "id": "_7851_0",
                "updated_at": "2008-05-06T07:26:35.000z",
                "display_name": "File_0.pdf",
            },
            {
                "id": "_7851_1",
                "updated_at": "1983-05-26T02:37:23.000z",
                "display_name": "File_1.pdf",
            },
        ]

    def test_it_raises_if_results_is_missing(self, json_data, assert_raises):
        del json_data["results"]

        assert_raises()

    def test_it_raises_if_results_isnt_a_list(self, json_data, assert_raises):
        json_data["results"] = None

        assert_raises()

    @pytest.mark.parametrize("missing_field", ["id", "modified", "name"])
    def test_it_raises_if_a_required_field_is_missing(
        self, json_data, assert_raises, missing_field
    ):
        del json_data["results"][0][missing_field]

        assert_raises()

    @pytest.mark.parametrize("invalid_field", ["id", "modified", "name"])
    def test_it_raises_if_a_field_is_invalid(
        self, json_data, assert_raises, invalid_field
    ):
        json_data["results"][0][invalid_field] = 23

        assert_raises()

    @pytest.fixture
    def json_data(self):
        """Return the JSON body of a valid Blackboard Files API response."""
        return {
            "results": [
                {
                    "id": "_7851_0",
                    "modified": "2008-05-06T07:26:35.000z",
                    "name": "File_0.pdf",
                    "unknown_field": "this_should_be_excluded",
                },
                {
                    "id": "_7851_1",
                    "modified": "1983-05-26T02:37:23.000z",
                    "name": "File_1.pdf",
                },
            ]
        }

    @pytest.fixture
    def assert_raises(self, json_data):
        def assert_raises():
            """Assert that the schema raises when parsing json_data."""
            schema = BlackboardListFilesSchema(
                factories.requests.Response(json_data=json_data)
            )

            with pytest.raises(ValidationError):
                schema.parse()

        return assert_raises

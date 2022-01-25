import pytest

from lms.services.vitalsource._schemas import BookTOCSchema
from tests import factories


class TestBookTOCSchema:
    def test_valid(self, list_chapters_response):
        schema = BookTOCSchema(
            factories.requests.Response(json_data=list_chapters_response)
        )
        schema.context["book_id"] = "BOOK_ID"

        result = schema.parse()

        assert result == {
            "table_of_contents": [
                {
                    "title": "Chapter 1",
                    "cfi": "/cif_01",
                    "page": "1",
                    "url": "vitalsource://book/bookID/BOOK_ID/cfi//cif_01",
                },
                {
                    "title": "Chapter 2",
                    "cfi": "/cif_02",
                    "page": "2",
                    "url": "vitalsource://book/bookID/BOOK_ID/cfi//cif_02",
                },
            ]
        }


@pytest.fixture
def list_chapters_response():
    """Return the JSON body of a valid VitalSource Book TOC API response."""
    return {
        "table_of_contents": [
            {
                "title": "Chapter 1",
                "cfi": "/cif_01",
                "page": "1",
            },
            {
                "title": "Chapter 2",
                "cfi": "/cif_02",
                "page": "2",
            },
        ]
    }

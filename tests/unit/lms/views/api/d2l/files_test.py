from unittest.mock import sentinel

import pytest

from lms.views.api.d2l.files import list_files


@pytest.mark.parametrize(
    "toc,files",
    [
        (
            [
                {
                    "topics": [
                        {
                            "id": sentinel.id,
                            "type": "File",
                            "name": sentinel.name,
                            "updated_at": sentinel.updated_at,
                        },
                        {
                            "type": "NOT A FILE",
                        },
                    ]
                }
            ],
            [
                {
                    "id": "d2l://content-resource/sentinel.id/",
                    "display_name": sentinel.name,
                    "updated_at": sentinel.updated_at,
                    "type": "File",
                }
            ],
        ),
        (
            [
                {
                    "topics": [
                        {
                            "id": sentinel.id,
                            "type": "File",
                            "name": sentinel.name,
                            "updated_at": sentinel.updated_at,
                        }
                    ],
                    "modules": [
                        {
                            "topics": [
                                {
                                    "id": sentinel.nested_id,
                                    "type": "File",
                                    "name": sentinel.nested_name,
                                    "updated_at": sentinel.nested_updated_at,
                                }
                            ],
                        }
                    ],
                }
            ],
            [
                {
                    "id": "d2l://content-resource/sentinel.id/",
                    "display_name": sentinel.name,
                    "updated_at": sentinel.updated_at,
                    "type": "File",
                },
                {
                    "id": "d2l://content-resource/sentinel.nested_id/",
                    "display_name": sentinel.nested_name,
                    "updated_at": sentinel.nested_updated_at,
                    "type": "File",
                },
            ],
        ),
    ],
)
def test_course_group_sets(pyramid_request, d2l_api_client, toc, files):
    pyramid_request.matchdict = {"course_id": "test_course_id"}
    d2l_api_client.course_table_of_contents.return_value = toc

    result = list_files(sentinel.context, pyramid_request)

    assert result == files
    d2l_api_client.course_table_of_contents.assert_called_once_with("test_course_id")

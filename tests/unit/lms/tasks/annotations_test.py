import logging
from contextlib import contextmanager

import pytest

from lms.tasks import annotations
from tests import factories


@pytest.mark.usefixtures("annotation_activity_email_service")
class TestAnnotationEvent:
    def test_annotation_event(
        self,
        annotation_event,
        caplog,
        annotation_activity_email_service,
        mentioning_user,
        mentioned_user,
        assignment,
    ):
        annotations.annotation_event(event=annotation_event)

        assert "Processing mention" in caplog.text
        annotation_activity_email_service.send_mention.assert_called_once_with(
            annotation_event["annotation"]["id"],
            annotation_event["annotation"]["text_rendered"],
            annotation_event["annotation"]["quote"],
            mentioning_user.h_userid,
            mentioned_user.h_userid,
            assignment.id,
        )

    def test_annotation_event_delete(self, annotation_event, caplog):
        annotation_event["action"] = "delete"

        annotations.annotation_event(event=annotation_event)

        assert "Skipping event type" in caplog.text

    def test_annotation_event_private_annotation(
        self, private_annotation_event, caplog
    ):
        annotations.annotation_event(event=private_annotation_event)

        assert "Skipping private annotation" in caplog.text

    def test_annotation_event_with_no_email(
        self, annotation_event, caplog, mentioned_user
    ):
        mentioned_user.email = None

        annotations.annotation_event(event=annotation_event)

        assert "has no email address" in caplog.text

    def test_annotation_event_self_mention(self, self_mention_annotation_event, caplog):
        annotations.annotation_event(event=self_mention_annotation_event)

        assert "Skipping self-mention" in caplog.text

    @pytest.fixture
    def assignment(self):
        return factories.Assignment()

    @pytest.fixture
    def mentioning_user(self):
        return factories.LMSUser(email="EMAIL")

    @pytest.fixture
    def mentioned_user(self):
        return factories.LMSUser(email="EMAIL")

    @pytest.fixture
    def annotation_event(self, assignment, mentioning_user, mentioned_user):
        return {
            "action": "create",
            "annotation": {
                "id": "w6fNigSgEfCOTdupAyRrPQ",
                "created": "2025-03-19T09:01:37.181037+00:00",
                "updated": "2025-03-19T09:01:37.181037+00:00",
                "text_rendered": "ANNOTATION TEXT",
                "quote": "ANNOTATION QUOTE",
                "user": mentioning_user.h_userid,
                "uri": "https://example.com/",
                "text": '<a data-hyp-mention="" data-userid="acct:270d2d38d2ddd16c911661e62f116c@lms.hypothes.is">@Dean Dean</a> ',
                "tags": [],
                "group": "GgW8qVLX",
                "permissions": {
                    "read": ["group:GgW8qVLX"],
                    "admin": ["acct:3a022b6c146dfd9df4ea8662178eac@lms.hypothes.is"],
                    "update": ["acct:3a022b6c146dfd9df4ea8662178eac@lms.hypothes.is"],
                    "delete": ["acct:3a022b6c146dfd9df4ea8662178eac@lms.hypothes.is"],
                },
                "target": [
                    {
                        "source": "https://example.com/",
                        "selector": [
                            {
                                "type": "RangeSelector",
                                "endOffset": 117,
                                "startOffset": 112,
                                "endContainer": "/div[1]/p[1]",
                                "startContainer": "/div[1]/p[1]",
                            },
                            {"end": 142, "type": "TextPositionSelector", "start": 137},
                            {
                                "type": "TextQuoteSelector",
                                "exact": "prior",
                                "prefix": "   domain in literature without ",
                                "suffix": " coordination or asking for perm",
                            },
                        ],
                    }
                ],
                "document": {"title": ["Example Domain"]},
                "links": {
                    "incontext": "http://localhost:8000/w6fNigSgEfCOTdupAyRrPQ/example.com/",
                    "json": "http://localhost:5000/api/annotations/w6fNigSgEfCOTdupAyRrPQ",
                },
                "mentions": [
                    {
                        "userid": mentioned_user.h_userid,
                        "original_userid": mentioned_user.h_userid,
                        "username": "270d2d38d2ddd16c911661e62f116c",
                        "display_name": mentioned_user.display_name,
                        "link": None,
                        "description": None,
                        "joined": None,
                    }
                ],
                "user_info": {"display_name": "DISPLAY NAME TEACHER"},
                "metadata": {
                    "lms": {
                        "guid": assignment.tool_consumer_instance_guid,
                        "assignment": {
                            "resource_link_id": assignment.resource_link_id,
                        },
                    }
                },
                "flagged": False,
                "hidden": False,
            },
        }

    @pytest.fixture
    def private_annotation_event(self, annotation_event):
        annotation_event["annotation"]["permissions"]["read"] = annotation_event[
            "annotation"
        ]["permissions"]["admin"]
        return annotation_event

    @pytest.fixture
    def self_mention_annotation_event(self, annotation_event):
        annotation_event["annotation"]["mentions"][0]["userid"] = annotation_event[
            "annotation"
        ]["user"]
        return annotation_event

    @pytest.fixture
    def caplog(self, caplog):
        caplog.set_level(logging.DEBUG)
        return caplog


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.annotations.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app

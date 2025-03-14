from unittest.mock import sentinel

from lms.tasks import annotations


def test_annotation_event():
    assert not annotations.annotation_event(event=sentinel.event)

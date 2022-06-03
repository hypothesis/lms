"""Assertions for use in LTI 1.3 test."""

import json

from lms.resources._js_config import JSConfig


def assert_launched_as_student(response):
    assert response.status_code == 200

    # This assumes an unconfigured launch giving us the error page
    assert response.content_type == "text/html"
    assert "assignment isn't configured" in response.text


def assert_launched_as_teacher(response):
    assert response.status_code == 200
    assert response.html

    js_config = json.loads(response.html.find("script", {"class": "js-config"}).string)

    # This assumes an unconfigured launch, which causes the file picker to
    # appear for teachers. We also double-check with the debug tag for role
    assert "role:instructor" in js_config["debug"]["tags"]
    assert js_config["mode"] == JSConfig.Mode.FILE_PICKER

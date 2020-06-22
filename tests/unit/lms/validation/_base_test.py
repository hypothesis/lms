import json

import pytest
from marshmallow import fields
from pyramid.httpexceptions import HTTPUnsupportedMediaType
from pyramid.testing import DummyRequest

from lms.validation._base import JSONPyramidRequestSchema


class TestJSONPyramidRequestSchema:
    class ExampleSchema(JSONPyramidRequestSchema):
        key = fields.Str()

    def test_it_reads_from_json_content(self):
        data = {"key": "value"}

        request = DummyRequest(
            body=json.dumps(data),
            headers={"Content-Type": "application/json; charset=UTF-8"},
        )
        request.content_type = request.headers["content-type"] = "application/json"

        assert self.ExampleSchema(request).parse() == data

    @pytest.mark.parametrize("content_type", (None, "text/html"))
    def test_it_fails_without_json_content_type_header(self, content_type):
        request = DummyRequest(body=json.dumps({}))
        request.content_type = request.headers["content_type"] = content_type

        with pytest.raises(HTTPUnsupportedMediaType):
            self.ExampleSchema(request).parse()

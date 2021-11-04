import json
from unittest.mock import sentinel

import pytest
from marshmallow import fields
from pyramid.httpexceptions import HTTPUnsupportedMediaType
from pyramid.testing import DummyRequest

from lms.services import ExternalRequestError
from lms.validation._base import JSONPyramidRequestSchema, RequestsResponseSchema
from tests import factories


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


class TestRequestsResponseSchema:
    class MySchema(RequestsResponseSchema):
        test_field = fields.Str(required=True)

    def test_it_returns_the_parsed_data_if_the_response_is_valid(self):
        response = factories.requests.Response(json_data={"test_field": "test_value"})
        schema = self.MySchema(response)

        parsed_data = schema.parse()

        assert parsed_data == {"test_field": "test_value"}

    @pytest.mark.parametrize(
        "response_body,validation_errors",
        [
            pytest.param(
                "{}",
                {"test_field": ["Missing data for required field."]},
                id="Valid JSON but doesn't match the schema",
            ),
            pytest.param(
                "foo",
                {"_schema": ["response doesn't have a valid JSON body"]},
                id="Not valid JSON at all",
            ),
        ],
    )
    def test_it_raises_ExternalRequestError_if_the_response_is_invalid(
        self, response_body, validation_errors
    ):
        response = factories.requests.Response(
            raw=response_body, request=sentinel.request
        )
        schema = self.MySchema(response)

        with pytest.raises(ExternalRequestError) as exc_info:
            schema.parse()

        exc = exc_info.value
        assert isinstance(exc, ExternalRequestError)
        assert exc.request == sentinel.request
        assert exc.response == response
        assert exc.validation_errors == validation_errors

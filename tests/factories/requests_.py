import json
from io import BytesIO

import requests
from factory import Factory, Faker


class Response(Factory):
    class Meta:
        model = requests.Response

    raw = None
    json_data = None
    encoding = "utf-8"
    status_code = Faker(
        "random_element", elements=[200, 201, 301, 304, 401, 404, 500, 501],
    )
    headers = None

    @classmethod
    def _adjust_kwargs(cls, raw=..., json_data=..., **kwargs):
        headers = kwargs["headers"] or {}
        encoding = kwargs["encoding"]

        if raw is None and json_data is not None:
            raw = json.dumps(json_data)

            if not headers:
                headers["Content-Type"] = f"application/json; charset={encoding}"

        if isinstance(raw, str):
            raw = BytesIO(raw.encode(encoding))

        kwargs["raw"] = raw

        # Requests seems to store these lower case and expects them that way

        kwargs["headers"] = {key.lower(): value for key, value in headers.items()}

        return kwargs

    @classmethod
    def _create(cls, model_class, **kwargs):
        response = model_class()
        for field, value in kwargs.items():
            setattr(response, field, value)

        return response

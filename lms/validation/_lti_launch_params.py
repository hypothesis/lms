from urllib.parse import unquote

import marshmallow

from lms.validation._helpers import PyramidRequestSchema


class LaunchParamsSchema(PyramidRequestSchema):
    """
    Schema describing the minimum requirements for LTI launch parameters.

    This *DOES NOT* contain all of the fields required for authentication.
    For that see `lms.validation.authentication.LaunchParamsAuthSchema`
    """

    pass


class LaunchParamsURLConfiguredSchema(LaunchParamsSchema):
    """
    Schema for an "URL-configured" Basic LTI Launch.

    An URL-configured launch is one where the content URL is provided by a "url"
    launch param.
    """

    url = marshmallow.fields.Str(required=True)

    @marshmallow.post_load
    def _decode_url(self, _data, **_kwargs):  # pylint:disable=no-self-use
        # Work around a bug in Canvas's handling of LTI Launch URLs in
        # SpeedGrader launches. In that context, query params get
        # doubly-encoded. This is worked around by detecting when this has
        # happened and decoding the URL a second time.
        #
        # See https://github.com/instructure/canvas-lms/issues/1486
        url = _data["url"]
        if url.lower().startswith("http%3a") or url.lower().startswith("https%3a"):
            url = unquote(url)
            _data["url"] = url
        return _data

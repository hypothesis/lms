from webargs import pyramidparser

from lms.validation._exceptions import ValidationError
from lms.validation._oauth import CANVAS_OAUTH_CALLBACK_ARGS


__all__ = ("parser", "CANVAS_OAUTH_CALLBACK_ARGS", "ValidationError")


parser = pyramidparser.PyramidParser()


@parser.error_handler
def _handle_error(error, _req, _schema, _status_code, _headers):
    raise ValidationError(messages=error.messages) from error

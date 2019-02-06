"""Validation for OAuth views."""
from webargs import fields


#: Arguments for the canvas_oauth_callback() view.
CANVAS_OAUTH_CALLBACK_ARGS = {
    "code": fields.Str(required=True),
    "state": fields.Str(required=True),
}

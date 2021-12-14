from lms.views.api.canvas.exceptions import (
    CanvasGroupSetEmpty,
    CanvasGroupSetNotFound,
    CanvasStudentNotInGroup,
)


def includeme(config):  # pragma: no cover
    config.scan(__name__)
    config.include("lms.views.predicates")

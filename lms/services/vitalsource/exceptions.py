from lms.services.exceptions import SerializableError


class VitalSourceError(SerializableError):
    """Indicate a failure in the VitalSource service or client."""


class VitalSourceMalformedRegex(VitalSourceError):  # noqa: N818
    """An issue with the user regex."""

    def __init__(self, description, pattern):
        super().__init__(
            error_code="bad_user_lti_pattern",
            message="There is a problem with the configured VitalSource configuration",
            details={"error": description, "pattern": pattern},
        )

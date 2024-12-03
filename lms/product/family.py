from enum import StrEnum


class Family(StrEnum):
    """Enum for which product this relates to."""

    BLACKBAUD = "BlackbaudK12"
    BLACKBOARD = "BlackboardLearn"
    CANVAS = "canvas"
    D2L = "desire2learn"
    MOODLE = "moodle"
    SAKAI = "sakai"
    SCHOOLOGY = "schoology"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, _value):
        return cls.UNKNOWN

    @classmethod
    def from_launch(cls, lti_params: dict):
        """
        Get the product of the current launch.

        This method only applies for the initial launch made by from an LMS.
        For any subsequent API calls see LTIUser.lti.product_family.
        """
        # We'll use the parameters available to guess
        if product_name := lti_params.get("tool_consumer_info_product_family_code"):
            return cls(product_name)

        # If we don't get a hint from LTI check a canvas specific parameter
        if "custom_canvas_course_id" in lti_params:
            return cls.CANVAS

        # Another canvas-only fix, when the API params are not correctly set use the GUID
        if lti_params.get("tool_consumer_instance_guid", "").endswith("canvas-lms"):
            return cls.CANVAS

        return cls.UNKNOWN

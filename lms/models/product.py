from dataclasses import dataclass
from enum import Enum


@dataclass
class Product:
    class Family(str, Enum):
        BLACKBAUD = "BlackbaudK12"
        BLACKBOARD = "BlackboardLearn"
        CANVAS = "canvas"
        D2L = "desire2learn"
        MOODLE = "moodle"
        SAKAI = "sakai"
        SCHOOLOGY = "schoology"
        UNKNOWN = "unkown"

        @classmethod
        def _missing_(cls, _value):
            return cls.UNKNOWN

    family: Family

    @classmethod
    def from_request(cls, request):
        return Product(family=cls._get_family(request))

    @classmethod
    def _get_family(cls, request):
        # If we are in an API request, where we are forwarding the product type ourselves
        if request.content_type == "application/json":
            return cls.Family(request.json["lms"]["product"])

        # In an LTI launch we'll use the parameters available to guess
        if product_name := request.lti_params.get(
            "tool_consumer_info_product_family_code"
        ):
            return cls.Family(product_name)

        # If we don't get a hint from LTI check a canvas specific parameter
        if "custom_canvas_course_id" in request.lti_params:
            return cls.Family.CANVAS

        return cls.Family.UNKNOWN


def includeme(config):
    config.add_request_method(
        Product.from_request, name="product", property=True, reify=True
    )

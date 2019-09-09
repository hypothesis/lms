"""Schema for validating params required for LIS Outcomes."""
import marshmallow

from lms.validation._helpers import PyramidRequestSchema
from lms.values import LISResultSourcedId


__all__ = ["LISResultSourcedIdSchema"]


class LISResultSourcedIdSchema(PyramidRequestSchema):
    """
    Schema for LIS Result/LMS Outcomes params.

    Validates params for LMS Outcomes metadata. Usage via webargs::

        >>> from webargs.pyramidparser import parser
        >>>
        >>> schema = LISResultSourcedIdSchema(request)
        >>> parsed_params = parser.parse(schema, request)

    Or to verify the request and get an :class:`~lms.values.LISResultSourcedId`
    from the request's params::

        >>> schema = LISResultSourcedIdSchema(request)
        >>> schema.lis_result_sourcedid()
        LISResultSourcedId(lis_result_sourcedid='...', ...)
    """

    lis_result_sourcedid = marshmallow.fields.Str(required=True)
    lis_outcome_service_url = marshmallow.fields.Str(required=True)
    context_id = marshmallow.fields.Str(required=True)
    resource_link_id = marshmallow.fields.Str(required=True)
    tool_consumer_info_product_family_code = marshmallow.fields.Str(missing="")

    def lis_result_sourcedid_info(self):
        """
        Return an :class:`~lms.values.LISResultSourcedId`.

        :raise ValidationError: if the request isn't a valid LIS Outcome launch
        :rtype: LISResultSourcedId
        """

        parsed_params = self.parse(locations=["form"])

        return LISResultSourcedId(
            lis_result_sourcedid=parsed_params["lis_result_sourcedid"],
            lis_outcome_service_url=parsed_params["lis_outcome_service_url"],
            context_id=parsed_params["context_id"],
            resource_link_id=parsed_params["resource_link_id"],
            tool_consumer_info_product_family_code=parsed_params[
                "tool_consumer_info_product_family_code"
            ],
        )

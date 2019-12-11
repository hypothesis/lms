from lms.logic.grading.grading_types import FloatGrading


class ToolConsumerService:
    product_family_code = None

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @classmethod
    def factory(cls, context, request):
        service_class = cls
        product_family_code = request.params.get(
            "tool_consumer_info_product_family_code"
        )

        for sub_class in cls.__subclasses__():
            if sub_class.product_family_code == product_family_code:
                service_class = sub_class
                break

        return service_class(context, request)

    # TODO - Are these really three different cases or can we collapse them?
    def assignment_is_gradable(self, resource_link_id):
        # When an instructor launches an LTI assignment, Blackboard sets the
        # `lis_outcome_service_url` form param if evaluation is enabled or omits it otherwise.
        #
        # When extending the generic LTI grader to support other LMSes, we may need
        # a different method to detect whether grading is enabled for a given
        # assignment.
        #
        # The URL here is not actually used to submit grades. Instead that URL
        # is passed to us when a _student_ launches the assignment and recorded for
        # use when an instructor launches the assignment.
        return "lis_outcome_service_url" in self.request.params

    def requires_grading_ui(self, resource_link_id):
        return True

    def grading_type(self, resource_link_id):
        return FloatGrading()

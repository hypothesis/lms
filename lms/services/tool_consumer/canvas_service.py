from lms.services.tool_consumer.generic_service import ToolConsumerService


class CanvasInterface(ToolConsumerService):
    product_family_code = "canvas"

    def requires_grading_ui(self, resource_link_id):
        return False

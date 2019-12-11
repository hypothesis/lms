from lms.tool_consumer.moodle.model import Scale
from lms.tool_consumer.moodle.module.api_module import APISubModule


class CoreCompetency(APISubModule):
    area = "core_competency"

    def get_scale_values(self, scale_id):
        """Get the values for a scale"""

        scale_id = int(scale_id)

        values = self.call("get_scale_values", params={"scaleid": scale_id})
        return Scale.from_values(scale_id, values)

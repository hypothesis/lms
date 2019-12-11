from lms.tool_consumer.moodle import module
from lms.tool_consumer.moodle.ws import MoodleWebServiceClient


class MoodleClient(MoodleWebServiceClient):
    def _spawn_child(self, child_class):
        if child_class not in self.children:
            self.children[child_class] = child_class(self)

        return self.children[child_class]

    @property
    def competency(self):
        return self._spawn_child(module.CoreCompetency)

    @property
    def course(self):
        return self._spawn_child(module.CoreCourse)

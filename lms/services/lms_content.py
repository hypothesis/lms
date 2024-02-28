from abc import abstractmethod
from typing import Protocol

from lms.product.family import Family
from lms.services.canvas import CanvasService
from lms.services.d2l_api import D2LAPIClient
from lms.services.moodle import MoodleAPIClient


class BaseLMSAPI(Protocol):
    @abstractmethod
    def list_files(self, course_id):
        raise NotImplementedError


class LMSAPI:
    def __init__(self, api: BaseLMSAPI):
        self._api = api

    def list_files(self, course_id):
        return self._api.list_files(course_id)

    @classmethod
    def factory(cls, _context, request):
        api = None
        if request.product.family == Family.D2L:
            api = request.find_service(D2LAPIClient)
        elif request.product.family == Family.CANVAS:
            api = request.find_service(CanvasService)
        elif request.product.family == Family.MOODLE:
            api = request.find_service(MoodleAPIClient)
        elif request.product.family == Family.BLACKBOARD:
            api = request.find_service(name="blackboard_api_client")
        else:
            raise NotImplementedError

        return cls(api=api)

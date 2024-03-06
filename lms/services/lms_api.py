from abc import abstractmethod
from typing import Protocol

from lms.product.family import Family


class BaseLMSAPI(Protocol):
    @abstractmethod
    def list_files(self, course_id):
        raise NotImplementedError


class LMSAPI:
    def __init__(self, api: BaseLMSAPI):
        self._api = api

    def list_files(self, course_id, folder_id=None):
        return self._api.list_files(course_id)

    @classmethod
    def factory(cls, _context, request):
        api = None
        if api_service_name := request.product.api_service_name:
            api = request.find_service(name=api_service_name)
        else:
            raise NotImplementedError

        return cls(api=api)

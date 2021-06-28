from unittest.mock import sentinel

import pytest

from lms.services.file import FileService, factory
from tests import factories


class TestGet:
    def test_it_returns_the_matching_file_if_there_is_one(
        self, application_instance, svc
    ):
        file_ = factories.File(application_instance=application_instance)

        assert svc.get(application_instance, file_.lms_id, file_.type) == file_

    def test_it_returns_None_if_theres_no_matching_file(
        self, application_instance, svc
    ):
        assert not svc.get(application_instance, "unknown_file_id", "canvas_file")

    def test_it_doesnt_return_matching_files_from_other_application_instances(
        self, application_instance, svc
    ):
        file_ = factories.File()

        assert not svc.get(application_instance, file_.lms_id, file_.type)


@pytest.mark.usefixtures("application_instance_service")
class TestFactory:
    def test_it(self, pyramid_request):
        file_service = factory(sentinel.context, pyramid_request)

        assert isinstance(file_service, FileService)


@pytest.fixture
def application_instance():
    return factories.ApplicationInstance()


@pytest.fixture(autouse=True)
def noise(application_instance):
    factories.File(application_instance=application_instance)


@pytest.fixture
def svc(db_session):
    return FileService(db_session)

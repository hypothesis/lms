from unittest.mock import sentinel

import pytest

from lms.models import File
from lms.services.file import FileService, factory
from tests import factories


class TestGet:
    def test_it_returns_the_matching_file_if_there_is_one(
        self, application_instance, svc
    ):
        file_ = factories.File(application_instance=application_instance)

        assert svc.get(file_.lms_id, file_.type) == file_

    def test_it_returns_None_if_theres_no_matching_file(self, svc):
        assert not svc.get("unknown_file_id", "canvas_file")

    def test_it_doesnt_return_matching_files_from_other_application_instances(
        self, svc
    ):
        file_ = factories.File()

        assert not svc.get(file_.lms_id, file_.type)

    def test_it_upsert(self, db_session, svc, application_instance):
        files = factories.File.create_batch(
            5, application_instance=application_instance
        )
        db_session.flush()
        total_files = db_session.query(File).count()

        svc.upsert(
            [
                {
                    "type": file.type,
                    "course_id": file.course_id,
                    "lms_id": file.lms_id,
                    "name": f"file_{i}",
                    "size": i,
                }
                for i, file in enumerate(files)
            ]
        )

        assert db_session.query(File).count() == total_files
        # Refresh the model instances to gather changed data from the DB
        _ = [db_session.refresh(file) for file in files]
        for i, file in enumerate(files):
            assert file.size == i
            assert file.name == f"file_{i}"


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
def svc(application_instance, db_session):
    return FileService(application_instance, db_session)

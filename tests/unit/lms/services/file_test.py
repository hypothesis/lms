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

    def test_upsert(self, db_session, svc, application_instance):
        existing_files_count = db_session.query(File).count()

        # This files will be created on the DB
        update_files = factories.File.create_batch(
            5, application_instance=application_instance
        )
        # These won't exist on the DB
        insert_files = factories.File.build_batch(5)
        assert db_session.query(File).count() == existing_files_count + len(
            update_files
        )
        svc.upsert(
            [
                {
                    "type": file.type,
                    "course_id": file.course_id,
                    "lms_id": file.lms_id,
                    "name": f"update_file_{i}",
                    "size": i * 10,
                }
                for i, file in enumerate(update_files)
            ]
            + [
                {
                    "type": file.type,
                    "course_id": file.course_id,
                    "lms_id": file.lms_id,
                    "name": f"insert_file_{i}",
                    "size": i * 100,
                }
                for i, file in enumerate(insert_files)
            ],
        )

        assert db_session.query(File).count() == existing_files_count + len(
            update_files
        ) + len(insert_files)

        # Refresh the model instances to gather changed data from the DB
        for file in update_files:
            db_session.refresh(file)
        for i, file in enumerate(update_files):
            assert file.size == i * 10
            assert file.name == f"update_file_{i}"

        for i, file in enumerate(insert_files):
            file = db_session.query(File).filter_by(lms_id=file.lms_id).one()
            assert file.size == i * 100
            assert file.name == f"insert_file_{i}"


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

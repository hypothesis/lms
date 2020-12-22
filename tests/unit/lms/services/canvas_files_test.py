from unittest.mock import sentinel

import pytest

from lms.models import CanvasFile
from lms.services.canvas_files import factory
from tests import factories


class TestUpsert:
    def test_if_theres_no_record_in_the_db_it_adds_one(self, db_session, svc):
        canvas_file = factories.CanvasFile.build()

        svc.upsert(canvas_file)

        assert (
            db_session.query(CanvasFile)
            .filter_by(
                consumer_key=canvas_file.application_instance.consumer_key,
                tool_consumer_instance_guid=canvas_file.tool_consumer_instance_guid,
                course_id=canvas_file.course_id,
                file_id=canvas_file.file_id,
                filename=canvas_file.filename,
                size=canvas_file.size,
            )
            .one_or_none()
        )

    def test_if_theres_a_record_in_the_db_it_updates_it(self, db_session, svc):
        existing_file = factories.CanvasFile()
        new_file = factories.CanvasFile.build(
            consumer_key=existing_file.application_instance.consumer_key,
            tool_consumer_instance_guid=existing_file.tool_consumer_instance_guid,
            course_id=existing_file.course_id,
            file_id=existing_file.file_id,
            filename="NEW" + existing_file.filename,
        )

        svc.upsert(new_file)

        assert (
            db_session.query(CanvasFile)
            .filter_by(
                consumer_key=new_file.consumer_key,
                tool_consumer_instance_guid=new_file.tool_consumer_instance_guid,
                course_id=new_file.course_id,
                file_id=new_file.file_id,
                filename=new_file.filename,
                size=new_file.size,
            )
            .one_or_none()
        )


@pytest.fixture
def svc(pyramid_request):
    return factory(sentinel.context, pyramid_request)

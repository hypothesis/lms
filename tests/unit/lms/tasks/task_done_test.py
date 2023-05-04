from contextlib import contextmanager
from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time
from sqlalchemy import select

from lms.models import TaskDone
from lms.tasks.task_done import delete_expired_rows


@freeze_time("2023-05-04 12:12:01")
def test_delete_expired_rows(db_session):
    frozen_time = datetime.fromisoformat("2023-05-04 12:12:01")
    expired_task_dones = [
        TaskDone(key="expired_1", expires_at=frozen_time - timedelta(seconds=1)),
        TaskDone(key="expired_2", expires_at=frozen_time - timedelta(seconds=2)),
    ]
    fresh_task_done = TaskDone(
        key="fresh", expires_at=frozen_time + timedelta(seconds=1)
    )
    db_session.add_all([*expired_task_dones, fresh_task_done])
    db_session.flush()

    delete_expired_rows()

    # It should have deleted expired_task_dones but not fresh_task_done.
    assert db_session.scalars(select(TaskDone.id)).all() == [fresh_task_done.id]


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.task_done.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app

from celery import Celery

from lms.tasks.celery import app


class TestApp:
    def test_sanity(self):
        assert isinstance(app, Celery)

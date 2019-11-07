from unittest import mock

import pytest
from pyramid.tweens import EXCVIEW

from lms.tweens import includeme, rollback_db_session_tween_factory


class TestDBRollbackSessionOnExceptionTween:
    def test_it_does_nothing_usually(self, handler, pyramid_request):
        tween = rollback_db_session_tween_factory(handler, pyramid_request.registry)

        tween(pyramid_request)

        handler.assert_called_once_with(pyramid_request)
        pyramid_request.db.rollback.assert_not_called()

    def test_it_calls_db_rollback_on_exception(self, handler, pyramid_request):
        handler.side_effect = IOError

        tween = rollback_db_session_tween_factory(handler, pyramid_request.registry)

        with pytest.raises(IOError):
            tween(pyramid_request)

        handler.assert_called_once_with(pyramid_request)
        pyramid_request.db.rollback.assert_called_once_with()

    @pytest.fixture
    def handler(self):
        return mock.create_autospec(lambda request: None)  # pragma: nocover

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.db = mock.MagicMock(spec_set=["rollback"])
        return pyramid_request


class TestIncludeMe:
    def test_it_adds_rollback_db_session_tween(self, config):
        includeme(config)

        config.add_tween.assert_called_with(
            "lms.tweens.rollback_db_session_tween_factory", under=EXCVIEW
        )

    @pytest.fixture
    def config(self):
        return mock.MagicMock(spec_set=["add_tween"])

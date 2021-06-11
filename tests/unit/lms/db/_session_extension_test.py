import pytest

from lms.db._session_extension import SessionExtension


class TestSessionExtension:
    def test_it(self, session):
        result = session.extension

        assert isinstance(result, SessionExtension)
        assert result.session == session

    def test_it_stores_the_name(self, session):
        assert session.extension.name == "extension"

    def test_you_cannot_call_it_on_the_class(self):
        class Session:
            extension = SessionExtension()

        with pytest.raises(TypeError):
            assert Session.extension

    @pytest.fixture
    def session(self):
        class Session:
            extension = SessionExtension()

        return Session()

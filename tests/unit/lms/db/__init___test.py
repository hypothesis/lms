from sqlalchemy import select

from lms.models import Event


class TestCustomSession:
    def test_compile_query(self, db_session):
        old_style_query = db_session.query(Event).filter_by(id=0)
        new_style_query = select(Event).where(Event.id == 0)

        old_style_query_compiled = db_session.compile_query(old_style_query)
        new_style_query_complied = db_session.compile_query(new_style_query)

        assert old_style_query_compiled == new_style_query_complied
        assert old_style_query_compiled.startswith("SELECT event.id")

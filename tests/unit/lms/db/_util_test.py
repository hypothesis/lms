from sqlalchemy import select

from lms.db import compile_query
from lms.models import Event


def test_compile_query(db_session):
    old_style_query = db_session.query(Event).filter_by(id=0)
    new_style_query = select(Event).where(Event.id == 0)

    old_style_query_compiled = compile_query(old_style_query)
    new_style_query_complied = compile_query(new_style_query)

    assert old_style_query_compiled == new_style_query_complied
    assert (
        old_style_query_compiled
        == """SELECT event.id, event.timestamp, event.type_id, event.application_instance_id, event.course_id, event.assignment_id, event.grouping_id 
FROM event 
WHERE event.id = 0"""  # noqa: W291
    )

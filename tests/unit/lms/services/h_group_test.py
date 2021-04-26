# pylint: disable=protected-access
import pytest

from lms.models import HGroup
from lms.models._hashed_id import hashed_id
from lms.services.h_group import factory


class TestHGroupService:
    def test_upsert_inserts(self, service):
        assert not service._db.query(HGroup).count()

        group = service.upsert("name", "auth", "course_group")

        assert group.type == "course_group"
        assert service._db.query(HGroup).count() == 1

    def test_upsert_gets(self, service):
        assert not service._db.query(HGroup).count()

        group_1 = service.upsert("name", "auth", "course_group")

        assert group_1.type == "course_group"
        assert service._db.query(HGroup).count() == 1

        group_2 = service.upsert("name", "auth", "course_group")

        assert service._db.query(HGroup).count() == 1
        assert group_1.id == group_2.id

    def test_course_group(self, service):
        group = service.course_group("irrelevant", "tool_guid", "context_id")

        assert group.authority_provided_id == hashed_id("tool_guid", "context_id")
        assert group.type == "course_group"

    def test_course_group_name_is_required(self, service):
        with pytest.raises(ValueError):
            service.course_group(None, "tool_guid", "context_id")

    def test_sections_group(self, service):
        group = service.section_group(
            "irrelevant", "tool_guid", "context_id", "section_id"
        )

        assert group.authority_provided_id == hashed_id(
            "tool_guid", "context_id", "section_id"
        )
        assert group.type == "section_group"

    @pytest.mark.parametrize(
        "name,expected_result",
        (
            ("Test Course", "Test Course"),
            (" Test Course ", "Test Course"),
            ("Test   Course", "Test   Course"),
            ("Object Oriented Polymorphism 101", "Object Oriented Polymorp…"),
            ("  Object Oriented Polymorphism 101  ", "Object Oriented Polymorp…"),
        ),
    )
    def test_truncates_the_name(self, service, name, expected_result):
        clean_name = service._name(name)

        assert clean_name == expected_result

    @pytest.fixture
    def service(self, pyramid_request):
        return factory(
            None,
            pyramid_request,
        )

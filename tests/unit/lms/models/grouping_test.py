import pytest

from lms.models import Grouping
from tests import factories


class TestGrouping:
    def test_groupid(self):
        group = factories.Grouping(authority_provided_id="test_authority_provided_id")

        groupid = group.groupid("lms.hypothes.is")

        assert groupid == "group:test_authority_provided_id@lms.hypothes.is"

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
    def test_name(self, name, expected_result):
        group = Grouping(lms_name=name)

        assert group.name == expected_result

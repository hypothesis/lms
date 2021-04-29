import pytest

from lms.models import HGroup
from tests import factories


class TestHGroup:
    def test_groupid(self):
        group = factories.HGroup(authority_provided_id="test_authority_provided_id")

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
    def test_truncates_the_name(self, name, expected_result):
        clean_name = HGroup(_name=name).name

        assert clean_name == expected_result

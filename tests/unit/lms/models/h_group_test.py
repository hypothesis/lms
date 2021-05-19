import pytest

from lms.models import HGroup
from tests import factories

GROUP_CONSTRUCTORS = (
    (
        HGroup.section_group,
        ("tool_consumer_instance_guid", "context_id", "section_id"),
        "sections_group",
    ),
)


class TestHGroup:
    def test_groupid(self):
        group = factories.HGroup(authority_provided_id="test_authority_provided_id")

        groupid = group.groupid("lms.hypothes.is")

        assert groupid == "group:test_authority_provided_id@lms.hypothes.is"

    def test_sections_group(self, hashed_id):
        group = HGroup.section_group(
            "irrelevant", "tool_guid", "context_id", "section_id"
        )

        hashed_id.assert_called_once_with("tool_guid", "context_id", "section_id")
        assert group.authority_provided_id == hashed_id.return_value
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
    def test_constructors_truncate_the_name(
        self, name_only_constructor, name, expected_result
    ):
        group = name_only_constructor(name)

        assert group.name == expected_result

    def test_constructors_name_is_mandatory(self, name_only_constructor):
        with pytest.raises(ValueError):
            name_only_constructor(None)

    @pytest.fixture(
        params=GROUP_CONSTRUCTORS, ids=[group[2] for group in GROUP_CONSTRUCTORS]
    )
    def name_only_constructor(self, request):
        constructor, args, _group_type = request.param

        return lambda name: constructor(name, *args)

    @pytest.fixture
    def hashed_id(self, patch):
        return patch("lms.models.h_group.hashed_id")

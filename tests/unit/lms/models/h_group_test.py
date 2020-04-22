from unittest import mock

import pytest

from lms.models import HGroup, h_group_name


def test_groupid():
    group = HGroup(mock.sentinel.name, "test_authority_provided_id")

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
def test_h_group_name(name, expected_result):
    assert h_group_name(name) == expected_result

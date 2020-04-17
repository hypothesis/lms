from unittest import mock

from lms.models import HGroup


def test_groupid():
    group = HGroup(mock.sentinel.name, "test_authority_provided_id")

    groupid = group.groupid("lms.hypothes.is")

    assert groupid == "group:test_authority_provided_id@lms.hypothes.is"

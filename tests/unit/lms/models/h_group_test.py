from tests import factories


class TestHGroup:
    def test_groupid(self):
        group = factories.HGroup(authority_provided_id="test_authority_provided_id")

        groupid = group.groupid("lms.hypothes.is")

        assert groupid == "group:test_authority_provided_id@lms.hypothes.is"

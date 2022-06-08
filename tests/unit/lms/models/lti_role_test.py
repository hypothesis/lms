import pytest

from lms.models.lti_role import RoleType, _RoleParser


class TestRoleType:
    # At the time of writing, this is every role string we've seen from an
    # LTI 1.1 LMS
    @pytest.mark.parametrize(
        "value,role_type",
        (
            ("Administrator", RoleType.ADMIN),
            ("Alumni", RoleType.LEARNER),
            ("ContentDeveloper", RoleType.INSTRUCTOR),
            ("Faculty", RoleType.INSTRUCTOR),
            ("Guest", RoleType.LEARNER),
            ("Instructor", RoleType.INSTRUCTOR),
            ("Learner", RoleType.LEARNER),
            ("Member", RoleType.LEARNER),
            ("Mentor", RoleType.INSTRUCTOR),
            ("None", RoleType.LEARNER),
            ("Observer", RoleType.LEARNER),
            ("Other", RoleType.LEARNER),
            ("ProspectiveStudent", RoleType.LEARNER),
            ("Staff", RoleType.INSTRUCTOR),
            ("Student", RoleType.LEARNER),
            ("urn:lti:instrole:ims/lis/Administrator", RoleType.ADMIN),
            ("urn:lti:instrole:ims/lis/Alumni", RoleType.LEARNER),
            ("urn:lti:instrole:ims/lis/Faculty", RoleType.INSTRUCTOR),
            ("urn:lti:instrole:ims/lis/Guest", RoleType.LEARNER),
            ("urn:lti:instrole:ims/lis/Instructor", RoleType.INSTRUCTOR),
            ("urn:lti:instrole:ims/lis/Learner", RoleType.LEARNER),
            ("urn:lti:instrole:ims/lis/Member", RoleType.LEARNER),
            ("urn:lti:instrole:ims/lis/Mentor", RoleType.INSTRUCTOR),
            ("urn:lti:instrole:ims/lis/None", RoleType.LEARNER),
            ("urn:lti:instrole:ims/lis/Observer", RoleType.LEARNER),
            ("urn:lti:instrole:ims/lis/Other", RoleType.LEARNER),
            ("urn:lti:instrole:ims/lis/ProspectiveStudent", RoleType.LEARNER),
            ("urn:lti:instrole:ims/lis/Staff", RoleType.INSTRUCTOR),
            ("urn:lti:instrole:ims/lis/Student", RoleType.LEARNER),
            ("urn:lti:role:ims/lis/ContentDeveloper", RoleType.INSTRUCTOR),
            ("urn:lti:role:ims/lis/Instructor", RoleType.INSTRUCTOR),
            ("urn:lti:role:ims/lis/Learner", RoleType.LEARNER),
            ("urn:lti:role:ims/lis/Mentor", RoleType.INSTRUCTOR),
            ("urn:lti:role:ims/lis/TeachingAssistant", RoleType.INSTRUCTOR),
            ("urn:lti:role:ims/lis/TeachingAssistant/Grader", RoleType.INSTRUCTOR),
            ("urn:lti:sysrole:ims/lis/Administrator", RoleType.ADMIN),
            ("urn:lti:sysrole:ims/lis/None", RoleType.LEARNER),
            ("urn:lti:sysrole:ims/lis/SysAdmin", RoleType.ADMIN),
        ),
    )
    def test_parse_lti_role_v11(self, value, role_type):
        assert RoleType.parse_lti_role(value) == role_type

    # pylint: disable=protected-access
    @pytest.mark.parametrize(
        "value,role_type", tuple(_RoleParser._V13_ROLE_MAPPINGS.items())
    )
    def test_parse_lti_role_v13_exact_matches(self, value, role_type):
        assert RoleType.parse_lti_role(value) == role_type

    _V13_PREFIX = "http://purl.imsglobal.org/vocab/lis/v2/"

    @pytest.mark.parametrize(
        "value,role_type",
        (
            (
                f"{_V13_PREFIX}membership/Learner#GuestLearner",
                RoleType.LEARNER,
            ),
            (
                f"{_V13_PREFIX}membership/Learner#Instructor",
                RoleType.INSTRUCTOR,
            ),
            (
                f"{_V13_PREFIX}membership/Instructor#Lecturer",
                RoleType.INSTRUCTOR,
            ),
            (f"{_V13_PREFIX}membership/WRONG", RoleType.LEARNER),
        ),
    )
    def test_parse_lti_role_v13_prefix_matches(self, value, role_type):
        # "Context roles" can have sub-roles appended to the end. Check we can
        # match these correctly
        assert RoleType.parse_lti_role(value) == role_type

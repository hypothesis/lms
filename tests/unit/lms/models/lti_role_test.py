import pytest
from sqlalchemy.exc import StatementError

from lms.models.lti_role import LTIRole, LTIRoleOverride, RoleScope, RoleType


class TestLTIRoleOverride:
    def test_value(self):
        lti_role = LTIRole(value="ROLE")

        # pylint:disable=comparison-with-callable
        assert LTIRoleOverride(lti_role=lti_role).value == lti_role.value


class TestLTIRole:
    _V13_PREFIX = "http://purl.imsglobal.org/vocab/lis/v2/"

    @pytest.mark.parametrize(
        "value,role_type,role_scope",
        # At the time of writing, this is every role string we've seen
        [
            (
                "urn:lti:instrole:ims/lis/Administrator",
                RoleType.ADMIN,
                RoleScope.INSTITUTION,
            ),
            (
                "urn:lti:instrole:ims/lis/Alumni",
                RoleType.LEARNER,
                RoleScope.INSTITUTION,
            ),
            (
                "urn:lti:instrole:ims/lis/Faculty",
                RoleType.INSTRUCTOR,
                RoleScope.INSTITUTION,
            ),
            ("urn:lti:instrole:ims/lis/Guest", RoleType.LEARNER, RoleScope.INSTITUTION),
            (
                "urn:lti:instrole:ims/lis/Instructor",
                RoleType.INSTRUCTOR,
                RoleScope.INSTITUTION,
            ),
            (
                "urn:lti:instrole:ims/lis/Learner",
                RoleType.LEARNER,
                RoleScope.INSTITUTION,
            ),
            (
                "urn:lti:instrole:ims/lis/Member",
                RoleType.LEARNER,
                RoleScope.INSTITUTION,
            ),
            (
                "urn:lti:instrole:ims/lis/Mentor",
                RoleType.INSTRUCTOR,
                RoleScope.INSTITUTION,
            ),
            ("urn:lti:instrole:ims/lis/None", RoleType.NONE, RoleScope.INSTITUTION),
            (
                "urn:lti:instrole:ims/lis/Observer",
                RoleType.LEARNER,
                RoleScope.INSTITUTION,
            ),
            ("urn:lti:instrole:ims/lis/Other", RoleType.LEARNER, RoleScope.INSTITUTION),
            (
                "urn:lti:instrole:ims/lis/ProspectiveStudent",
                RoleType.LEARNER,
                RoleScope.INSTITUTION,
            ),
            (
                "urn:lti:instrole:ims/lis/Staff",
                RoleType.INSTRUCTOR,
                RoleScope.INSTITUTION,
            ),
            (
                "urn:lti:instrole:ims/lis/Student",
                RoleType.LEARNER,
                RoleScope.INSTITUTION,
            ),
            ("urn:lti:role:ims/lis/Administrator", RoleType.ADMIN, RoleScope.COURSE),
            (
                "urn:lti:role:ims/lis/ContentDeveloper",
                RoleType.INSTRUCTOR,
                RoleScope.COURSE,
            ),
            ("urn:lti:role:ims/lis/Instructor", RoleType.INSTRUCTOR, RoleScope.COURSE),
            ("urn:lti:role:ims/lis/Learner", RoleType.LEARNER, RoleScope.COURSE),
            (
                "urn:lti:role:ims/lis/Learner/GuestLearner",
                RoleType.LEARNER,
                RoleScope.COURSE,
            ),
            ("urn:lti:role:ims/lis/Mentor", RoleType.INSTRUCTOR, RoleScope.COURSE),
            (
                "urn:lti:role:ims/lis/TeachingAssistant",
                RoleType.INSTRUCTOR,
                RoleScope.COURSE,
            ),
            (
                "urn:lti:role:ims/lis/TeachingAssistant/Grader",
                RoleType.INSTRUCTOR,
                RoleScope.COURSE,
            ),
            (
                "urn:lti:sysrole:ims/lis/Administrator",
                RoleType.ADMIN,
                RoleScope.SYSTEM,
            ),
            ("urn:lti:sysrole:ims/lis/None", RoleType.NONE, RoleScope.SYSTEM),
            ("urn:lti:sysrole:ims/lis/SysAdmin", RoleType.ADMIN, RoleScope.SYSTEM),
            ("Administrator", RoleType.ADMIN, RoleScope.COURSE),
            ("Alumni", RoleType.LEARNER, RoleScope.COURSE),
            ("ContentDeveloper", RoleType.INSTRUCTOR, RoleScope.COURSE),
            ("Faculty", RoleType.INSTRUCTOR, RoleScope.COURSE),
            ("Guest", RoleType.LEARNER, RoleScope.COURSE),
            ("Instructor", RoleType.INSTRUCTOR, RoleScope.COURSE),
            ("Learner", RoleType.LEARNER, RoleScope.COURSE),
            ("Member", RoleType.LEARNER, RoleScope.COURSE),
            ("Mentor", RoleType.INSTRUCTOR, RoleScope.COURSE),
            ("Observer", RoleType.LEARNER, RoleScope.COURSE),
            ("Other", RoleType.LEARNER, RoleScope.COURSE),
            ("ProspectiveStudent", RoleType.LEARNER, RoleScope.COURSE),
            ("Staff", RoleType.INSTRUCTOR, RoleScope.COURSE),
            ("Student", RoleType.LEARNER, RoleScope.COURSE),
            (
                f"{_V13_PREFIX}institution/person#Administrator",
                RoleType.ADMIN,
                RoleScope.INSTITUTION,
            ),
            (
                f"{_V13_PREFIX}institution/person#Alumni",
                RoleType.LEARNER,
                RoleScope.INSTITUTION,
            ),
            (
                f"{_V13_PREFIX}institution/person#Faculty",
                RoleType.INSTRUCTOR,
                RoleScope.INSTITUTION,
            ),
            (
                f"{_V13_PREFIX}institution/person#Instructor",
                RoleType.INSTRUCTOR,
                RoleScope.INSTITUTION,
            ),
            (
                f"{_V13_PREFIX}institution/person#Learner",
                RoleType.LEARNER,
                RoleScope.INSTITUTION,
            ),
            (
                f"{_V13_PREFIX}institution/person#Staff",
                RoleType.INSTRUCTOR,
                RoleScope.INSTITUTION,
            ),
            (
                f"{_V13_PREFIX}institution/person#Student",
                RoleType.LEARNER,
                RoleScope.INSTITUTION,
            ),
            (
                f"{_V13_PREFIX}membership#Administrator",
                RoleType.ADMIN,
                RoleScope.COURSE,
            ),
            (
                f"{_V13_PREFIX}membership#ContentDeveloper",
                RoleType.INSTRUCTOR,
                RoleScope.COURSE,
            ),
            (
                f"{_V13_PREFIX}membership#Instructor",
                RoleType.INSTRUCTOR,
                RoleScope.COURSE,
            ),
            (f"{_V13_PREFIX}membership#Learner", RoleType.LEARNER, RoleScope.COURSE),
            (f"{_V13_PREFIX}membership#Member", RoleType.LEARNER, RoleScope.COURSE),
            (f"{_V13_PREFIX}membership#Mentor", RoleType.INSTRUCTOR, RoleScope.COURSE),
            (
                f"{_V13_PREFIX}membership/Instructor#TeachingAssistant",
                RoleType.INSTRUCTOR,
                RoleScope.COURSE,
            ),
            (
                f"{_V13_PREFIX}system/person#Administrator",
                RoleType.ADMIN,
                RoleScope.SYSTEM,
            ),
            (f"{_V13_PREFIX}system/person#User", RoleType.LEARNER, RoleScope.SYSTEM),
            (f"{_V13_PREFIX}system/person#None", RoleType.NONE, RoleScope.SYSTEM),
            (
                f"{_V13_PREFIX}institution/person#None",
                RoleType.NONE,
                RoleScope.INSTITUTION,
            ),
            (
                "http://purl.imsglobal.org/vocab/lti/system/person#TestUser",
                RoleType.LEARNER,
                RoleScope.SYSTEM,
            ),
        ],
    )
    def test_it(self, value, role_type, role_scope):
        lti_role = LTIRole(value=value)

        assert lti_role.type == role_type
        assert lti_role.scope == role_scope

    @pytest.mark.parametrize(
        "value,role_type",
        (
            (f"{_V13_PREFIX}membership/Learner#GuestLearner", RoleType.LEARNER),
            (f"{_V13_PREFIX}membership/Learner#Instructor", RoleType.LEARNER),
            (f"{_V13_PREFIX}membership/Instructor#Lecturer", RoleType.INSTRUCTOR),
            (f"{_V13_PREFIX}membership/WRONG", RoleType.LEARNER),
        ),
    )
    def test_parse_lti_role_v13_prefix_matches(self, value, role_type):
        # We are ignoring the subtype, the spec says:

        # LTI does not classify any of the sub-roles as a core role. Whenever a
        # platform specifies a sub-role, by best practice it should also
        # include the associated principal role.
        assert LTIRole(value=value).type == role_type

    def test_it_converts_type_to_an_enum(self):
        lti_role = LTIRole(type="admin")
        assert lti_role.type == RoleType.ADMIN

        lti_role.type = "learner"
        assert lti_role.type == RoleType.LEARNER

    def test_it_raises_LookupError_for_invalid_types(self, db_session):
        with pytest.raises(StatementError):
            db_session.add(LTIRole(type="INVALID"))
            db_session.flush()

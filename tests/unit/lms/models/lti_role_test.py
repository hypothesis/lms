import pytest
from sqlalchemy.exc import StatementError

from lms.models.lti_role import LTIRole, RoleType, _RoleParser, RoleScope


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
    def test_parse_lti_role_type_v11(self, value, role_type):
        assert RoleType.parse(value) == role_type

    _V13_PREFIX = "http://purl.imsglobal.org/vocab/lis/v2/"

    # pylint: disable=protected-access
    @pytest.mark.parametrize(
        "value,role_type", tuple(_RoleParser._V13_ROLE_MAPPINGS.items())
    )
    def test_parse_lti_role_v13_exact_matches(self, value, role_type):
        assert RoleType.parse(value) == role_type

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
        assert RoleType.parse(value) == role_type


class TestLTIRole:
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
            ("urn:lti:instrole:ims/lis/None", RoleType.LEARNER, RoleScope.INSTITUTION),
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
            ("urn:lti:sysrole:ims/lis/None", RoleType.LEARNER, RoleScope.SYSTEM),
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
                "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Administrator",
                RoleType.ADMIN,
                RoleScope.INSTITUTION,
            ),
            (
                "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Alumni",
                RoleType.LEARNER,
                RoleScope.INSTITUTION,
            ),
            (
                "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Faculty",
                RoleType.INSTRUCTOR,
                RoleScope.INSTITUTION,
            ),
            (
                "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Instructor",
                RoleType.INSTRUCTOR,
                RoleScope.INSTITUTION,
            ),
            (
                "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Learner",
                RoleType.LEARNER,
                RoleScope.INSTITUTION,
            ),
            (
                "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Staff",
                RoleType.INSTRUCTOR,
                RoleScope.INSTITUTION,
            ),
            (
                "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Student",
                RoleType.LEARNER,
                RoleScope.INSTITUTION,
            ),
            (
                "http://purl.imsglobal.org/vocab/lis/v2/membership#Administrator",
                RoleType.ADMIN,
                RoleScope.COURSE,
            ),
            (
                "http://purl.imsglobal.org/vocab/lis/v2/membership#ContentDeveloper",
                RoleType.INSTRUCTOR,
                RoleScope.COURSE,
            ),
            (
                "http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor",
                RoleType.INSTRUCTOR,
                RoleScope.COURSE,
            ),
            (
                "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner",
                RoleType.LEARNER,
                RoleScope.COURSE,
            ),
            (
                "http://purl.imsglobal.org/vocab/lis/v2/membership#Member",
                RoleType.LEARNER,
                RoleScope.COURSE,
            ),
            (
                "http://purl.imsglobal.org/vocab/lis/v2/membership#Mentor",
                RoleType.INSTRUCTOR,
                RoleScope.COURSE,
            ),
            (
                "http://purl.imsglobal.org/vocab/lis/v2/membership/Instructor#TeachingAssistant",
                RoleType.INSTRUCTOR,
                RoleScope.COURSE,
            ),
            (
                "http://purl.imsglobal.org/vocab/lis/v2/system/person#Administrator",
                RoleType.ADMIN,
                RoleScope.SYSTEM,
            ),
            (
                "http://purl.imsglobal.org/vocab/lis/v2/system/person#User",
                RoleType.LEARNER,
                RoleScope.SYSTEM,
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

    def test_it_converts_type_to_an_enum(self):
        lti_role = LTIRole(type="admin")
        assert lti_role.type == RoleType.ADMIN

        lti_role.type = "learner"
        assert lti_role.type == RoleType.LEARNER

    def test_it_raises_LookupError_for_invalid_types(self, db_session):
        with pytest.raises(StatementError):
            db_session.add(LTIRole(type="INVALID"))
            db_session.flush()

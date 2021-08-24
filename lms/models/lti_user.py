import sqlalchemy as sa

from lms.db import BASE
from lms.models import HUser
from lms.models._mixins import CreatedUpdatedMixin


class LTIUser(CreatedUpdatedMixin, BASE):
    """An LTI user."""

    __tablename__ = "lti_user"

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    user_id = sa.Column(sa.UnicodeText(), nullable=False)
    """The user_id LTI launch parameter."""

    roles = sa.Column(sa.UnicodeText(), nullable=False)
    """The user's LTI roles."""

    tool_consumer_instance_guid = sa.Column(sa.UnicodeText(), nullable=False)

    application_instance_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("application_instances.id", ondelete="cascade"),
        nullable=False,
    )
    application_instance = sa.orm.relationship("ApplicationInstance")

    display_name = sa.Column(sa.UnicodeText(), nullable=True)
    """The user's display name."""

    email = sa.Column(sa.UnicodeText(), nullable=True)
    """The user's email address."""

    @property
    def h_user(self):
        return HUser.from_lti_user(self)

    @property
    def is_instructor(self):
        """Whether this user is an instructor."""
        return any(
            role in self.roles.lower()
            for role in ("administrator", "instructor", "teachingassistant")
        )

    @property
    def is_learner(self):
        """Whether this user is a learner."""
        return "learner" in self.roles.lower()


def display_name(given_name, family_name, full_name):
    """
    Return an h-compatible display name the given name parts.

    LTI 1.1 launch requests have separate given_name (lis_person_name_given),
    family_name (lis_person_name_family) and full_name (lis_person_name_full)
    parameters. This function returns a single display name string based on
    these three separate names.
    """
    name = full_name.strip()

    if not name:
        given_name = given_name.strip()
        family_name = family_name.strip()

        name = " ".join((given_name, family_name)).strip()

    if not name:
        return "Anonymous"

    # The maximum length of an h display name.
    display_name_max_length = 30

    if len(name) <= display_name_max_length:
        return name

    return name[: display_name_max_length - 1].rstrip() + "…"

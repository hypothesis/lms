import pytest
from h_matchers import Any

from lms.models import ApplicationInstance
from tests import factories


class TestOrganization:
    def test_parent_child_relationships(self, organization, db_session):
        children = factories.Organization.create_batch(2, parent=organization)
        db_session.flush()

        assert organization.children == children
        for child in children:
            assert child.parent == organization

    def test_application_instance_relationship(
        self, organization, application_instances, db_session
    ):
        db_session.flush()

        by_id = lambda x: x.id  # noqa: E731
        assert sorted(organization.application_instances, key=by_id) == sorted(
            application_instances, key=by_id
        )
        for application_instance in application_instances:
            assert application_instance.organization == organization

    def test_deleting_orgs_does_not_delete_application_instances(
        self, organization, db_session, application_instances
    ):
        db_session.flush()
        ai_ids = [ai.id for ai in application_instances]
        for ai in application_instances:
            db_session.expunge(ai)

        db_session.delete(organization)

        found = (
            db_session.query(ApplicationInstance)
            .filter(ApplicationInstance.id.in_(ai_ids))
            .all()
        )
        assert found == Any.list.containing(
            [
                Any.instance_of(ApplicationInstance).with_attrs(
                    {"id": ai_id, "organization": None}
                )
                for ai_id in ai_ids
            ]
        )

    def test_public_id(self, organization, db_session):
        # Flush to ensure the default is applied
        db_session.flush()

        assert organization.public_id == Any.string.matching(
            r"us\.lms\.org\.[A-Za-z0-9-_]{22}"
        )

    @pytest.fixture
    def organization(self):
        return factories.Organization()

    @pytest.fixture
    def application_instances(self, organization):
        return factories.ApplicationInstance.create_batch(2, organization=organization)

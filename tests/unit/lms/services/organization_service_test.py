from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.models import Organization
from lms.services.organization import OrganizationService, service_factory
from tests import factories


class TestOrganizationService:
    @pytest.mark.usefixtures("with_matching_noise")
    def test_get_by_id(self, svc, db_session):
        org = factories.Organization()
        db_session.flush()

        assert org == svc.get_by_id(org.id)

    @pytest.mark.usefixtures("with_matching_noise")
    def test_get_by_linked_guid_matches_from_ai(self, svc):
        orgs = factories.Organization.create_batch(2)
        for org in orgs:
            factories.ApplicationInstance(
                tool_consumer_instance_guid="guid", organization=org
            )

        matches = svc.get_by_linked_guid("guid")

        assert matches == Any.list.containing(orgs).only()

    @pytest.mark.usefixtures("with_matching_noise")
    def test_get_by_linked_guid_matches_from_group_info(self, svc):
        orgs = factories.Organization.create_batch(2)
        for org in orgs:
            factories.GroupInfo(
                application_instance=factories.ApplicationInstance(
                    tool_consumer_instance_guid="guid", organization=org
                ),
                tool_consumer_instance_guid="guid",
            )

        matches = svc.get_by_linked_guid("guid")

        assert matches == Any.list.containing(orgs).only()

    def test_get_by_linked_guid_with_no_guid(self, svc):
        factories.ApplicationInstance(
            tool_consumer_instance_guid=None, organization=factories.Organization()
        )

        assert not svc.get_by_linked_guid(None)

    def test_get_by_public_id(self, svc, db_session):
        orgs = factories.Organization.create_batch(2)
        db_session.add_all(orgs)
        db_session.flush()

        result = svc.get_by_public_id(orgs[1].public_id)

        assert result == orgs[1]

    def test_auto_assign_organization_with_no_guid(self, svc, application_instance):
        application_instance.tool_consumer_instance_guid = None

        assert svc.auto_assign_organization(application_instance) is None

    @pytest.mark.parametrize(
        "org_params,name",
        (
            (None, "ai_name"),
            ({"name": None}, "ai_name"),
            ({"name": "existing"}, "existing"),
        ),
    )
    def test_auto_assign_organization_defaults_the_name(
        self, svc, application_instance, org_params, name
    ):
        # This is also a cheeky test that if there's no matching org, we
        # create a new one
        org = factories.Organization(**org_params) if org_params else None
        application_instance.organization = org

        result = svc.auto_assign_organization(application_instance)

        assert application_instance.organization == result
        if org:
            assert result == org
        else:
            # For the newly created org case, make sure we have an ID
            assert result.id

        assert result == Any.instance_of(Organization).with_attrs({"name": name})

    @pytest.mark.usefixtures("with_matching_noise")
    @pytest.mark.parametrize("matching_ais", (1, 2))
    def test_auto_assign_organization_matches(
        self, svc, application_instance, matching_ais
    ):
        # We've tested get_by_linked_guid above, so we won't retread
        orgs = factories.Organization.create_batch(matching_ais)
        for org in orgs:
            factories.ApplicationInstance(
                tool_consumer_instance_guid=application_instance.tool_consumer_instance_guid,
                organization=org,
            )

        result = svc.auto_assign_organization(application_instance)

        assert result in orgs  # You'll get one, but we don't say which
        assert application_instance.organization == result

    def test_create_organization(self, svc):
        org = svc.create_organization(name="NAME")

        assert org.name == "NAME"

    @pytest.mark.parametrize("name", (None, "NAME"))
    @pytest.mark.parametrize("enabled", (None, True, False))
    def test_update_organization(self, svc, name, enabled):
        org = svc.update_organization(
            factories.Organization(), name=name, enabled=enabled
        )

        if name:
            assert org.name == name

        if enabled is not None:
            assert org.enabled == enabled

    @pytest.mark.usefixtures("with_matching_noise")
    def test_search_by_name(self, svc):
        org = factories.Organization(name="NAME")

        assert svc.search(name="NAME") == [org]

    @pytest.fixture
    def with_matching_noise(self):
        factories.ApplicationInstance(
            tool_consumer_instance_guid="NO MATCH",
            organization=factories.Organization(),
        )

    @pytest.fixture
    def svc(self, db_session):
        return OrganizationService(db_session=db_session)

    @pytest.fixture
    def application_instance(self):
        return factories.ApplicationInstance(
            tool_consumer_instance_guid="guid", tool_consumer_instance_name="ai_name"
        )


class TestServiceFactory:
    def test_it(self, pyramid_request, OrganizationService):
        svc = service_factory(sentinel.context, pyramid_request)

        OrganizationService.assert_called_once_with(db_session=pyramid_request.db)
        assert svc == OrganizationService.return_value

    @pytest.fixture
    def OrganizationService(self, patch):
        return patch("lms.services.organization.OrganizationService")

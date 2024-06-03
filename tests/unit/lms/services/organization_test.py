from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.models import Organization
from lms.services.organization import (
    InvalidOrganizationParent,
    InvalidPublicId,
    OrganizationService,
    service_factory,
)
from tests import factories


class TestOrganizationService:
    @pytest.mark.usefixtures("with_matching_noise")
    def test_get_by_id(self, svc, db_session):
        org = factories.Organization()
        db_session.flush()

        assert org == svc.get_by_id(org.id)

    def test_get_by_public_id(self, svc, db_session):
        orgs = factories.Organization.create_batch(2)
        db_session.add_all(orgs)
        db_session.flush()

        result = svc.get_by_public_id(orgs[1].public_id)

        assert result == orgs[1]

    def test_get_by_public_id_raises_for_malformed_ids(self, svc):
        with pytest.raises(InvalidPublicId):
            svc.get_by_public_id("MISSING_PARTS")

    def test_get_hierarchy_root(self, svc, org_with_parent):
        root = svc.get_hierarchy_root(org_with_parent.id)

        assert root == org_with_parent.parent

    @pytest.mark.usefixtures("with_matching_noise")
    @pytest.mark.parametrize(
        "param,field", (("name", "name"), ("public_id", "public_id"), ("id_", "id"))
    )
    def test_search(self, svc, param, field, db_session):
        org = factories.Organization(name="NAME")
        # Ensure ids are written
        db_session.add(org)
        db_session.flush()

        assert svc.search(**{param: getattr(org, field)}) == [org]

    def test_search_limit(self, svc):
        orgs = factories.Organization.create_batch(10)

        result = svc.search(limit=5)

        assert len(result) == 5
        assert orgs == Any.list.containing(result)

    @pytest.mark.usefixtures("with_matching_noise")
    def test_search_performs_an_or_by_default(self, svc, db_session):
        orgs = factories.Organization.create_batch(2)
        # Ensure ids are written
        db_session.add_all(orgs)
        db_session.flush()

        assert (
            svc.search(name=orgs[0].name, public_id=orgs[1].public_id)
            == Any.list.containing(orgs).only()
        )

    @pytest.mark.usefixtures("with_matching_noise")
    def test_search_with_guid_matches_from_ai(self, svc):
        orgs = factories.Organization.create_batch(2)
        for org in orgs:
            factories.ApplicationInstance(
                tool_consumer_instance_guid="guid", organization=org
            )

        matches = svc.search(guid="guid")

        assert matches == Any.list.containing(orgs).only()

    @pytest.mark.usefixtures("with_matching_noise")
    def test_search_with_guid_matches_from_group_info(self, svc):
        orgs = factories.Organization.create_batch(2)
        for org in orgs:
            factories.GroupInfo(
                application_instance=factories.ApplicationInstance(
                    tool_consumer_instance_guid="guid", organization=org
                ),
                tool_consumer_instance_guid="guid",
            )

        matches = svc.search(guid="guid")

        assert matches == Any.list.containing(orgs).only()

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
            assert not result.settings.get("hypothesis", "auto_created")
            assert not application_instance.settings.get(
                "hypothesis", "auto_assigned_to_org"
            )
        else:
            # For the newly created org case, make sure we have an ID
            assert result.id
            assert result.settings.get("hypothesis", "auto_created")
            assert application_instance.settings.get(
                "hypothesis", "auto_assigned_to_org"
            )

        assert result == Any.instance_of(Organization).with_attrs({"name": name})

    @pytest.mark.usefixtures("with_matching_noise")
    @pytest.mark.parametrize("matching_ais", (1, 2))
    def test_auto_assign_organization_matches(
        self, svc, application_instance, matching_ais
    ):
        # We separately test searching by GUID, so we won't retread
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
    @pytest.mark.parametrize("notes", (None, "Some notes"))
    def test_update_organization(self, svc, name, enabled, notes):
        org = svc.update_organization(
            factories.Organization(), name=name, enabled=enabled, notes=notes
        )

        if name:
            assert org.name == name

        if notes:
            assert org.settings.get("hypothesis", "notes") == notes

        if enabled is not None:
            assert org.enabled == enabled

    def test_update_organization_set_organization(self, svc, db_session):
        parent_org = factories.Organization.create()
        org = factories.Organization.create()
        db_session.flush()

        svc.update_organization(org, parent_public_id=parent_org.public_id)

        assert org.parent_id == parent_org.id
        assert org.parent == parent_org

    def test_update_organization_blank_organization(self, svc, org_with_parent):
        svc.update_organization(org_with_parent, parent_public_id=None)

        assert org_with_parent.parent_id is None
        assert org_with_parent.parent is None

    def test_update_organization_cannot_set_self(self, svc, org_with_parent):
        with pytest.raises(InvalidOrganizationParent):
            svc.update_organization(
                org_with_parent, parent_public_id=org_with_parent.public_id
            )

    def test_update_organization_cannot_set_child(self, svc, org_with_parent):
        with pytest.raises(InvalidOrganizationParent):
            svc.update_organization(
                org_with_parent.parent, parent_public_id=org_with_parent.public_id
            )

    def test_update_organization_with_missing_parent(self, svc, org_with_parent):
        with pytest.raises(InvalidOrganizationParent):
            svc.update_organization(
                org_with_parent.parent, parent_public_id="us.lms.org.MISSING"
            )

    def test_update_organization_parent_id_missing_has_no_effect(
        self, svc, org_with_parent
    ):
        svc.update_organization(org_with_parent)

        assert org_with_parent.parent

    def test_is_member(self, svc, db_session):
        org = factories.Organization()
        ai = factories.ApplicationInstance(organization=org)
        user = factories.User()
        other_user = factories.User()
        course = factories.Course(application_instance=ai)
        factories.GroupingMembership(user=user, grouping=course)
        db_session.flush()

        assert svc.is_member(org, user)
        assert not svc.is_member(org, other_user)

    @pytest.fixture
    def org_with_parent(self, db_session):
        org_with_parent = factories.Organization.create(
            parent=factories.Organization.create()
        )
        # Flush to ensure public ids are generated
        db_session.flush()
        return org_with_parent

    @pytest.fixture
    def with_matching_noise(self):
        factories.ApplicationInstance(
            tool_consumer_instance_guid="NO MATCH",
            organization=factories.Organization(),
        )

    @pytest.fixture
    def svc(self, db_session):
        return OrganizationService(db_session=db_session, region_code="us")

    @pytest.fixture
    def application_instance(self):
        return factories.ApplicationInstance(
            tool_consumer_instance_guid="guid", tool_consumer_instance_name="ai_name"
        )


class TestServiceFactory:
    def test_it(self, pyramid_request, OrganizationService):
        svc = service_factory(sentinel.context, pyramid_request)

        OrganizationService.assert_called_once_with(
            db_session=pyramid_request.db, region_code="us"
        )
        assert svc == OrganizationService.return_value

    @pytest.fixture
    def OrganizationService(self, patch):
        return patch("lms.services.organization.OrganizationService")

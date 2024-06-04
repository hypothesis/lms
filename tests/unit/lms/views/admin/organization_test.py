from datetime import datetime
from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPNotFound

from lms.services.organization import InvalidOrganizationParent, InvalidPublicId
from lms.views.admin.organization import AdminOrganizationViews
from tests import factories
from tests.matchers import temporary_redirect_to


@pytest.mark.usefixtures("organization_service", "hubspot_service")
class TestAdminOrganizationViews:
    def test_new_organization_callback(
        self, pyramid_request, organization_service, views
    ):
        pyramid_request.POST["name"] = "NAME"

        response = views.new_organization_callback()

        organization_service.create_organization.assert_called_once_with(name="NAME")
        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.organization",
                id_=organization_service.create_organization.return_value.id,
            )
        )

    def test_new_organization_callback_invalid_payload(self, views):
        assert not views.new_organization_callback()

    def test_show_organization(
        self, pyramid_request, organization_service, views, hubspot_service
    ):
        pyramid_request.matchdict["id_"] = sentinel.id_

        response = views.show_organization()

        organization_service.get_by_id.assert_called_once_with(sentinel.id_)
        organization_service.get_hierarchy_root.assert_called_once_with(
            organization_service.get_by_id.return_value.id
        )

        assert response == {
            "org": organization_service.get_by_id.return_value,
            "hierarchy_root": organization_service.get_hierarchy_root.return_value,
            "company": hubspot_service.get_company.return_value,
            "sort_by_name": Any.callable(),
        }

    def test_show_organization_sort_by_name(self, views, pyramid_request):
        pyramid_request.matchdict["id_"] = sentinel.id_
        response = views.show_organization()
        sort_by_name = response["sort_by_name"]

        org_a = factories.Organization(name="a")
        org_b = factories.Organization(name="b")
        org_none = factories.Organization(name=None)

        results = sort_by_name([org_a, org_none, org_b])

        assert list(results) == [org_none, org_a, org_b]

    def test_show_organization_not_found(
        self, pyramid_request, organization_service, views
    ):
        pyramid_request.matchdict["id_"] = sentinel.id_
        organization_service.get_by_id.return_value = None

        with pytest.raises(HTTPNotFound):
            views.show_organization()

        organization_service.get_by_id.assert_called_once_with(sentinel.id_)

    @pytest.mark.parametrize("name", ["  ", " name"])
    @pytest.mark.parametrize("notes", ["  ", " name"])
    def test_update_organization(
        self, pyramid_request, organization_service, views, name, notes
    ):
        pyramid_request.matchdict["id_"] = sentinel.id_
        pyramid_request.params["name"] = name
        pyramid_request.params["hypothesis.notes"] = notes
        organization_service.get_by_id.return_value = factories.Organization()

        response = views.update_organization()

        organization_service.update_organization.assert_called_once_with(
            organization_service.get_by_id.return_value,
            name=name.strip() if name else "",
            notes=notes.strip() if notes else "",
        )

        assert response == Any.instance_of(HTTPFound)

    @pytest.mark.parametrize(
        "parent_public_id_param,expected",
        (
            ("  string  ", "string"),
            ("  ", None),
            ("", None),
            (None, None),
        ),
    )
    def test_move_organization(
        self,
        views,
        pyramid_request,
        organization_service,
        parent_public_id_param,
        expected,
    ):
        pyramid_request.matchdict["id_"] = sentinel.id_
        if parent_public_id_param is not None:
            pyramid_request.params["parent_public_id"] = parent_public_id_param

        response = views.move_organization()

        organization_service.get_by_id.assert_called_once_with(sentinel.id_)
        organization_service.update_organization.assert_called_once_with(
            organization_service.get_by_id.return_value, parent_public_id=expected
        )

        assert response == Any.instance_of(HTTPFound)

    @pytest.mark.parametrize("exception", (InvalidPublicId, InvalidOrganizationParent))
    def test_move_organization_errors(
        self, views, pyramid_request, organization_service, exception
    ):
        pyramid_request.matchdict["id_"] = sentinel.id_
        organization_service.update_organization.side_effect = exception

        response = views.move_organization()

        assert response == Any.instance_of(HTTPFound)

    @pytest.mark.parametrize("value,expected", [("", False), ("on", True)])
    def test_toggle_organization_enabled(
        self,
        value,
        expected,
        pyramid_request,
        organization_service,
        views,
        AuditTrailEvent,
        db_session,
    ):
        organization = factories.Organization()
        children = factories.Organization.create_batch(5, parent=organization)
        db_session.flush()  # Give orgs IDs

        pyramid_request.matchdict["id_"] = sentinel.id_
        pyramid_request.params["enabled"] = value
        organization_service.get_by_id.side_effect = [organization] + children
        organization_service.get_hierarchy_ids.return_value = [organization.id] + [
            org.id for org in children
        ]

        views.toggle_organization_enabled()

        organization_service.get_hierarchy_ids.assert_called_once_with(sentinel.id_)
        for org in [organization]:
            organization_service.get_by_id.assert_any_call(org.id)
            organization_service.update_organization.assert_any_call(
                org, enabled=expected
            )
            AuditTrailEvent.notify.assert_any_call(pyramid_request, org)

    @pytest.fixture
    def AuditTrailEvent(self, patch):
        return patch("lms.views.admin.organization.AuditTrailEvent")

    def test_search(self, pyramid_request, organization_service, views):
        pyramid_request.params["public_id"] = " PUBLIC_ID "
        pyramid_request.params["name"] = " NAME "
        pyramid_request.params["id"] = " 100 "
        pyramid_request.params["guid"] = " GUID  "

        result = views.search()

        organization_service.search.assert_called_once_with(
            name="NAME", public_id="PUBLIC_ID", id_="100", guid="GUID"
        )
        assert result == {"organizations": organization_service.search.return_value}

    def test_search_invalid(self, pyramid_request, views):
        pyramid_request.params["id"] = "not a number"

        assert not views.search()
        assert pyramid_request.session.peek_flash

    def test_blank_search(self, views, organization_service):
        views.search()

        organization_service.search.assert_called_once_with(
            name="", public_id="", id_="", guid=""
        )

    def test_search_handles_invalid_public_id(
        self, pyramid_request, organization_service, views
    ):
        organization_service.search.side_effect = InvalidPublicId
        pyramid_request.params["public_id"] = "NOT A VALID PUBLIC ID"

        result = views.search()

        assert pyramid_request.session.peek_flash("errors")
        assert result == {"organizations": []}

    @pytest.mark.usefixtures("with_valid_params_for_usage")
    @pytest.mark.parametrize(
        "form,expected_error_message",
        [
            ({"since": "invalid"}, r"^Times must be in ISO 8601 format"),
            ({"until": "invalid"}, r"^Times must be in ISO 8601 format"),
            (
                {"since": "2023-02-28T00:00:00", "until": "2023-02-27T00:00:00"},
                r"^The 'since' time must be earlier than the 'until' time\.$",
            ),
            (
                {"since": "2022-02-28T00:00:00"},
                r"Usage reports can only be generated since 2023",
            ),
        ],
    )
    def test_usage_crashes_if_you_submit_invalid_values(
        self,
        views,
        pyramid_request,
        organization_service,
        form,
        expected_error_message,
    ):
        for key in form:
            pyramid_request.POST[key] = form[key]

        with pytest.raises(HTTPBadRequest, match=expected_error_message):
            views.usage()

        organization_service.usage_report.assert_not_called()

    @pytest.mark.usefixtures("with_valid_params_for_usage")
    def test_usage_flashes_if_service_raises(self, views, organization_service):
        organization_service.usage_report.side_effect = ValueError
        since = datetime(2023, 1, 1)
        until = datetime(2023, 12, 31)

        result = views.usage()

        org = organization_service.get_by_id.return_value
        assert result == {"org": org, "since": since, "until": until, "report": []}

    @pytest.mark.usefixtures("with_valid_params_for_usage")
    def test_usage(self, organization_service, views):
        since = datetime(2023, 1, 1)
        until = datetime(2023, 12, 31)

        result = views.usage()

        organization_service.get_by_id.assert_called_once_with(sentinel.id_)
        org = organization_service.get_by_id.return_value
        organization_service.usage_report.assert_called_once_with(org, since, until)
        assert result == {
            "org": org,
            "since": since,
            "until": until,
            "report": organization_service.usage_report.return_value,
        }

    @pytest.fixture
    def with_valid_params_for_usage(self, pyramid_request):
        pyramid_request.POST["since"] = "2023-01-01"
        pyramid_request.POST["until"] = "2023-12-31"
        pyramid_request.matchdict["id_"] = sentinel.id_

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminOrganizationViews(pyramid_request)

import pytest

from lms.views.admin.application_instance.search import (
    SETTING_NAMES,
    SearchApplicationInstanceViews,
)
from tests import factories


@pytest.mark.usefixtures("application_instance_service")
class TestSearchApplicationInstanceViews:
    def test_search_start(self, views):
        assert views.search_start() == {"settings": SETTING_NAMES}

    def test_search_callback(
        self, pyramid_request, application_instance_service, views
    ):
        pyramid_request.params = pyramid_request.POST = {
            "id": "1",
            "name": "NAME",
            "consumer_key": "CONSUMER_KEY",
            "issuer": "ISSUER",
            "client_id": "CLIENT_ID",
            "deployment_id": "DEPLOYMENT_ID",
            "tool_consumer_instance_guid": "TOOL_CONSUMER_INSTANCE_GUID",
            "email": "EMAIL",
        }

        response = views.search_callback()

        application_instance_service.search.assert_called_once_with(
            id_="1",
            name="NAME",
            consumer_key="CONSUMER_KEY",
            issuer="ISSUER",
            client_id="CLIENT_ID",
            deployment_id="DEPLOYMENT_ID",
            tool_consumer_instance_guid="TOOL_CONSUMER_INSTANCE_GUID",
            email="EMAIL",
            settings=None,
        )
        assert response == {
            "instances": application_instance_service.search.return_value,
            "settings": SETTING_NAMES,
        }

    @pytest.mark.parametrize(
        "settings_key,settings_value,expected",
        (
            ("jstor.enabled", "True", {"jstor.enabled": True}),
            ("jstor.enabled", "1", {"jstor.enabled": True}),
            ("jstor.enabled", "0", {"jstor.enabled": False}),
            ("jstor.enabled", "", {"jstor.enabled": ...}),
            ("jstor.site_code", "True", {"jstor.site_code": "True"}),
        ),
    )
    def test_search_callback_with_settings(
        self,
        views,
        pyramid_request,
        application_instance_service,
        settings_key,
        settings_value,
        expected,
    ):
        group, key = settings_key.split(".")
        ai = factories.ApplicationInstance()
        ai.settings.set(group, key, "SETTING")
        application_instance_service.search.return_value = [ai]

        pyramid_request.params = pyramid_request.POST = {
            "settings_key": settings_key,
            "settings_value": settings_value,
        }

        response = views.search_callback()

        assert (
            application_instance_service.search.call_args.kwargs["settings"] == expected
        )

        assert response["instances"][0].settings_focus_value == "SETTING"

    def test_search_callback_invalid(self, views, pyramid_request):
        pyramid_request.POST = {"id": "not a number"}

        assert not views.search_callback()
        assert pyramid_request.session.peek_flash

    @pytest.fixture
    def views(self, pyramid_request):
        return SearchApplicationInstanceViews(pyramid_request)

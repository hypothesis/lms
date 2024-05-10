from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any
from requests import Request

from lms.services.exceptions import ExternalRequestError
from lms.services.vitalsource._client import (
    BookNotFound,
    VitalSourceClient,
    VitalSourceConfigurationError,
    _VSUserAuth,
)
from lms.services.vitalsource.exceptions import VitalSourceError
from tests import factories


def xml_like(body):
    return Any.string.matching(rf'^<\?xml version="1.0" encoding="utf-8"\?>\n{body}$')


class TestVitalSourceClient:
    def test_init(self):
        client = VitalSourceClient(api_key=sentinel.api_key)

        assert client._http_session.session.headers == {  # noqa: SLF001
            "X-VitalSource-API-Key": sentinel.api_key
        }

    def test_init_raises_if_launch_credentials_invalid(self):
        with pytest.raises(ValueError):
            VitalSourceClient(api_key=None)

    def test_get_book_info(self, client, http_service):
        http_service.request.return_value = factories.requests.Response(
            json_data={
                "vbid": "VBID",
                "title": "TITLE",
                "resource_links": {"cover_image": "COVER_IMAGE"},
            }
        )

        book_info = client.get_book_info("BOOK_ID")

        http_service.request.assert_called_once_with(
            "GET",
            "https://api.vitalsource.com/v4/products/BOOK_ID",
            headers={"Accept": "application/json"},
        )
        assert book_info == {
            "id": "VBID",
            "title": "TITLE",
            "cover_image": "COVER_IMAGE",
            "url": "vitalsource://book/bookID/VBID",
        }

    def test_get_table_of_contents(self, client, http_service):
        http_service.request.return_value = factories.requests.Response(
            json_data={
                "table_of_contents": [
                    {"title": "TITLE", "cfi": "CFI", "level": 1, "page": "PAGE"}
                ]
            }
        )

        book_toc = client.get_table_of_contents("BOOK_ID")

        http_service.request.assert_called_once_with(
            "GET",
            "https://api.vitalsource.com/v4/products/BOOK_ID/toc",
            headers={"Accept": "application/json"},
        )

        assert book_toc == [
            {
                "title": "TITLE",
                "cfi": "CFI",
                "level": 1,
                "page": "PAGE",
                "url": "vitalsource://book/bookID/BOOK_ID/cfi/CFI",
            }
        ]

    @pytest.mark.parametrize(
        "response,exception_class",
        (
            (
                factories.requests.Response(
                    status_code=404,
                    headers={"Content-Type": "application/json"},
                    json_data={"errors": ["Book not found"]},
                ),
                BookNotFound,
            ),
            (
                factories.requests.Response(
                    status_code=404,
                    headers={"Content-Type": "application/json"},
                    json_data={"errors": ["Product BOOK_ID not found"]},
                ),
                BookNotFound,
            ),
            (
                factories.requests.Response(
                    # We don't actually know the error code, because we didn't
                    # capture it at the time
                    status_code=500,
                    headers={"Content-Type": "application/json; charset=utf-8"},
                    json_data={"errors": ["Catalog not found"]},
                ),
                VitalSourceConfigurationError,
            ),
            (
                factories.requests.Response(
                    status_code=500,
                    headers={"Content-Type": "application/json"},
                    json_data={"errors": ["Any valid string"]},
                ),
                ExternalRequestError,
            ),
            (
                factories.requests.Response(
                    status_code=404,
                    headers={"Content-Type": "application/json"},
                    json_data="Not the expected dict",
                ),
                ExternalRequestError,
            ),
            (
                factories.requests.Response(
                    status_code=404,
                    headers={"Content-Type": "application/json"},
                    raw=b"[not valid json...",
                ),
                ExternalRequestError,
            ),
            (factories.requests.Response(status_code=400), ExternalRequestError),
            (factories.requests.Response(status_code=500), ExternalRequestError),
        ),
    )
    @pytest.mark.parametrize("method", ("get_table_of_contents", "get_book_info"))
    def test_book_method_errors(
        self, client, http_service, response, exception_class, method
    ):
        http_service.request.side_effect = ExternalRequestError(response=response)

        with pytest.raises(exception_class):
            getattr(client, method)("BOOK_ID")

    @pytest.mark.parametrize(
        "response_xml",
        (
            # There are many more attributes in real results than these, but at the
            # moment we don't really care about any of them.
            """<?xml version="1.0" encoding="UTF-8"?>
                <licenses>
                    <license imprint="IMPRINT" name="NAME"/>
                </licenses>
            """,
            """<?xml version="1.0" encoding="UTF-8"?>
                <licenses>
                    <license imprint="IMPRINT" name="NAME"/>
                    <license imprint="IMPRINT2" name="NAME2"/>
                </licenses>
            """,
        ),
    )
    def test_get_user_book_license(
        self, client, http_service, response_xml, _VSUserAuth
    ):
        http_service.request.return_value = factories.requests.Response(
            status_code=200, raw=response_xml
        )

        result = client.get_user_book_license(
            user_reference=sentinel.user_ref, book_id=sentinel.book_id
        )

        _VSUserAuth.assert_called_once_with(client, sentinel.user_ref)
        http_service.request.assert_called_once_with(
            "GET",
            "https://api.vitalsource.com/v3/licenses.xml",
            params={"sku": sentinel.book_id},
            headers={"Accept": "application/xml; charset=utf-8"},
            auth=_VSUserAuth.return_value,
        )

        # This isn't nice output, but we currently use it as a bool
        assert result == {"imprint": "IMPRINT", "name": "NAME"}

    def test_get_user_book_license_with_no_license(self, client, http_service):
        http_service.request.return_value = factories.requests.Response(
            status=200,
            raw="""<?xml version="1.0" encoding="UTF-8"?>
                <licenses>
                </licenses>
            """,
        )

        assert (
            client.get_user_book_license(
                user_reference=sentinel.user_ref, book_id=sentinel.book_id
            )
            is None
        )

    def test_get_sso_redirect(self, client, http_service, _VSUserAuth):
        http_service.request.return_value = factories.requests.Response(
            status_code=200,
            # There are many more attributes in real results than these, but
            # at the moment we only care about `auto-signin`.
            raw="""<?xml version="1.0"?>
                <redirect
                    auto-signin="http://example.com/redirect"
                    expires="2019-08-12 14:12:59 UTC"
                />
            """,
        )

        result = client.get_sso_redirect(user_reference=sentinel.user_ref, url="URL")

        _VSUserAuth.assert_called_once_with(client, sentinel.user_ref)
        http_service.request.assert_called_once_with(
            "POST",
            "https://api.vitalsource.com/v3/redirects.xml",
            data=xml_like("<redirect><destination>URL</destination></redirect>"),
            headers={
                "Accept": "application/xml; charset=utf-8",
                "Content-Type": "application/xml; charset=utf-8",
            },
            auth=_VSUserAuth.return_value,
        )

        assert result == "http://example.com/redirect"

    @pytest.mark.parametrize(
        "xml",
        (
            """<?xml version="1.0" encoding="UTF-8"?>
                <credentials>
                    <credential access-token="ACCESS_TOKEN" other="FAKE">
                    </credential>
                </credentials>
            """,
            """<?xml version="1.0" encoding="UTF-8"?>
                <credentials>
                    <credential access-token="ACCESS_TOKEN" other="FAKE">
                    </credential>
                    <credential access-token="SHOULD BE IGNORED" other="IGNORED">
                    </credential>
                </credentials>
            """,
        ),
    )
    def test_get_user_credentials(self, client, http_service, xml):
        http_service.request.return_value = factories.requests.Response(
            status_code=200, raw=xml
        )

        result = client.get_user_credentials("USER_REF")

        http_service.request.assert_called_once_with(
            "POST",
            "https://api.vitalsource.com/v3/credentials.xml",
            data=xml_like(
                '<credentials><credential reference="USER_REF"></credential></credentials>'
            ),
            headers={
                "Accept": "application/xml; charset=utf-8",
                "Content-Type": "application/xml; charset=utf-8",
            },
        )

        assert result == {"access_token": "ACCESS_TOKEN", "other": "FAKE"}

    @pytest.mark.parametrize(
        "response_xml",
        (
            # There are many more attributes in real results than these, but at the
            # moment we don't really care about any of them.
            """<?xml version="1.0" encoding="UTF-8"?>
                <credentials>
                    <error code="603" email="" message="Invalid reference value" guid="" reference="123"></error>
                </credentials>
            """,
            # This probably should raise a different error
            """<?xml version="1.0" encoding="UTF-8"?>
                <credentials>
                    <error code="650" email="" message="Malformed credentials request" guid=""></error>
                </credentials>
            """,
        ),
    )
    def test_get_user_credentials_with_no_credentials(
        self, client, http_service, response_xml
    ):
        http_service.request.return_value = factories.requests.Response(
            status_code=200, raw=response_xml
        )

        with pytest.raises(VitalSourceError) as exc:
            assert client.get_user_credentials("USER_REF")

        assert exc.value.error_code == "vitalsource_user_not_found"

    @pytest.fixture
    def client(self):
        return VitalSourceClient("api_key")

    @pytest.fixture(autouse=True)
    def http_service(self, patch):
        HTTPService = patch("lms.services.vitalsource._client.HTTPService")

        return HTTPService.return_value

    @pytest.fixture
    def _VSUserAuth(self, patch):
        return patch("lms.services.vitalsource._client._VSUserAuth")


class Test_VSUserAuth:
    def test_it(self, client):
        request = Request(headers={"Existing": "Header"})
        client.get_user_credentials.return_value = {
            "access_token": sentinel.access_token,
            "other": "IGNORED",
        }

        auth = _VSUserAuth(client, sentinel.user_reference)
        result = auth(request)

        client.get_user_credentials.assert_called_once_with(sentinel.user_reference)
        assert isinstance(result, Request)
        assert result.headers == {
            "Existing": "Header",
            "X-VitalSource-Access-Token": sentinel.access_token,
        }

    @pytest.fixture
    def client(self):
        return create_autospec(VitalSourceClient, instance=True, spec_set=True)

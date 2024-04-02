import logging
from functools import lru_cache

import xmltodict
from marshmallow import EXCLUDE, Schema, fields
from requests import JSONDecodeError, PreparedRequest
from requests.auth import AuthBase

from lms.services.exceptions import ExternalRequestError, SerializableError
from lms.services.http import HTTPService
from lms.services.vitalsource.exceptions import VitalSourceError
from lms.services.vitalsource.model import VSBookLocation
from lms.validation._base import RequestsResponseSchema

LOG = logging.getLogger(__name__)


class BookNotFound(SerializableError):
    def __init__(self, book_id):
        super().__init__(message=f"Book {book_id} not found")


class VitalSourceConfigurationError(SerializableError):
    def __init__(self, message):
        super().__init__(message=f"VitalSource is misconfigured: {message}")


class VitalSourceClient:
    """
    A client for making individual calls to VitalSource API.

    See: https://developer.vitalsource.com/hc/en-us/categories/360001974433
    """

    VS_API = "https://api.vitalsource.com"

    def __init__(self, api_key: str):
        """
        Initialise a client object.

        :param api_key: Key for VitalSource API
        :raises ValueError: If `api_key` is missing
        """
        if not api_key:
            raise ValueError("VitalSource credentials are missing")

        self._http_session = HTTPService()

        # Set headers in the session which will be passed with every request
        self._http_session.session.headers = {"X-VitalSource-API-Key": api_key}

    def get_book_info(self, book_id: str) -> dict:
        """
        Get details of a book.

        See: https://developer.vitalsource.com/hc/en-us/articles/360010967153-GET-v4-products-vbid-Title-TOC-Metadata

        :param book_id: Id of the book or VBID in VS speak
        :raises BookNotFound: If the book cannot be found
        :raises ExternalRequestError: For all other problems contacting VS
        """

        try:
            response = self._json_request("GET", f"{self.VS_API}/v4/products/{book_id}")
        except ExternalRequestError as err:
            self._handle_book_errors(book_id, err)

        book_info = _BookInfoSchema(response).parse()

        # This should be the same as `book_id` but it comes from the
        # authoritative source. This might make a difference if the VS APIs
        # normalize or redirect IDs.
        vbid = book_info["vbid"]

        return {
            "id": vbid,
            "title": book_info["title"],
            "cover_image": book_info["resource_links"]["cover_image"],
            "url": VSBookLocation(vbid).document_url,
        }

    def get_table_of_contents(self, book_id: str) -> list[dict]:
        """
        Get the table of contents for a book.

        See: https://developer.vitalsource.com/hc/en-us/articles/360010967153-GET-v4-products-vbid-Title-TOC-Metadata

        :param book_id: Id of the book or VBID in VS speak
        :raises BookNotFound: If the book cannot be found
        :raises ExternalRequestError: For all other problems contacting VS
        """

        try:
            response = self._json_request(
                "GET", f"{self.VS_API}/v4/products/{book_id}/toc"
            )
        except ExternalRequestError as err:
            self._handle_book_errors(book_id, err)

        toc = _BookTOCSchema(response).parse()["table_of_contents"]
        for chapter in toc:
            chapter["url"] = VSBookLocation(book_id, cfi=chapter["cfi"]).document_url

        return toc

    def get_user_book_license(self, user_reference, book_id) -> dict | None:
        """
        Get a user licence for a specific book (if any).

        See: https://developer.vitalsource.com/hc/en-us/articles/204332688-GET-v3-licenses-Read

        :param user_reference: String identifying the current user
        :param book_id: Id of the book or VBID, to get the license for
        """
        result = self._xml_request(
            "GET",
            f"{self.VS_API}/v3/licenses.xml",
            params={"sku": book_id},
            auth=_VSUserAuth(self, user_reference),
        )

        LOG.debug("Result of license call for %s: %s", user_reference, result)

        # The result is a list of active licenses that match the given book
        # ID/SKU.
        try:
            return self._to_camel_case(self._pick_first(result["licenses"]["license"]))
        except (KeyError, TypeError):
            return None

    def get_sso_redirect(self, user_reference, url) -> str:
        """
        Get a URL which logs in a user then redirects to a URL.

        See: https://developer.vitalsource.com/hc/en-us/articles/204317878-POST-v3-redirects-SSO-to-Bookshelf-eReader

        :param user_reference: String identifying the current user
        :param url: The URL to redirect to after login
        """
        result = self._xml_request(
            "POST",
            f"{self.VS_API}/v3/redirects.xml",
            data={"redirect": {"destination": url}},
            auth=_VSUserAuth(self, user_reference),
        )

        return result["redirect"]["@auto-signin"]

    # This is used in `_VSUserAuth` authentication mechanism below. We want to
    # cache this so that repeated calls for the same user are only issued once.
    @lru_cache(1)
    def get_user_credentials(self, user_reference: str) -> dict:
        """
        Get user credentials that can be used with user-specific queries.

        See: https://developer.vitalsource.com/hc/en-us/articles/204315388-POST-v3-credentials-Verify-Credentials

        :param user_reference: String identifying the current user
        :raises VitalSourceError: If no credentials are found for the user
        """

        result = self._xml_request(
            "POST",
            f"{self.VS_API}/v3/credentials.xml",
            data={"credentials": {"credential": {"@reference": user_reference}}},
        )

        if credentials := result["credentials"].get("credential"):
            return self._to_camel_case(self._pick_first(credentials))

        LOG.exception(
            "VitalSource user not found: %s", result["credentials"].get("error")
        )
        raise VitalSourceError(error_code="vitalsource_user_not_found")

    @classmethod
    def _handle_book_errors(cls, book_id: str, err: ExternalRequestError):
        if json_errors := cls._get_json_errors(err):
            # This isn't something we can do anything about, but we can check
            # for it. If the catalog is not initialized we get this error and
            # VS need to do "something" to configure it. This shouldn't happen
            # at random, only when onboarding new customers.
            if "Catalog not found" in json_errors:
                raise VitalSourceConfigurationError(
                    "The catalog has not been initialized"
                )

            if err.status_code == 404:
                raise BookNotFound(book_id) from err

        raise err

    @staticmethod
    def _get_json_errors(err: ExternalRequestError) -> list | None:
        if err.response.headers.get("Content-Type", "").startswith("application/json"):
            # Many errors from VitalSource say they are JSON, but don't include
            # any actual JSON data to decode
            try:
                return err.response.json().get("errors")
            except (JSONDecodeError, AttributeError):
                pass

        return None

    @staticmethod
    def _pick_first(list_or_item):
        """
        Pick the first thing if this is a list, or the whole item if not.

        Due to the nature of XML and `xmltodict`, we can't tell the
        difference between a list with a single item, or a single nested
        item. This allows us to smooth over the difference.
        """
        if isinstance(list_or_item, list):
            return list_or_item[0]

        return list_or_item

    @staticmethod
    def _to_camel_case(data: dict) -> dict:
        """
        Remove `xmltodict` specific formatting for attributes.

        This converts from things like `@attribute-name` to `attribute_name`.
        """
        return {key.lstrip("@").replace("-", "_"): value for key, value in data.items()}

    def _json_request(self, method, url):
        """
        Make a request to a VitalSource endpoint that accepts/returns JSON.

        The VitalSource API endpoints prefixed with "v4/" use JSON or XML.
        """

        # As we are using a requests Session, headers and auth etc. set in the
        # session will take effect here in addition to the values passed in.
        return self._http_session.request(
            method, url, headers={"Accept": "application/json"}
        )

    def _xml_request(self, method, url, data=None, **kwargs) -> dict:
        """
        Make a request to a VitalSource endpoint that accepts/returns XML.

        The VitalSource API endpoints prefixed with "v3/" use XML.
        """
        kwargs["headers"] = {"Accept": "application/xml; charset=utf-8"}

        if data:
            kwargs["data"] = xmltodict.unparse(data)
            kwargs["headers"]["Content-Type"] = "application/xml; charset=utf-8"

        response = self._http_session.request(method, url, **kwargs)
        return xmltodict.parse(response.text)


class _VSUserAuth(AuthBase):
    """
    A requests authentication method for user based access tokens.

    See: https://requests.readthedocs.io/en/latest/user/advanced/#custom-authentication

    Using this allows us to completely separate authentication from other
    behaviors which leads to simpler tests, and code. Authentication is also
    transparent to the caller and results can be cached.
    """

    def __init__(self, client: VitalSourceClient, user_reference: str):
        self._client = client
        self._user_reference = user_reference

    def __call__(self, request: PreparedRequest) -> PreparedRequest:
        credentials = self._client.get_user_credentials(self._user_reference)
        request.headers["X-VitalSource-Access-Token"] = credentials["access_token"]

        return request


class _BookInfoSchema(RequestsResponseSchema):
    vbid = fields.Str(required=True)
    """The primary key of the book. We refer to this as book id elsewhere."""

    title = fields.Str(required=True)
    """The title of the book."""

    class ResourceLinks(Schema):
        class Meta:
            unknown = EXCLUDE

        cover_image = fields.Str(required=True)

    resource_links = fields.Nested(ResourceLinks, required=True)


class _BookTOCSchema(RequestsResponseSchema):
    class Chapter(Schema):
        class Meta:
            unknown = EXCLUDE

        title = fields.Str(required=True)
        """Title of the chapter."""

        cfi = fields.Str(required=True)
        """A reference to the location within the book."""

        page = fields.Str(required=True)
        """The start page of the chapter."""

        level = fields.Integer()
        """The nesting depth of this entry. This is an integer >= 1."""

    table_of_contents = fields.List(fields.Nested(Chapter), required=True)

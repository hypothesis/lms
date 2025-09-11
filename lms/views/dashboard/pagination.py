import json
import logging
from types import NoneType
from typing import Any, TypeVar
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from marshmallow import ValidationError, fields, post_load, validate
from sqlalchemy import Select

from lms.js_config_types import Pagination
from lms.validation._base import PyramidRequestSchema

LOG = logging.getLogger(__name__)

T = TypeVar("T")


MAX_ITEMS_PER_PAGE = 100
"""Maximum number of items to return in paginated endpoints"""


def _get_cursor_value[T](items: list[T], cursor_columns: list) -> str:
    last_element = items[-1]
    # Get the relevant values from the last element on the page
    values = [getattr(last_element, column.key) for column in cursor_columns]
    return json.dumps(values)


def _get_next_url(current_url, cursor_value) -> str:
    """Insert or replace the `cursor` query param in `current_url`."""
    parsed_url = urlparse(current_url)
    query_params = parse_qs(parsed_url.query)

    query_params["cursor"] = [cursor_value]

    new_query_string = urlencode(query_params, doseq=True)

    return urlunparse(parsed_url._replace(query=new_query_string))


def get_page[T](
    request, items_query: Select[tuple[T, *tuple[Any]]], cursor_columns: list
) -> tuple[list[T], Pagination]:
    """Return the first page and pagination metadata from a query."""

    # If we have a cursor only fetch the elements that follow
    if cursor_values := request.parsed_params.get("cursor"):
        if cursor_values[0] is None:
            # We allow nullable column on the first column of the cursor, usually a (student, assignment...) name
            # Tweak the query as sorting/comparing by null doesn't behave nicely
            items_query = items_query.where(
                # We explicitly check for null in the first column and sort by the second
                cursor_columns[0].is_(None),
                cursor_columns[1] > cursor_values[1],
            )
        else:
            # In the non-null case we can sort by both columns
            items_query = items_query.where(
                tuple(cursor_columns) > tuple(cursor_values)  # type: ignore  # noqa: PGH003
            )

    limit = min(MAX_ITEMS_PER_PAGE, request.parsed_params["limit"])
    # Over fetch one element to check if need to calculate the next cursor
    items = request.db.scalars(items_query.limit(limit + 1)).all()
    if not items or len(items) <= limit:
        # No elements or no next page, no pagination.next
        return items, Pagination(next=None)
    items = items[0:limit]

    cursor_value = _get_cursor_value(items, cursor_columns)
    return items, Pagination(next=_get_next_url(request.url, cursor_value))


class PaginationParametersMixin(PyramidRequestSchema):
    location = "query"

    limit = fields.Integer(
        required=False, load_default=MAX_ITEMS_PER_PAGE, validate=validate.Range(min=1)
    )
    """Maximum number of items to return."""

    cursor = fields.Str()
    """Position to return elements from."""

    @post_load
    def decode_cursor(self, in_data: dict, **_kwargs) -> dict:
        cursor = in_data.get("cursor")
        if not cursor:
            return in_data

        try:
            in_data["cursor"] = json.loads(cursor)
        except ValueError as exc:
            raise ValidationError("Invalid value for pagination cursor.") from exc  # noqa: EM101, TRY003

        if not isinstance(in_data["cursor"], list) or len(in_data["cursor"]) != 2:
            raise ValidationError(  # noqa: TRY003
                "Invalid value for pagination cursor. Cursor must be a list of at least two values."  # noqa: EM101
            )
        if [type(v) for v in in_data["cursor"]] not in [[str, int], [NoneType, int]]:
            raise ValidationError(  # noqa: TRY003
                "Invalid value for pagination cursor. Cursor must be a [str | None, int] list."  # noqa: EM101
            )

        return in_data

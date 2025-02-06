import json

import pytest
from h_matchers import Any
from sqlalchemy import select

from lms.js_config_types import Pagination
from lms.models import Course, User
from lms.validation import ValidationError
from lms.views.dashboard.pagination import PaginationParametersMixin, get_page
from tests import factories


class TestGetPage:
    def test_when_no_next_page(self, pyramid_request, db_session):
        pyramid_request.parsed_params = {"limit": 100}
        courses = factories.Course.create_batch(5)
        query = select(Course).order_by(Course.id)
        db_session.flush()

        items, pagination = get_page(pyramid_request, query, (Course.id,))

        assert items == courses
        assert pagination == Pagination(next=None)

    def test_when_empty(self, pyramid_request):
        pyramid_request.parsed_params = {"limit": 100}
        query = select(Course).where(False)  # noqa: FBT003

        items, pagination = get_page(pyramid_request, query, (Course.id,))

        assert items == []
        assert pagination == Pagination(next=None)

    def test_it_calculates_next(self, pyramid_request, db_session):
        pyramid_request.parsed_params = {"limit": 1}
        courses = factories.Course.create_batch(5)
        query = select(Course).order_by(Course.id)
        db_session.flush()

        items, pagination = get_page(pyramid_request, query, (Course.id,))

        assert items == courses[0:1]
        assert pagination == Pagination(
            next=Any.url.with_query({"cursor": json.dumps([courses[0].id])})
        )

    def test_it_filters_by_cursor(self, pyramid_request, db_session):
        courses = factories.Course.create_batch(5)
        query = select(Course).order_by(Course.id)
        db_session.flush()
        pyramid_request.parsed_params = {
            "cursor": [courses[0].id, courses[0].lms_name],
            "limit": 1,
        }

        items, _ = get_page(pyramid_request, query, (Course.id, Course.lms_name))

        assert items == courses[1:2]

    def test_it_filters_by_cursor_allows_nullable(self, pyramid_request, db_session):
        students = factories.User.create_batch(5)
        students[0].display_name = None
        query = select(User).order_by(User.id)
        db_session.flush()
        pyramid_request.parsed_params = {
            "cursor": [None, students[0].id],
            "limit": 1,
        }
        items, _ = get_page(pyramid_request, query, (User.display_name, User.id))

        assert items == students[1:2]


class TestPaginationParametersMixin:
    def test_limit_default(self, pyramid_request):
        assert PaginationParametersMixin(pyramid_request).parse() == {"limit": 100}

    @pytest.mark.parametrize(
        "cursor",
        [
            pytest.param("1,", id="Not a list"),
            pytest.param("{}", id="Not a list"),
            pytest.param("[1]", id="Not a list of two elements"),
            pytest.param("[true, false]", id="Not string/integer list elements"),
        ],
    )
    def test_invalid_cursor(self, pyramid_request, cursor):
        pyramid_request.GET = {"cursor": cursor}

        with pytest.raises(ValidationError):
            PaginationParametersMixin(pyramid_request).parse()

    def test_cursor(self, pyramid_request):
        pyramid_request.GET = {"cursor": json.dumps(("VALUE", 1))}

        assert PaginationParametersMixin(pyramid_request).parse() == {
            "limit": 100,
            "cursor": ["VALUE", 1],
        }

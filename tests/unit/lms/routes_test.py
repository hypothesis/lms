import pytest
from pyramid.interfaces import IRoutesMapper
from pyramid.testing import DummyRequest


# This test does not cover all routes, only cases that have non-trivial route
# patterns.
#
# Note that the `path` test param is the path _after_ URL decoding.
# See https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/urldispatch.html#route-pattern-syntax
@pytest.mark.parametrize(
    "path,expected_route,expected_match",
    [
        (
            "/api/jstor/articles/1234",
            "jstor_api.articles.metadata",
            {"article_id": "1234"},
        ),
        (
            "/api/jstor/articles/10.123/456",
            "jstor_api.articles.metadata",
            {"article_id": "10.123/456"},
        ),
        ("/api/jstor/articles/10/456", None, None),
        (
            "/api/jstor/articles/1234/thumbnail",
            "jstor_api.articles.thumbnail",
            {"article_id": "1234"},
        ),
        (
            "/api/jstor/articles/10.123/456/thumbnail",
            "jstor_api.articles.thumbnail",
            {"article_id": "10.123/456"},
        ),
        ("/api/jstor/articles/10/456/thumbnail", None, None),
        (
            "/api/youtube/videos/456",
            "youtube_api.videos",
            {"video_id": "456"},
        ),
    ],
)
def test_request_matches_expected_route(
    pyramid_config, path, expected_route, expected_match
):
    route_mapper = pyramid_config.registry.queryUtility(IRoutesMapper)
    request = DummyRequest(path=path)

    route = route_mapper(request)
    route_name = route["route"].name if route["route"] else None

    assert route_name == expected_route
    assert route["match"] == expected_match

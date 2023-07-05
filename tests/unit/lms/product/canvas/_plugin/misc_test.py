from unittest.mock import sentinel

import pytest

from lms.product.canvas._plugin.misc import CanvasMiscPlugin


class TestCanvasMiscPlugin:
    def test_get_document_url(self, plugin, pyramid_request):
        assert not plugin.get_document_url(
            pyramid_request, sentinel.assignment, sentinel.historical_assignment
        )

    @pytest.mark.parametrize(
        "url,expected",
        (
            (None, None),
            # URL encoded paths
            (
                "https%3A%2F%2Fexample.com%2Fpath%3Fparam%3Dvalue",
                "https://example.com/path?param=value",
            ),
            (
                "http%3A%2F%2Fexample.com%2Fpath%3Fparam%3Dvalue",
                "http://example.com/path?param=value",
            ),
            (
                "HTTP%3a%2F%2Fexample.com%2Fpath%3Fparam%3Dvalue",
                "HTTP://example.com/path?param=value",
            ),
            (
                "canvas%3A%2F%2Ffile%2Fcourse_id%2FCOURSE_ID%2Ffile_if%2FFILE_ID",
                "canvas://file/course_id/COURSE_ID/file_if/FILE_ID",
            ),
            (
                "jstor%3A%2F%2FDOI",
                "jstor://DOI",
            ),
            (
                "vitalsource%3A%2F%2Fbook%2FbookID%2FL-999-70469%2Fcfi%2F%2F6%2F8",
                "vitalsource://book/bookID/L-999-70469/cfi//6/8",
            ),
            # Non-URL encoded paths
            (
                "https://example.com/path?param=value",
                "https://example.com/path?param=value",
            ),
            (
                "http://example.com/path?param=%25foo%25",
                "http://example.com/path?param=%25foo%25",
            ),
            (
                "canvas://file/course_id/COURSE_ID/file_if/FILE_ID",
                "canvas://file/course_id/COURSE_ID/file_if/FILE_ID",
            ),
            ("jstor://DOI", "jstor://DOI"),
            (
                "vitalsource://book/bookID/L-999-70469/cfi//6/8",
                "vitalsource://book/bookID/L-999-70469/cfi//6/8",
            ),
            # Unknown but valid (RFC3986) schemas get decoded
            (
                "j5-tor.r%3A%2F%2FDOI",
                "j5-tor.r://DOI",
            ),
            # Invalid schemas don't get decoded
            (
                "1stor%3A%2F%2FDOI",
                "1stor%3A%2F%2FDOI",
            ),
        ),
    )
    def test_get_document_url_with_deeplinking_url(
        self, plugin, pyramid_request, url, expected
    ):
        if url:
            pyramid_request.params["url"] = url

        assert (
            plugin.get_document_url(
                pyramid_request, sentinel.assignment, sentinel.historical_assignment
            )
            == expected
        )

    def test_get_document_url_with_canvas_files(self, plugin, pyramid_request):
        pyramid_request.params["canvas_file"] = "any"
        pyramid_request.params["file_id"] = "FILE_ID"
        pyramid_request.lti_params["custom_canvas_course_id"] = "COURSE_ID"

        assert (
            plugin.get_document_url(
                pyramid_request, sentinel.assignment, sentinel.historical_assignment
            )
            == "canvas://file/course/COURSE_ID/file_id/FILE_ID"
        )

    @pytest.mark.parametrize("cfi", (None, sentinel.cfi))
    def test_get_document_url_with_legacy_vitalsource_book(
        self, plugin, pyramid_request, VSBookLocation, cfi
    ):
        pyramid_request.params["vitalsource_book"] = "any"
        pyramid_request.params["book_id"] = sentinel.book_id
        if cfi:
            pyramid_request.params["cfi"] = cfi

        result = plugin.get_document_url(
            pyramid_request, sentinel.assignment, sentinel.historical_assignment
        )

        VSBookLocation.assert_called_once_with(book_id=sentinel.book_id, cfi=cfi)
        assert result == VSBookLocation.return_value.document_url

    def test_get_deeplinking_launch_url(self, plugin, pyramid_request):
        config = {"param": "value"}

        assert (
            plugin.get_deeplinking_launch_url(pyramid_request, config)
            == "http://example.com/lti_launches?param=value"
        )

    def test_factory(self, pyramid_request):
        plugin = CanvasMiscPlugin.factory(sentinel.context, pyramid_request)
        assert isinstance(plugin, CanvasMiscPlugin)

    @pytest.fixture
    def plugin(self):
        return CanvasMiscPlugin()

    @pytest.fixture
    def VSBookLocation(self, patch):
        return patch("lms.product.canvas._plugin.misc.VSBookLocation")

from lms.views import favicon


def test_favicon(pyramid_request):
    response = favicon.favicon(pyramid_request)

    assert response.status_int == 200
    assert response.headers["Content-Type"] in (
        # Python's default mime type for .ico files.
        "image/vnd.microsoft.icon",
        # Non-standard mime type that some systems will report.
        # See https://en.wikipedia.org/wiki/Favicon#Standardization
        "image/x-icon",
    )

    # Avoid resource leak warning
    response.app_iter.close()

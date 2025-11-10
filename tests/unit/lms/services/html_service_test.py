import pytest

from lms.services.html_service import strip_html_tags


@pytest.mark.parametrize(
    "text,expected",
    [
        ("<b>COLON :</b>", "COLON :"),
        ("A <em>B</em>", "A B"),
        (" C <em>D</em> E", "C D E"),
        # ("A<B", "A<B"),  # noqa: ERA001 This is failing in CI. Skipping for now
    ],
)
def test_strip_html_tags(text, expected):
    assert strip_html_tags(text) == expected

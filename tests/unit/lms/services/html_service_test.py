import pytest

from lms.services.html_service import strip_html_tags


@pytest.mark.parametrize(
    "text,expected,tags_to_new_line",
    [
        ("<b>COLON :</b>", "COLON :", None),
        ("A <em>B</em>", "A B", None),
        (" C <em>D</em> E", "C D E", None),
        ("A<B", "A<B", None),
        ("<p>PARAGRAPH</p>OTHER", "PARAGRAPH\nOTHER", ["p"]),
        ("<p>PARAGRAPH</p>OTHER<br/>ANOTHER", "PARAGRAPH\nOTHER\nANOTHER", ["p", "br"]),
        ("<div>1\n <p>2</p>\n<p>3 </p>\n</div>", "1\n2\n3", ["p", "br"]),
    ],
)
def test_strip_html_tags(text, expected, tags_to_new_line):
    assert strip_html_tags(text, tags_to_new_line) == expected

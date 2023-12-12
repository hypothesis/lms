import re
from html.parser import HTMLParser


class WhiteSpaceHTMLParser(HTMLParser):  # pylint:disable=abstract-method
    def __init__(self, tags_to_newline):
        super().__init__()
        self._chunks = []
        self._tags_to_new_line = tags_to_newline or []

    def handle_data(self, data):
        self._chunks.append(data)

    def handle_endtag(self, tag):
        if tag in self._tags_to_new_line:
            self._chunks.append("\n")

    def get_text(self) -> str:
        joined = "".join(self._chunks).strip()
        # Remove any superfluous white space added after new lines
        return re.sub(r"\n\s", "\n", joined)


def strip_html_tags(html: str, tags_to_newline=None) -> str:
    parser = WhiteSpaceHTMLParser(tags_to_newline)
    parser.feed(html)
    parser.close()

    return parser.get_text()

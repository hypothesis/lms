import re
from html.parser import HTMLParser


class WhiteSpaceHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._chunks = []

    def handle_data(self, data):
        self._chunks.append(data)

    def get_text(self) -> str:
        joined = "".join(self._chunks).strip()
        # Remove any superfluous white space added after new lines
        return re.sub(r"\n\s", "\n", joined)


def strip_html_tags(html: str) -> str:
    parser = WhiteSpaceHTMLParser()
    parser.feed(html)
    parser.close()
    return parser.get_text()

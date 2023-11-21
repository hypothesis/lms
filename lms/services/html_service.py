from html.parser import HTMLParser


def strip_html_tags(html: str) -> str:
    """Get plain text from a string which may contain HTML tags."""

    # Extract text nodes using HTMLParser. We rely on it being tolerant of
    # invalid markup.
    chunks = []
    parser = HTMLParser()
    parser.handle_data = chunks.append
    parser.feed(html)
    parser.close()

    # Strip leading/trailing whitespace and duplicate spaces
    return " ".join("".join(chunks).split())

"""Open LTI tool embeds in a Canvas page top-level in Canvas."""

import re
from html import escape, unescape
from urllib.parse import urlparse

# An <iframe ...> tag, optionally followed by its closing tag.
IFRAME_RE = re.compile(r"<iframe\b[^>]*>\s*(?:</iframe\s*>)?", re.IGNORECASE)
SRC_RE = re.compile(r"""\bsrc\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.IGNORECASE)

LINK_TEXT = "Open this embedded content in Canvas"


def open_lti_embeds_in_canvas(body: str | None) -> str | None:
    """
    Replace Canvas LTI tool embeds in `body` with links that open in Canvas.

    Canvas embeds LTI tools (Studio, Zoom, ...) as iframes pointing at its
    `external_tools/retrieve` route. That route only works inside Canvas: it
    needs the Canvas session cookie and its `frame-ancestors` CSP only allows
    Canvas itself to frame it, so proxied through Via the iframe is a login
    page or a blank frame. A link lets the user open it in Canvas directly.
    """
    if not body:
        return body

    return IFRAME_RE.sub(_replace_lti_embed, body)


def _replace_lti_embed(match: re.Match) -> str:
    src_match = SRC_RE.search(match.group(0))
    if not src_match:
        return match.group(0)

    url = unescape(src_match.group(1) or src_match.group(2) or "")
    parsed = urlparse(url)
    # Only an absolute http(s) URL: a `javascript:` one would run on click.
    if parsed.scheme not in ("http", "https") or not parsed.path.endswith(
        "/external_tools/retrieve"
    ):
        return match.group(0)

    # Escaped again on the way out: a single-quoted src may hold a `"`.
    href = escape(url, quote=True)
    return f'<p><a href="{href}" target="_blank" rel="noopener">{LINK_TEXT}</a></p>'

"""
Maintain Assignment.document_uri: the h document identity of an assignment.

h resolves documents by URI (``Document.find_by_uris``), so anything we tell h
about an assignment's document — e.g. a Hide & Reveal checkpoint — must use
the URI the Hypothesis client uses as the document's *identity*, not our
internal ``document_url``. That identity depends on the content type:

* http(s) URLs: the client annotates the URL itself (Via preserves it), so
  ``document_url`` is already the right URI.

* LMS files (Canvas, Blackboard, D2L, Moodle) and JSTOR: the viewer loads the
  file from a per-launch download URL (usually signed and short-lived), so no
  URL is a usable identity. These are all PDFs, and the client attaches a
  stable ``urn:x-pdf:<fingerprint>`` claim computed from the file's bytes —
  we compute the same fingerprint server-side and use that.

* Canvas pages: the client annotates the canonical page URL that our page
  proxy injects as ``<link rel="canonical">``.

* VitalSource: the client uses a stable per-book URL
  (``VitalSourceContentIntegration.uri()`` in the client).

* Canvas Studio: Via's video player saves the annotations with the video's
  canonical REST URL (``CanvasStudioService.get_canonical_video_url()``).

* Moodle pages: the proxy's canonical link has no scheme, so the browser
  resolves the href against the *viahtml* URL of the proxied page.

`initial_document_uri` covers the cases derivable from ``document_url`` alone
and is re-applied on every launch, because the page cases resolve their ids
through the launch's course (see below); the PDF fingerprint needs the file's
bytes and is filled in lazily by `ensure_checkpoint_fingerprint`.
"""

import hashlib
import logging
import re
from urllib.parse import quote_plus, urlparse

from lms.document_url_regex import (
    BLACKBOARD_FILE,
    CANVAS_FILE,
    CANVAS_PAGE,
    D2L_FILE,
    MOODLE_FILE,
    MOODLE_PAGE,
)
from lms.models import Assignment, Course
from lms.services.canvas import CanvasService
from lms.services.d2l_api import D2LAPIClient
from lms.services.jstor.service import JSTORService
from lms.services.moodle import MoodleAPIClient
from lms.services.vitalsource.model import VSBookLocation
from lms.services.youtube import YouTubeService, video_id_from_url

LOG = logging.getLogger(__name__)

#: Content annotated at its own URL: document_url is already the h identity.
_HTTP_URL_REGEX = re.compile(r"^https?://", re.IGNORECASE)

# Keep in sync with CanvasStudioService.media_id()'s parsing.
_CANVAS_STUDIO_REGEX = re.compile(r"canvas-studio:\/\/media\/(?P<media_id>.+)")


def initial_document_uri(  # noqa: PLR0911
    request, document_url: str, course: Course
) -> str | None:
    """
    Return the h document URI derivable from `document_url`, or None.

    None means the identity can't be derived (yet): file content needs its PDF
    fingerprint computed from the file's bytes (see
    `ensure_checkpoint_fingerprint`), pages in a copied course can't be
    resolved until the course-copy mapping is stored, and some content types
    aren't supported yet.

    `course` is the course of the *current* launch, not necessarily the one the
    assignment was configured in: the page cases below resolve their ids
    through it so a copied course derives the identity the client will use.
    """
    application_instance = course.application_instance

    if _HTTP_URL_REGEX.match(document_url):
        if (video_id := video_id_from_url(document_url)) and request.find_service(
            iface=YouTubeService
        ).enabled:
            # Via's YouTube player canonicalizes the video URL before the
            # client annotates it (canonical_video_url() in via), so e.g. a
            # youtu.be/X document_url isn't what the annotations get.
            return f"https://www.youtube.com/watch?v={quote_plus(video_id)}"
        return document_url

    if match := CANVAS_PAGE.search(document_url):
        return _canvas_page_uri(course, match)

    if document_url.startswith("vitalsource://"):
        try:
            book_id = VSBookLocation.from_document_url(document_url).book_id
        except ValueError:
            return None
        # The same URL as the client's VitalSourceContentIntegration.uri().
        return f"https://bookshelf.vitalsource.com/reader/books/{book_id}"

    if match := _CANVAS_STUDIO_REGEX.search(document_url):
        # The same URL as CanvasStudioService.get_canonical_video_url(),
        # which Via's video player saves with the annotations.
        domain = application_instance.settings.get("canvas_studio", "domain")
        if not domain:
            return None
        return f"https://{domain}/api/public/v1/media/{match['media_id']}"

    if match := MOODLE_PAGE.search(document_url):
        return _moodle_page_uri(request, course, match)

    # LMS files and jstor:// are PDFs: nothing derivable from the URL — their
    # fingerprint is computed at launch (see ensure_checkpoint_fingerprint).
    return None


def _canvas_page_uri(course: Course, match: re.Match) -> str | None:
    """
    Return the h identity of a Canvas page, or None if it can't be derived yet.

    The same URL as CanvasPage.canonical_url(), which our page proxy injects
    as <link rel="canonical"> and the client uses as the URI.

    Both ids are resolved the way `canvas_api.pages.via_url` resolves the ones
    it passes to the proxy: the *current* course's Canvas id, and the page id
    mapped for course copy (`get_mapped_page_id` returns the original when
    there's no mapping).
    """
    course_id = _canvas_course_id(course, match)
    page_id = course.get_mapped_page_id(match["page_id"])

    if _in_unmapped_copied_course(course_id, page_id, match):
        return None

    lms_host = course.application_instance.lms_host()
    return f"https://{lms_host}/courses/{course_id}/pages/{page_id}"


def _canvas_course_id(course: Course, match: re.Match) -> str:
    """
    Return the *current* course's Canvas id.

    `extra["canvas"]` is only written when a course row is first created (see
    CourseService.get_from_launch), so courses that predate it don't have it.
    Fall back to the id in document_url rather than raising on a launch: it's
    the right one outside a course copy anyway.
    """
    return (
        course.extra.get("canvas", {}).get("custom_canvas_course_id")
        or match["course_id"]
    )


def _in_unmapped_copied_course(current_course_id, page_id, match: re.Match) -> bool:
    """
    Return whether `match` is a page in a copied course with no mapping yet.

    A course id different from document_url's means a copied course, and an
    unmapped page id (`get_mapped_page_id` returns the original when there's
    no mapping) means the `*_api.pages.via_url` view — which the frontend only
    calls after the launch response — hasn't stored the mapping yet. Deriving
    now would produce the *source* course's URL — an identity the client never
    uses — and sync an orphan checkpoint to h keyed by it. Better to leave the
    identity unresolved: the next launch, with the mapping stored, derives the
    right one.
    """
    return current_course_id != match["course_id"] and page_id == match["page_id"]


def _moodle_page_uri(request, course: Course, match: re.Match) -> str | None:
    """
    Return the h identity of a Moodle page, or None if it can't be derived yet.

    Same course-copy resolution as `_canvas_page_uri`, including skipping an
    unmapped copied course (the same copy detection as
    `moodle_api.pages.via_url`, which stores the mapping).
    """
    via_html_url = request.registry.settings.get("via_html_url")
    if not via_html_url:
        # Without knowing viahtml's public URL we'd derive an identity the
        # client never uses; leave it unresolved instead.
        LOG.warning("VIA_HTML_URL isn't set: can't resolve Moodle page identities")
        return None

    page_id = course.get_mapped_page_id(match["page_id"])

    if _in_unmapped_copied_course(course.lms_id, page_id, match):
        return None

    canonical_href = (
        f"{course.application_instance.lms_host()}/mod/page/view.php?id={page_id}"
    )
    browser_url = f"{via_html_url}{request.route_url('moodle_api.pages.proxy')}"

    return f"{browser_url.rsplit('/', 1)[0]}/{canonical_href}"


def ensure_checkpoint_fingerprint(request, assignment: Assignment, course: Course):
    """
    Fill in document_uri for a Hide & Reveal file assignment.

    File content is identified by its PDF fingerprint, which needs the file's
    bytes rather than just its URL.

    Runs for whoever launches: the file is fetched with the launching user's own
    credentials, so anyone who can view the document can be fingerprinted from
    it, and students launch first most of the time.

    Best-effort: any failure (expired API token, unreachable file...) is
    logged and swallowed — a launch must never break over this. Until the
    fingerprint is stored the checkpoint sync degrades to being skipped.
    """
    if assignment.document_uri:
        return

    try:
        pdf = _download_file_content(request, assignment, course)
    except Exception:
        LOG.exception(
            "Couldn't compute the checkpoint PDF fingerprint for assignment %s",
            assignment.id,
        )
        return

    if pdf is not None:
        assignment.document_uri = f"urn:x-pdf:{pdf_fingerprint(pdf)}"


def _download_file_content(request, assignment: Assignment, course: Course):  # noqa: PLR0911
    """
    Download the assignment's file content, or return None.

    None means document_url isn't LMS file content. Each branch resolves the
    download URL the same way the LMS's files.py::via_url view does for the
    viewer, minus the course-copy repair fallbacks (we only use already-stored
    mappings: this is best-effort and re-runs on every launch until it works).
    """
    document_url = assignment.document_url
    http = request.find_service(name="http")

    if match := CANVAS_FILE.search(document_url):
        public_url = request.find_service(CanvasService).public_url_for_file(
            assignment, match["file_id"], _canvas_course_id(course, match)
        )
        return http.get(public_url).content

    if match := BLACKBOARD_FILE.search(document_url):
        public_url = request.find_service(name="blackboard_api_client").public_url(
            course.lms_id, course.get_mapped_file_id(match["file_id"])
        )
        return http.get(public_url).content

    if match := D2L_FILE.search(document_url):
        public_url = request.find_service(D2LAPIClient).public_url(
            course.lms_id, course.get_mapped_file_id(match["file_id"])
        )
        access_token = request.find_service(name="oauth2_token").get().access_token
        return http.get(
            public_url, headers={"Authorization": f"Bearer {access_token}"}
        ).content

    if match := MOODLE_FILE.search(document_url):
        file_url = course.get_mapped_file_id(match["url"])
        if urlparse(file_url).hostname != course.application_instance.lms_host():
            LOG.warning(
                "Not fingerprinting assignment %s: its Moodle file URL's host"
                " isn't the application instance's LMS host",
                assignment.id,
            )
            return None
        token = request.find_service(MoodleAPIClient).token
        return http.get(file_url, params={"token": token}).content

    if document_url.startswith("jstor://"):
        jstor = request.find_service(iface=JSTORService)
        if not jstor.enabled:
            return None
        return http.get(jstor.public_url(document_url)).content

    return None


# The fingerprint algorithm below matches the `fingerprints` getter in the
# PDF.js build bundled in Via (via/static/vendor/pdfjs-2/build/pdf.worker.js),
# which is what the client reads to build its urn:x-pdf: claims.

_FINGERPRINT_FIRST_BYTES = 1024
_EMPTY_ID = b"\x00" * 16

#: A PDF trailer /ID array: two strings, each either hex (<...>) or literal
#: ((...) with backslash escapes). We only need the first (the "original" ID).
_PDF_ID_REGEX = re.compile(
    rb"/ID\s*\[\s*(?:<(?P<hex>[0-9A-Fa-f\s]*)>|\((?P<literal>(?:\\.|[^\\)])*)\))"
)


def pdf_fingerprint(pdf: bytes) -> str:
    """
    Return PDF.js's fingerprint for `pdf`.

    This is the value the client puts in annotations' urn:x-pdf:<fingerprint>
    document claims: the hex of the PDF trailer's original /ID when present
    (and not empty/zeroed), else the MD5 of the first 1024 bytes.
    """
    if original_id := _pdf_original_id(pdf):
        return original_id.hex()
    return hashlib.md5(pdf[:_FINGERPRINT_FIRST_BYTES]).hexdigest()  # noqa: S324


def _pdf_original_id(pdf: bytes) -> bytes | None:
    """Return the original (first) /ID string of `pdf`'s latest trailer."""
    matches = list(_PDF_ID_REGEX.finditer(pdf))
    if not matches:
        return None

    # Incremental updates append a new trailer at the end of the file, and
    # PDF.js reads the latest one — so take the last /ID in the file. (The
    # original ID is required by spec to be the same in every trailer anyway.)
    match = matches[-1]

    if (hex_id := match["hex"]) is not None:
        # Whitespace is allowed anywhere inside a PDF hex string.
        hex_str = re.sub(r"\s", "", hex_id.decode("ascii"))
        if len(hex_str) % 2:
            # Per PDF spec, a hex string with an odd number of digits gets a
            # trailing zero appended.
            hex_str += "0"
        try:
            original_id = bytes.fromhex(hex_str)
        except ValueError:  # pragma: no cover
            # Unreachable: the /ID hex group is [0-9A-Fa-f\s]* and we've
            # stripped whitespace and padded to even length, so fromhex can't
            # fail. Kept as a defensive guard on the low-level decode.
            return None
    else:
        original_id = _decode_pdf_literal(match["literal"])

    # Same validation as PDF.js: a missing, empty or all-zeroes ID falls back
    # to the MD5 fingerprint.
    if original_id and original_id != _EMPTY_ID:
        return original_id
    return None


_LITERAL_ESCAPES = {
    ord("n"): b"\n",
    ord("r"): b"\r",
    ord("t"): b"\t",
    ord("b"): b"\b",
    ord("f"): b"\f",
    ord("("): b"(",
    ord(")"): b")",
    ord("\\"): b"\\",
}


def _decode_pdf_literal(data: bytes) -> bytes:
    """Decode a PDF literal string's backslash escapes."""
    out = bytearray()
    i = 0
    while i < len(data):
        byte = data[i]
        if byte != ord("\\"):
            out.append(byte)
            i += 1
            continue

        i += 1
        if i >= len(data):
            break
        escaped = data[i]

        if escaped in _LITERAL_ESCAPES:
            out += _LITERAL_ESCAPES[escaped]
            i += 1
        elif ord("0") <= escaped <= ord("7"):
            # Octal escape: up to three octal digits.
            digits = bytearray()
            while len(digits) < 3 and i < len(data) and ord("0") <= data[i] <= ord("7"):
                digits.append(data[i])
                i += 1
            out.append(int(digits, 8) & 0xFF)
        else:
            # An unknown escape means the backslash is ignored.
            out.append(escaped)
            i += 1

    return bytes(out)

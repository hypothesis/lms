"""Patterns for the custom `<product>://` URLs we store as an assignment's document_url.

Shared by the `views.api.*` views that resolve content for the viewer and by
`services.document_uri`, which derives the document's identity in h from the
same URLs.
"""

import re

#: canvas://file/course/COURSE_ID/file_id/FILE_ID
CANVAS_FILE = re.compile(
    r"canvas:\/\/file\/course\/(?P<course_id>[^\/]*)\/file_id\/(?P<file_id>[^\/]*)"
)

#: canvas://page/course/COURSE_ID/page_id/PAGE_ID
CANVAS_PAGE = re.compile(
    r"canvas:\/\/page\/course\/(?P<course_id>[^\/]*)\/page_id\/(?P<page_id>[^\/]*)"
)

#: blackboard://content-resource/FILE_ID/
BLACKBOARD_FILE = re.compile(r"blackboard:\/\/content-resource\/(?P<file_id>[^\/]*)\/")

#: d2l://file/course/COURSE_ID/file_id/FILE_ID/
D2L_FILE = re.compile(
    r"d2l:\/\/file\/course\/(?P<course_id>[^\/]*)\/file_id\/(?P<file_id>[^\/]*)\/"
)

#: moodle://file/course/COURSE_ID/url/URL
MOODLE_FILE = re.compile(
    r"moodle:\/\/file\/course\/(?P<course_id>[^\/]*)\/url\/(?P<url>.*)"
)

#: moodle://page/course/COURSE_ID/page_id/PAGE_ID
MOODLE_PAGE = re.compile(
    r"moodle:\/\/page\/course\/(?P<course_id>[^\/]*)\/page_id\/(?P<page_id>[^\/]*)"
)

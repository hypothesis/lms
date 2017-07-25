# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import urllib


from lti.util import pdf


def pack_state(data):
    """Return the given data dict as a URL-quoted JSON string."""
    return urllib.quote(json.dumps(data))


def unpack_state(url_quoted_json_string):
    """
    Return the given URL-quoted JSON string as a normal dict.

    This is the reverse of ``pack_state()`` above.

    ``url_quoted_json_string`` is a URL-quoted JSON string like
    ``pack_state()`` returns::

        '%7B%22foo%22%3A%20%22bar%22 ... %7D'

    This URL-unquotes to a normal JSON string like::

        '{"foo": "bar", ...}'

    And this function then returns that JSON as a dict::

        {
            'foo': 'bar',
            ...
        }

    """
    return json.loads(urllib.unquote(url_quoted_json_string))


__all__ = (
    'pdf',
    'unpack_state',
)

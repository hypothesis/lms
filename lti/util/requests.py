# -*- coding: utf-8 -*-

"""Utility functions for working with the Pyramid request."""

from __future__ import unicode_literals

import urlparse

from lti import constants


def capture_post_data(request):
    post = request.POST
    return {
        constants.OAUTH_CONSUMER_KEY: post.get(constants.OAUTH_CONSUMER_KEY),
        constants.CUSTOM_CANVAS_USER_ID: post.get(constants.CUSTOM_CANVAS_USER_ID),
        constants.CUSTOM_CANVAS_COURSE_ID: post.get(constants.CUSTOM_CANVAS_COURSE_ID),
        constants.CUSTOM_CANVAS_ASSIGNMENT_ID: post.get(constants.CUSTOM_CANVAS_ASSIGNMENT_ID),
        constants.EXT_CONTENT_RETURN_TYPES: post.get(constants.EXT_CONTENT_RETURN_TYPES),
        constants.EXT_CONTENT_RETURN_URL: post.get(constants.EXT_CONTENT_RETURN_URL),
        constants.LIS_OUTCOME_SERVICE_URL: post.get(constants.LIS_OUTCOME_SERVICE_URL),
        constants.LIS_RESULT_SOURCEDID: post.get(constants.LIS_RESULT_SOURCEDID),
    }


def get_query_param(request, key):
    """
    Return the given ``key``'s value from the given ``request``'s query string.

    If ``key`` appears multiple times in ``request``'s query string then return
    just the first value.

    If ``key`` doesn't appear in ``request``'s query string then return
    ``None``.

    """
    return (urlparse.parse_qs(request.query_string).get(key, [None]))[0]


def get_post_or_query_param(request, key):
    """
    Return ``key``'s value from ``request``'s query string or POST body.

    If there's a value for ``key`` in ``request``'s query param then return
    that value, for any ``key``.

    Otherwise, if ``key`` is one of the whitelisted keys that
    :py:func:`capture_post_data` returns, then if there's a value for ``key``
    in ``request``'s body then return that value.

    Otherwise return ``None``.

    """
    return get_query_param(request, key) or capture_post_data(request).get(key)

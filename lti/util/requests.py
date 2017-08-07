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
    query = urlparse.parse_qs(request.query_string)
    if key in query:
        return query[key][0]
    return None


def get_post_or_query_param(request, key):

    def get_post_param(request, key):
        post_data = capture_post_data(request)
        if key in post_data:
            return post_data[key]
        return None

    value = get_query_param(request, key)
    if value is not None:
        ret = value
    else:
        value = get_post_param(request, key)
        ret = value
    return ret

# -*- coding: utf-8 -*-

"""Utility functions for working with the Pyramid request."""

from __future__ import unicode_literals

from lti import constants


def capture_post_data(request):
    ret = {}
    for key in [
        constants.OAUTH_CONSUMER_KEY,
        constants.CUSTOM_CANVAS_USER_ID,
        constants.CUSTOM_CANVAS_COURSE_ID,
        constants.CUSTOM_CANVAS_ASSIGNMENT_ID,
        constants.EXT_CONTENT_RETURN_TYPES,
        constants.EXT_CONTENT_RETURN_URL,
        constants.LIS_OUTCOME_SERVICE_URL,
        constants.LIS_RESULT_SOURCEDID,
    ]:
        if key in request.POST.keys():
            ret[key] = request.POST[key]
        else:
            ret[key] = None
    return ret

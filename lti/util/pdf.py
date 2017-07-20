# -*- coding: utf-8 -*-
"""Utility functions related to PDF files."""

from __future__ import unicode_literals

import re

from lti import constants


def get_fingerprint(hash_):
    """
    We need the fingerprint to query for annotations on the submission page.

    NB: PDFJS always reports fingerpints with lowercase letters and that's required for a Hypothesis lookup,
    even when the fingerprint found in the doc uses uppercase!
    """
    file_ = open('%s/%s.pdf' % (constants.FILES_PATH, hash_), 'rb')
    text = file_.read()
    matches = re.findall(r'ID\s*\[\s*<(\w+)>', text)
    file_.close()
    if matches:
        return matches[0].lower()

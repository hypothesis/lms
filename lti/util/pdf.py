# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re

from lti import constants


"""Utility functions related to PDF files."""


def get_fingerprint(hash):
    """
    We need the fingerprint to query for annotations on the submission page.

    NB: PDFJS always reports fingerpints with lowercase letters and that's required for a Hypothesis lookup,
    even when the fingerprint found in the doc uses uppercase!
    """
    f = open('%s/%s.pdf' % (constants.FILES_PATH, hash), 'rb')
    s = f.read()
    m = re.findall('ID\s*\[\s*<(\w+)>',s)
    f.close()
    if len(m) > 0:
        return m[0].lower()

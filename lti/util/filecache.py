# -*- coding: utf-8 -*-

"""Functions for caching files."""

from __future__ import unicode_literals

import os.path


def exists_html(hash_, settings):
    """Return True if an HTML file with the given hash is already cached."""
    return os.path.isfile('%s/%s.html' % (settings['lti_files_path'], hash_))

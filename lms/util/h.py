# -*- coding: utf-8 -*-

"""Utility functions for working with the h API."""

from __future__ import unicode_literals

import random
import string


USERNAME_ALLOWED_CHARS = string.ascii_letters + string.digits + "._"
"""The characters that are allowed in h usernames."""


USERNAME_MAX_LENGTH = 30
"""The maximum length of an h username."""


def generate_username(request_params):
    """Return an h username generated from the given LTI launch request params."""
    full_name = request_params.get("lis_person_name_full") or ""
    user_id = request_params.get("user_id") or ""

    def n_valid_chars_from(s, n):  # pylint: disable=invalid-name
        """Return a string of up to ``n`` valid chars from the start of ``s``."""
        valid_chars = []
        for char in s:
            if char in USERNAME_ALLOWED_CHARS:
                valid_chars.append(char)
            if len(valid_chars) >= n:
                break
        return "".join(valid_chars)

    def pad(s, n):  # pylint: disable=invalid-name
        """Pad ``s`` so that it's ``n`` chars long."""
        while len(s) < n:
            s = s + random.choice(USERNAME_ALLOWED_CHARS)
        return s

    # The number of chars from user_id that we'll use in the returned username.
    max_chars_from_user_id = 8

    # The number of chars from full_name that we'll use in the returned username.
    max_chars_from_full_name = USERNAME_MAX_LENGTH - max_chars_from_user_id

    full_name = n_valid_chars_from(full_name, n=max_chars_from_full_name)
    full_name = full_name or "Anonymous"

    user_id = n_valid_chars_from(user_id, n=max_chars_from_user_id)
    user_id = pad(user_id, max_chars_from_user_id)

    return full_name + user_id

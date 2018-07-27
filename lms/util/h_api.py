# -*- coding: utf-8 -*-

"""Utility functions for working with the h API."""

from __future__ import unicode_literals


DISPLAY_NAME_MAX_LENGTH = 30
"""The maximum length of an h display name."""


def generate_display_name(request_params):
    """Return an h display_name from the given LTI launch request params."""
    full_name = (request_params.get("lis_person_name_full") or "").strip()
    given_name = (request_params.get("lis_person_name_given") or "").strip()
    family_name = (request_params.get("lis_person_name_family") or "").strip()

    if full_name:
        display_name = full_name
    else:
        display_name = " ".join((given_name, family_name))

    display_name = display_name.strip()

    display_name = display_name or "Anonymous"

    if len(display_name) > DISPLAY_NAME_MAX_LENGTH:
        display_name = display_name[:DISPLAY_NAME_MAX_LENGTH - 1].rstrip() + "…"

    return display_name

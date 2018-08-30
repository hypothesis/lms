# -*- coding: utf-8 -*-

"""Utility functions for working with the h API."""

from __future__ import unicode_literals

import hashlib

from lms.util.exceptions import MissingToolConsumerIntanceGUIDError
from lms.util.exceptions import MissingUserIDError


DISPLAY_NAME_MAX_LENGTH = 30
"""The maximum length of an h display name."""


USERNAME_MAX_LENGTH = 30
"""The maximum length of an h username."""


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


def generate_username(request_params):
    """
    Return an h username generated from the given LTI launch request params.

    :raises lms.util.MissingToolConsumerIntanceGUIDError:
      if ``"tool_consumer_instance_guid"`` is missing from ``request_params``

    :raises lms.util.MissingUserIDError:
      if ``"user_id"`` is missing from ``request_params``
    """
    hash_object = hashlib.sha1()
    hash_object.update(generate_provider(request_params).encode())
    hash_object.update(generate_provider_unique_id(request_params).encode())
    return hash_object.hexdigest()[:USERNAME_MAX_LENGTH]


def generate_provider(request_params):
    """
    Return an h "provider" string from the given LTI launch request params.

    :raises ~lms.util.MissingToolConsumerIntanceGUIDError:
      if ``"tool_consumer_instance_guid"`` is missing from ``request_params``

    """
    tool_consumer_instance_guid = request_params.get("tool_consumer_instance_guid")

    if not tool_consumer_instance_guid:
        raise MissingToolConsumerIntanceGUIDError()

    return tool_consumer_instance_guid


def generate_provider_unique_id(request_params):
    """
    Return an h provider_unique_id from the given LTI launch request params.

    :raises ~lms.util.MissingUserIDError:
      if ``"user_id"`` is missing from ``request_params``

    """
    user_id = request_params.get("user_id")

    if not user_id:
        raise MissingUserIDError()

    return user_id

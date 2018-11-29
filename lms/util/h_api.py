# -*- coding: utf-8 -*-

"""Utility functions for working with the h API."""

import hashlib

from lms.util.exceptions import MissingToolConsumerIntanceGUIDError
from lms.util.exceptions import MissingUserIDError
from lms.util.exceptions import MissingContextTitleError


USERNAME_MAX_LENGTH = 30
"""The maximum length of an h username."""


GROUP_NAME_MAX_LENGTH = 25
"""The maximum length of an h group name."""


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


def generate_group_name(request_params):
    """
    Return a Hypothesis group name generated from the given LTI launch params.

    This will usually generate a valid Hypothesis group name from the LTI
    params. For example if the LTI course's title is too long for a Hypothesis
    group name it'll be truncated. But this doesn't currently handle LTI course
    names that are *too short* to be Hypothesis group names (shorter than 3
    chars) - in that case if you try to create a Hypothesis group using the
    generated name you'll get back an unsuccessful response from the Hypothesis
    API.

    :raises ~lms.util.MissingContextTitleError:
      if ``"context_title"`` is missing from ``request_params``

    """
    name = request_params.get("context_title")

    if not name:
        raise MissingContextTitleError()

    name = name.strip()

    if len(name) > GROUP_NAME_MAX_LENGTH:
        name = name[: GROUP_NAME_MAX_LENGTH - 1].rstrip() + "…"

    return name

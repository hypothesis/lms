# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from lms.util import generate_display_name
from lms.util import generate_username


class TestGenerateDisplayName:
    @pytest.mark.parametrize("request_params,expected_display_name", [
        # It returns the full name if there is one.
        (
            {
                "lis_person_name_full": "Test Full",
                # Add given and family names too. These should be ignored.
                "lis_person_name_given": "Test Given",
                "lis_person_name_family": "Test Family",
            },
            "Test Full",
        ),

        # It strips leading and trailing whitespace from the full name.
        (
            {
                "lis_person_name_full": " Test Full  ",
            },
            "Test Full",
        ),

        # If theres no full name it concatenates given and family names.
        (
            {
                "lis_person_name_given": "Test Given",
                "lis_person_name_family": "Test Family",
            },
            "Test Given Test Family",
        ),

        # If full name is empty it concatenates given and family names.
        (
            {
                "lis_person_name_full": "",
                "lis_person_name_given": "Test Given",
                "lis_person_name_family": "Test Family",
            },
            "Test Given Test Family",
        ),
        (
            {
                "lis_person_name_full": "   ",
                "lis_person_name_given": "Test Given",
                "lis_person_name_family": "Test Family",
            },
            "Test Given Test Family",
        ),

        # It strips leading and trailing whitespace from the concatenated
        # given name and family name.
        (
            {
                "lis_person_name_given": "  Test Given  ",
                "lis_person_name_family": "  Test Family  ",
            },
            "Test Given Test Family",
        ),

        # If theres no full name or given name it uses just the family name.
        (
            {
                "lis_person_name_family": "Test Family",
            },
            "Test Family",
        ),
        (
            {
                "lis_person_name_full": "   ",
                "lis_person_name_given": "",
                "lis_person_name_family": "Test Family",
            },
            "Test Family",
        ),

        # It strips leading and trailing whitespace from just the family name.
        (
            {
                "lis_person_name_family": "  Test Family ",
            },
            "Test Family",
        ),

        # If theres no full name or family name it uses just the given name.
        (
            {
                "lis_person_name_given": "Test Given",
            },
            "Test Given",
        ),
        (
            {
                "lis_person_name_full": "   ",
                "lis_person_name_given": "Test Given",
                "lis_person_name_family": "",
            },
            "Test Given",
        ),

        # It strips leading and trailing whitespace from just the given name.
        (
            {
                "lis_person_name_given": "  Test Given ",
            },
            "Test Given",
        ),

        # If there's nothing else it just returns "Anonymous".
        (
            {},
            "Anonymous",
        ),
        (
            {
                "lis_person_name_full": "   ",
                "lis_person_name_given": " ",
                "lis_person_name_family": "",
            },
            "Anonymous",
        ),

        # If the full name is more than 30 characters long it truncates it.
        (
            {
                "lis_person_name_full": "Test Very Very Looong Full Name",
            },
            "Test Very Very Looong Full Na…",
        ),

        # If the given name is more than 30 characters long it truncates it.
        (
            {
                "lis_person_name_given": "Test Very Very Looong Given Name",
            },
            "Test Very Very Looong Given N…",
        ),

        # If the family name is more than 30 characters long it truncates it.
        (
            {
                "lis_person_name_family": "Test Very Very Looong Family Name",
            },
            "Test Very Very Looong Family…",
        ),

        # If the concatenated given name + family name is more than 30
        # characters long it truncates it.
        (
            {
                "lis_person_name_given": "Test Very Very",
                "lis_person_name_family": "Looong Concatenated Name",
            },
            "Test Very Very Looong Concate…",
        ),
    ])
    def test_it_returns_display_names_generated_from_lti_request_params(
        self, request_params, expected_display_name
    ):
        display_name   = generate_display_name(request_params)

        assert display_name == expected_display_name


@pytest.mark.usefixtures("random")
class TestGenerateUsername:
    @pytest.mark.parametrize(
        "full_name,user_id,expected_username",
        [
            # It uses the full name plus the first 8 chars of the user_id as the h username.
            (
                "janeqpublic",
                "0ae836b9-7fc9-4060-006f-27b2066ac545",
                "janeqpublic0ae836b9",
            ),
            # It truncates the full name if it's longer than 22 chars.
            (
                "janeqpublicthethirdmarquessofbute",
                "0ae836b9-7fc9-4060-006f-27b2066ac545",
                "janeqpublicthethirdmar0ae836b9",
            ),
            # Capital letters, dots and underscores in the full name are preserved.
            (
                "Jane_Q._Public",
                "0ae836b9-7fc9-4060-006f-27b2066ac545",
                "Jane_Q._Public0ae836b9",
            ),
            # Capital letters, dots and underscores in the user_id are preserved too.
            (
                "janeqpublic",
                "0.A_e836b9-7fc9-4060-006f-27b2066ac545",
                "janeqpublic0.A_e836",
            ),
            # Spaces are removed from the full name.
            (
                "jane q public",
                "0ae836b9-7fc9-4060-006f-27b2066ac545",
                "janeqpublic0ae836b9",
            ),
            # Multiple spaces in a row get removed too.
            (
                "jane  q   public",
                "0ae836b9-7fc9-4060-006f-27b2066ac545",
                "janeqpublic0ae836b9",
            ),
            # Leading and trailing spaces get removed too.
            (
                " janeqpublic  ",
                "0ae836b9-7fc9-4060-006f-27b2066ac545",
                "janeqpublic0ae836b9",
            ),
            # Other special characters are also removed from the full name.
            (
                "jane-@-public!",
                "0ae836b9-7fc9-4060-006f-27b2066ac545",
                "janepublic0ae836b9",
            ),
            # Special chars are removed from the userid too.
            (
                "janeqpublic",
                " 0a-@b! 0ae836b9-7fc9-4060-006f-27b2066ac545",
                "janeqpublic0ab0ae83",
            ),
        ],
    )
    def test_it_returns_usernames_generated_from_lti_request_params(
        self, full_name, user_id, expected_username
    ):
        request_params = {"lis_person_name_full": full_name, "user_id": user_id}

        username = generate_username(request_params)

        assert username == expected_username

    def test_it_uses_anonymous_if_the_full_name_is_missing(self):
        request_params = {"user_id": "0ae836b9-7fc9-4060-006f-27b2066ac545"}

        username = generate_username(request_params)

        assert username == "Anonymous0ae836b9"

    @pytest.mark.parametrize(
        "full_name", [None, "", "   ", "!$@-"]  # All disallowed characters.
    )
    def test_it_uses_anonymous_if_the_full_name_is_empty(self, full_name):
        request_params = {
            "lis_person_name_full": full_name,
            "user_id": "0ae836b9-7fc9-4060-006f-27b2066ac545",
        }

        username = generate_username(request_params)

        assert username == "Anonymous0ae836b9"

    def test_it_uses_random_characters_if_the_userid_is_missing(self):
        request_params = {"lis_person_name_full": "janeqpublic"}

        username = generate_username(request_params)

        assert username == "janeqpublicrandom_c"

    def test_it_uses_only_valid_random_characters(self, random):
        # Passing no ``user_id`` in ``request_params`` here, to force
        # ``generate_username()`` to replace ``user_id`` with random chars.
        request_params = {"lis_person_name_full": "janeqpublic"}

        generate_username(request_params)

        # The characters that are valid in h usernames.
        valid_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._"
        for call in random.choice.mock_calls:
            assert call == mock.call(valid_chars)

    @pytest.mark.parametrize(
        "user_id", [None, "", "   ", "!$@-"]  # All disallowed characters.
    )
    def test_it_uses_random_characters_if_the_userid_is_empty(self, user_id):
        request_params = {"lis_person_name_full": "janeqpublic", "user_id": user_id}

        username = generate_username(request_params)

        assert username == "janeqpublicrandom_c"

    def test_it_pads_with_random_characters_if_the_userid_is_too_short(self):
        request_params = {"lis_person_name_full": "janeqpublic", "user_id": "0ae8"}

        username = generate_username(request_params)

        assert username == "janeqpublic0ae8rand"

    def test_it_generates_a_username_if_both_full_name_and_user_id_are_missing(
        self
    ):
        request_params = {}

        username = generate_username(request_params)

        assert username == "Anonymousrandom_c"

    @pytest.fixture
    def random(self, patch):
        random = patch("lms.util.h.random")
        random.choice.side_effect = "random_characters"
        return random

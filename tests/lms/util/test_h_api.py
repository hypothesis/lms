# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from lms.util import generate_display_name


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
        assert generate_display_name(request_params) == expected_display_name

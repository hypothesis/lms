"""
This code is auto-generated.

From tests/bdd/steps/feature_steps/.
"""

from behave import step


@step("I make an LTI launch request")
def i_make_an_lti_launch_request(context):
    # From: tests/bdd/steps/feature_steps/lti.feature: line 15
    context.execute_steps(
        """
    Given I start an LTI launch request
    And   I sign the LTI launch request

    When I send the request to the app
    """
    )


@step("I sign the LTI launch request")
def i_sign_the_lti_launch_request(context):
    # From: tests/bdd/steps/feature_steps/lti.feature: line 11
    context.execute_steps(
        """
    Given I OAuth 1 sign the fixture 'params'
      And I set the form parameters from the fixture 'params'
    """
    )


@step("I start an LTI launch request")
def i_start_an_lti_launch_request(context):
    # From: tests/bdd/steps/feature_steps/lti.feature: line 6
    context.execute_steps(
        """
    Given I start a 'POST' request to 'http://localhost/lti_launches'
      And I set the request header 'Accept' to 'text/html'
      And I set the request header 'Content-Type' to 'application/x-www-form-urlencoded'
    """
    )


@step("standard authentication setup")
def standard_authentication_setup(context):
    # From: tests/bdd/steps/feature_steps/auth.feature: line 1
    context.execute_steps(
        """
    Given the OAuth 1 consumer key is 'Hypothesis4dd96539c449ca5c3d57cc3d778d6bf3'
      And the OAuth 1 shared secret is 'TEST_SECRET'

    Given I create an LMS DB 'ApplicationInstance'
        | Field            | Value                                      |
        | consumer_key     | Hypothesis4dd96539c449ca5c3d57cc3d778d6bf3 |
        | shared_secret    | TEST_SECRET                                |
        | lms_url          | test_lms_url                               |
        | requesters_email | test_requesters_email                      |
    """
    )


@step("standard setup for LTI section {section}")
def standard_setup_for_lti_section_section(context, section):
    # From: tests/bdd/steps/feature_steps/lti.feature: line 1
    context.execute_steps(
        """
    Given fixtures are located in '/lti_certification_1_1/section_{section}'
      And standard authentication setup
      And I load the fixture 'most_common.ini' as 'params'
    """.format(
            section=section
        )
    )


@step("the app redirects to the LTI tool with message matching '{regex}'")
def the_app_redirects_to_the_lti_tool_with_message_matching_regex(context, regex):
    # From: tests/bdd/steps/feature_steps/lti.feature: line 21
    context.execute_steps(
        """
     Then  the response status code is 302
      And   the response header 'Location' is the URL
      And   the fixture 'params' key 'launch_presentation_return_url' is the value
      And   the url matches the value
      And   the url query parameter 'lti_msg' matches '{regex}'
    """.format(
            regex=regex
        )
    )

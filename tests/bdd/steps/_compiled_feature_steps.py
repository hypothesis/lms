"""
This code is auto-generated.

From /home/jon/projects/lms/tests/bdd/steps/feature_steps/.
"""

from behave import step


@step("the user is a {role}")
def the_user_is_a_role(context, role):
    # From: tests/bdd/steps/feature_steps/fixture.feature: line 1
    context.execute_steps(
        """
    Given I load the fixture '{role}.ini' as 'role'
      And I update the fixture 'params' from fixture 'role'
    """.format(
            role=role
        )
    )


@step("the user is an {role}")
def the_user_is_an_role(context, role):
    # From: tests/bdd/steps/feature_steps/fixture.feature: line 5
    context.execute_steps(
        """
    Given the user is a {role}
    """.format(
            role=role
        )
    )


@step("the user is '{name}'")
def the_user_is_name(context, name):
    # From: tests/bdd/steps/feature_steps/fixture.feature: line 8
    context.execute_steps(
        """
    Given the user is a {name}
    """.format(
            name=name
        )
    )


@step("the request is for resource '{resource_id}'")
def the_request_is_for_resource_resource_id(context, resource_id):
    # From: tests/bdd/steps/feature_steps/fixture.feature: line 11
    context.execute_steps(
        """
    Given I load the fixture 'resource_{resource_id}.ini' as 'resource'
      And I update the fixture 'params' from fixture 'resource'
    """.format(
            resource_id=resource_id
        )
    )


@step("the params fixture matches the LTI example for section {test_name}")
def the_params_fixture_matches_the_lti_example_for_section_test_name(
    context, test_name
):
    # From: tests/bdd/steps/feature_steps/fixture.feature: line 15
    context.execute_steps(
        """
    Given I load the fixture 'src/{test_name}.ini' as 'lti_params'
      And I update the fixture 'lti_params' with
      | Key                | Value     |
      | oauth_consumer_key | *MISSING* |
      | oauth_nonce        | *MISSING* |
      | oauth_signature    | *MISSING* |
      | oauth_timestamp    | *MISSING* |
      Then the fixture 'params' matches the fixture 'lti_params'
    """.format(
            test_name=test_name
        )
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


@step("I sign the LTI launch request")
def i_sign_the_lti_launch_request(context):
    # From: tests/bdd/steps/feature_steps/lti.feature: line 11
    context.execute_steps(
        """
    Given I OAuth 1 sign the fixture 'params'
      And I set the form parameters from the fixture 'params'
    """
    )


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


@step("I start an LTI launch request with bad auth parameter '{key}'")
def i_start_an_lti_launch_request_with_bad_auth_parameter_key(context, key):
    # From: tests/bdd/steps/feature_steps/lti.feature: line 21
    context.execute_steps(
        """
    Given I start an LTI launch request
    And   I sign the LTI launch request
    And   I set the fixture 'params' key '{key}' to 'nonsense'
    And   I set the form parameters from the fixture 'params'
    """.format(
            key=key
        )
    )


@step("the app redirects to the LTI tool with message matching '{regex}'")
def the_app_redirects_to_the_lti_tool_with_message_matching_regex(context, regex):
    # From: tests/bdd/steps/feature_steps/lti.feature: line 27
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


@step("the response is HTML")
def the_response_is_html(context):
    # From: tests/bdd/steps/feature_steps/http.feature: line 1
    context.execute_steps(
        """
    Then  the response header 'Content-Type' matches '^text/html'
    """
    )


@step("we get an HTML error with status {status_code}")
def we_get_an_html_error_with_status_status_code(context, status_code):
    # From: tests/bdd/steps/feature_steps/http.feature: line 4
    context.execute_steps(
        """
    Then the response is an HTML page with status {status_code}
    """.format(
            status_code=status_code
        )
    )


@step("the response is an HTML page with status {status_code}")
def the_response_is_an_html_page_with_status_status_code(context, status_code):
    # From: tests/bdd/steps/feature_steps/http.feature: line 7
    context.execute_steps(
        """
    Then  the response is HTML
    And   the response status code is {status_code}
    """.format(
            status_code=status_code
        )
    )


@step("the assigment opens successfully")
def the_assigment_opens_successfully(context):
    # From: tests/bdd/steps/feature_steps/lms.feature: line 1
    context.execute_steps(
        """
    Then the response is HTML
    Then the response status code is 200
    """
    )


@step("the user has instructor privileges")
def the_user_has_instructor_privileges(context):
    # From: tests/bdd/steps/feature_steps/lms.feature: line 5
    context.execute_steps(
        """
    Then the response body does not match 'An instructor needs to launch the assignment to configure it.'
    """
    )


@step("the user only has learner privileges")
def the_user_only_has_learner_privileges(context):
    # From: tests/bdd/steps/feature_steps/lms.feature: line 8
    context.execute_steps(
        """
    Then the response body matches 'An instructor needs to launch the assignment to configure it.'
    """
    )

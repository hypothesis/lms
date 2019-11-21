Feature: Section 1 - Invalid Launch Requests

  This section comprises tests using invalid launch requests.

  Background:
    Given fixtures are located in '/lti_certification_1_1/section_1'

    Given the OAuth 1 consumer key is 'Hypothesis4dd96539c449ca5c3d57cc3d778d6bf3'
    And the OAuth 1 shared secret is 'TEST_SECRET'

    Given I create an LMS DB 'ApplicationInstance'
      | Field            | Value                                      |
      | consumer_key     | Hypothesis4dd96539c449ca5c3d57cc3d778d6bf3 |
      | shared_secret    | TEST_SECRET                                |
      | lms_url          | test_lms_url                               |
      | requesters_email | test_requesters_email                      |

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.1 - No resource_link_id provided
    # Expected result: Return user to the Tool Consumer with an error message

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.2 - No resource_link_id or return URL provided
    # Expected result: A user-friendly error message

    Given I load the fixture '1.2.ini' as 'params'
    And I set the 'params' fixture value 'resource_link_id' to '*MISSING*'
    And I set the 'params' fixture value 'launch_presentation_return_url' to '*MISSING*'

    Given I start a 'POST' request to 'http://localhost/lti_launches'
    And I set the request header 'Accept' to 'text/html'
    And I set the request header 'Content-Type' to 'application/x-www-form-urlencoded'
    And I OAuth 1 sign the fixture 'params'
    And I set the form parameters from the fixture 'params'

    When I send the request to the app

    Then the response header 'Content-Type' matches '^text/html'
    And the response status code is 422

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.3 - Invalid OAuth consumer key
    # Expected result: A user-friendly error message

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.4 - Invalid OAuth signature
    # Expected result: A user-friendly error message

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.5 - Invalid LTI version
    # Expected result: Return user to the Tool Consumer with an error message

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.6 - Wrong LTI version
    # Expected result: Return user to the Tool Consumer with an error message

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.7 - Missing LTI version
    # Expected result: Return user to the Tool Consumer with an error message

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.8 - Invalid LTI message type
    # Expected result: Return user to the Tool Consumer with an error message

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.9 - Missing LTI message type
    # Expected result: Return user to the Tool Consumer with an error message
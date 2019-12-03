Feature: Section 1 - Invalid Launch Requests

  This section comprises tests using invalid launch requests.

  Background:
    Given fixtures are located in '/lti_certification_1_1/section_1'
      And the OAuth 1 consumer key is 'Hypothesis4dd96539c449ca5c3d57cc3d778d6bf3'
      And the OAuth 1 shared secret is 'TEST_SECRET'
      And I create an LMS DB 'ApplicationInstance'
        | Field            | Value                                      |
        | consumer_key     | Hypothesis4dd96539c449ca5c3d57cc3d778d6bf3 |
        | shared_secret    | TEST_SECRET                                |
        | lms_url          | test_lms_url                               |
        | requesters_email | test_requesters_email                      |
      And I load the fixture 'most_common.ini' as 'params'

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.1 - No resource_link_id provided
    # Expected result: Return user to the Tool Consumer with an error message

    Given I update the fixture 'params' with
	  | Key                     | Value               |
	  | custom_link_setting_url | $LtiLink.custom.url |
	  | resource_link_id        | *MISSING*           |

      And I start a 'POST' request to 'http://localhost/lti_launches'
      And I set the request header 'Accept' to 'text/html'
      And I set the request header 'Content-Type' to 'application/x-www-form-urlencoded'
      And I OAuth 1 sign the fixture 'params'
      And I set the form parameters from the fixture 'params'

     When I send the request to the app

     Then the response status code is 302
      And the response header 'Location' is the URL
      And the fixture 'params' key 'launch_presentation_return_url' is the value
      And the url matches the value
      And the url query parameter 'lti_msg' matches '.*resource_link_id'

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.2 - No resource_link_id or return URL provided
    # Expected result: A user-friendly error message

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

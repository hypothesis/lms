Feature: Section 1 - Invalid Launch Requests

  This section comprises tests using invalid launch requests.

  Background:
    Given standard setup for LTI section 1
      And the assignment has been launched before

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.1 - No resource_link_id provided
    # Expected result: Return user to the Tool Consumer with an error message

    Given I update the fixture 'params' with
      | Key                     | Value               |
      | resource_link_id        | *MISSING*           |
      | custom_link_setting_url | $LtiLink.custom.url |

     When I make an LTI launch request

     Then the app redirects to the LTI tool with message matching '.*resource_link_id'

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.2 - No resource_link_id or return URL provided
    # Expected result: A user-friendly error message

    Given I update the fixture 'params' with
      | Key                            | Value               |
      | launch_presentation_return_url | *MISSING*           |
      | resource_link_id               | *MISSING*           |
      | resourcelinkid                 | rli-1234            |
      | custom_link_setting_url        | $LtiLink.custom.url |

     When I make an LTI launch request

     Then we get an HTML error with status 422

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.3 - Invalid OAuth consumer key
    # Expected result: A user-friendly error message

    Given I start an LTI launch request with bad auth parameter 'oauth_consumer_key'
     When I send the request to the app
     Then we get an HTML error with status 403

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.4 - Invalid OAuth signature
    # Expected result: A user-friendly error message

    Given I start an LTI launch request with bad auth parameter 'oauth_signature'
     When I send the request to the app
     Then we get an HTML error with status 403

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.5 - Invalid LTI version
    # Expected result: Return user to the Tool Consumer with an error message

    Given I set the fixture 'params' key 'lti_version' to 'LTI-1'
     When I make an LTI launch request
     Then the app redirects to the LTI tool with message matching '.*lti_version'

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.6 - Wrong LTI version
    # Expected result: Return user to the Tool Consumer with an error message

    Given I set the fixture 'params' key 'lti_version' to 'LTI-2p0'
     When I make an LTI launch request
     Then the app redirects to the LTI tool with message matching '.*lti_version'

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.7 - Missing LTI version
    # Expected result: Return user to the Tool Consumer with an error message

    Given I set the fixture 'params' key 'lti_version' to '*MISSING*'
     When I make an LTI launch request
     Then the app redirects to the LTI tool with message matching '.*lti_version'

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.8 - Invalid LTI message type
    # Expected result: Return user to the Tool Consumer with an error message

    Given I update the fixture 'params' with
      | Key                            | Value                                                                           |
      | lti_message_type               | a-basic-lti-launch-request                                                      |
      | launch_presentation_return_url | https://apps.imsglobal.org/lti/cert/tp/tp_return.php/a-basic-lti-launch-request |

     When I make an LTI launch request

     Then the app redirects to the LTI tool with message matching '.*lti_message_type'

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 1.9 - Missing LTI message type
    # Expected result: Return user to the Tool Consumer with an error message

    Given I update the fixture 'params' with
      | Key                            | Value                                                |
      | lti_message_type               | *MISSING*                                            |
      | launch_presentation_return_url | https://apps.imsglobal.org/lti/cert/tp/tp_return.php |

     When I make an LTI launch request

     Then the app redirects to the LTI tool with message matching '.*lti_message_type'

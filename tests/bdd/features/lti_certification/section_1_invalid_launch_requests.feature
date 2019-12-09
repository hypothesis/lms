Feature: Section 1 - Invalid Launch Requests

  This section comprises tests using invalid launch requests.

  Background:
    Given standard setup for LTI section 1

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
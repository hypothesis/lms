Feature: Standard LTI setup
  Scenario: standard setup for LTI section {section}
    Given fixtures are located in '/lti_certification_1_1/section_{section}'
      And standard authentication setup
      And I load the fixture 'most_common.ini' as 'params'

  Scenario: I start an LTI launch request
    Given I start a 'POST' request to 'http://localhost/lti_launches'
      And I set the request header 'Accept' to 'text/html'
      And I set the request header 'Content-Type' to 'application/x-www-form-urlencoded'

  Scenario: I sign the LTI launch request
    Given I OAuth 1 sign the fixture 'params'
      And I set the form parameters from the fixture 'params'

  Scenario: I make an LTI launch request
    Given I start an LTI launch request
    And   I sign the LTI launch request

    When I send the request to the app

  Scenario: I start an LTI launch request with bad auth parameter '{key}'
    Given I start an LTI launch request
    And   I sign the LTI launch request
    And   I set the fixture 'params' key '{key}' to 'nonsense'
    And   I set the form parameters from the fixture 'params'

  Scenario: the app redirects to the LTI tool with message matching '{regex}'
     Then  the response status code is 302
      And   the response header 'Location' is the URL
      And   the fixture 'params' key 'launch_presentation_return_url' is the value
      And   the url matches the value
      And   the url query parameter 'lti_msg' matches '{regex}'

Feature: HTTP steps
  Scenario: I make an LTI launch request
    Given I start a 'POST' request to 'http://localhost/lti_launches'
      And I set the request header 'Accept' to 'text/html'
      And I set the request header 'Content-Type' to 'application/x-www-form-urlencoded'
      And I OAuth 1 sign the fixture 'params'
      And I set the form parameters from the fixture 'params'

      When I send the request to the app

  Scenario: the response is HTML
    Then  the response header 'Content-Type' matches '^text/html'
Feature: HTTP steps
  Scenario: the response is HTML
    Then  the response header 'Content-Type' matches '^text/html'

  Scenario: we get an HTML error with status {status_code}
    Then the response is an HTML page with status {status_code}

  Scenario: the response is an HTML page with status {status_code}
    Then  the response is HTML
    And   the response status code is {status_code}
Feature: HTTP steps
  Scenario: the response is HTML
    Then  the response header 'Content-Type' matches '^text/html'
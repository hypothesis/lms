Feature: Steps for our app
  Scenario: the assigment opens successfully
    Then the response is HTML
    Then the response status code is 200

  Scenario: the user has instructor privileges
    Then the response body does not match 'An instructor needs to launch the assignment to configure it.'

  Scenario: the user only has learner privileges
    Then the response body matches 'An instructor needs to launch the assignment to configure it.'
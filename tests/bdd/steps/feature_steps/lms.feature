Feature: Steps for our app
  Scenario: the assigment opens successfully
    Then the response is HTML
    Then the response status code is 200

  Scenario: the user has instructor privileges
    Then the response body matches 'role:instructor'

  Scenario: the user only has learner privileges
    Then the response body matches 'role:learner'

  Scenario: the assignment has been launched before
    Given I create an LMS DB 'ModuleItemConfiguration'
      | Field                       | Value              |
      | resource_link_id            | rli-1234           |
      | tool_consumer_instance_guid | IMS Testing        |
      | document_url                | http://example.com |
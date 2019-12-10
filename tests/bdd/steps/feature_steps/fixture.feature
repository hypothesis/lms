Feature: Fixture helpers
  Scenario: the user is a {role}
    Given I load the fixture '{role}.ini' as 'role'
      And I update the fixture 'params' from fixture 'role'

  Scenario: the user is an {role}
    Given the user is a {role}

  Scenario: the request is for resource '{resource_id}'
    Given I load the fixture 'resource_{resource_id}.ini' as 'resource'
      And I update the fixture 'params' from fixture 'resource'

  Scenario: the params fixture matches the LTI example for section {test_name}
    Given I load the fixture 'src/{test_name}.ini' as 'lti_params'
      And I update the fixture 'lti_params' with
      | Key                | Value     |
      | oauth_consumer_key | *MISSING* |
      | oauth_nonce        | *MISSING* |
      | oauth_signature    | *MISSING* |
      | oauth_timestamp    | *MISSING* |
      Then the fixture 'params' matches the fixture 'lti_params'
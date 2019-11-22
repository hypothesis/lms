Feature: Fixture helpers
  Scenario: the user is a {role}
    Given I load the fixture '{role}.ini' as 'role'
      And I update the fixture 'params' from fixture 'role'

  Scenario: the user is an {role}
    Given  the user is a {role}

  Scenario: the request is for resource '{resource_id}'
    Given I load the fixture 'resource_{resource_id}.ini' as 'resource'
      And I update the fixture 'params' from fixture 'resource'
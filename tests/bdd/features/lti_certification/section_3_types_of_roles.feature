Feature: Section 3 - Types of User Roles

  This section performs a variety of launch requests with different values
  for the roles parameter.

  Background:
    Given standard setup for LTI section 3

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 3.1 - Launch as an instructor using a fully-qualified URN
    # Expected result: User should have whatever privileges are appropriate
    # to an instructor; e.g. able to edit

    Given the user is 'Jane'
      And I set the fixture 'params' key 'roles' to 'urn:lti:role:ims/lis/Instructor'

     When I make an LTI launch request

     Then the assigment opens successfully
      And the user has instructor privileges

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 3.2 - Launch as an instructor with a list of roles
    # Expected result: User should have whatever privileges are appropriate
    # to an instructor; e.g. able to edit

    Given the user is 'Jane'
      And I set the fixture 'params' key 'roles' to 'urn:non:ims/something/Else,Instructor,urn:lti:instrole:ims/lis/Alumni'

     When I make an LTI launch request

     Then the assigment opens successfully
      And the user has instructor privileges

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 3.3 - Launch as an instructor using a full URN role in a list
    # Expected result: User should have whatever privileges are appropriate
    # to an instructor; e.g. able to edit

    Given the user is 'Jane'
      And I set the fixture 'params' key 'roles' to 'urn:non:ims/something/Else,urn:lti:role:ims/lis/Instructor,urn:lti:instrole:ims/lis/Alumni'

     When I make an LTI launch request

     Then the assigment opens successfully
      And the user has instructor privileges

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 3.4 - Launch as a learner using a full URN role in a list
    # Expected result: User should be given whatever privileges are appropriate
    # to a student

    Given the user is 'Bob'
       And I set the fixture 'params' key 'roles' to 'urn:non:ims/something/Else,urn:lti:role:ims/lis/Learner,urn:lti:instrole:ims/lis/Alumni'

    When I make an LTI launch request

    Then the assigment opens successfully
     But the user only has learner privileges

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 3.5 - Launch as a user with no context role
    # Expected result: User should be given whatever privileges are appropriate
    # to a user with no role, which could be that they are denied access

    Given the user is 'Bob'
      And I set the fixture 'params' key 'roles' to 'urn:non:ims/something/Else'

    When I make an LTI launch request

    Then the assigment opens successfully
     But the user only has learner privileges

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 3.6 - Launch as a user with an institution role but no context role
    # Expected result: User should be given privileges appropriate to a user
    # with no context role, which could be that they are denied access

    Given I update the fixture 'params' with
      | Key     | Value                            |
      | roles   | urn:lti:instrole:ims/lis/Learner |
      | user_id | user-2001                        |

     When I make an LTI launch request

     Then the assigment opens successfully
      But the user only has learner privileges

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 3.7 - Launch as a user with an institution role which has no corresponding context role
    # Expected result: User should be given privileges appropriate to a user
    # with no context role, which could be that they are denied access

  	Given I update the fixture 'params' with
      | Key     | Value                           |
      | roles   | urn:lti:instrole:ims/lis/Alumni |
      | user_id | user-2001                       |

    When I make an LTI launch request

    Then the assigment opens successfully
     But the user only has learner privileges

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 3.8 - Launch as a user with an unrecognised role
    # Expected result: User should be given privileges appropriate to a user
    # with no context role, which could be that they are denied access

  	Given I update the fixture 'params' with
      | Key     | Value       |
      | roles   | NotALearner |
      | user_id | user-2001   |

    When I make an LTI launch request

    Then the assigment opens successfully
     But the user only has learner privileges
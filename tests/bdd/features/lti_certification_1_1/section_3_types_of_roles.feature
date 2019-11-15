Feature: Section 3 - Types of User Roles

  This section performs a variety of launch requests with different values
  for the roles parameter.

  Scenario: Test 3.1 - Launch as an instructor using a fully-qualified URN
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: User should have whatever privileges are appropriate
    # to an instructor; e.g. able to edit

  Scenario: Test 3.2 - Launch as an instructor with a list of roles
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: User should have whatever privileges are appropriate
    # to an instructor; e.g. able to edit

  Scenario: Test 3.3 - Launch as an instructor using a full URN role in a list
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: User should have whatever privileges are appropriate
    # to an instructor; e.g. able to edit

  Scenario: Test 3.3 - Launch as an instructor using a full URN role in a list
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: User should have whatever privileges are appropriate
    # to an instructor; e.g. able to edit

  Scenario: Test 3.4 - Launch as a learner using a full URN role in a list
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: User should be given whatever privileges are appropriate
    # to a student

  Scenario: Test 3.5 - Launch as a user with no context role
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: User should be given whatever privileges are appropriate
    # to a user with no role, which could be that they are denied access

  Scenario: Test 3.6 - Launch as a user with an institution role but no context role
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: User should be given privileges appropriate to a user
    # with no context role, which could be that they are denied access

  Scenario: Test 3.7 - Launch as a user with an institution role which has no corresponding context role
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: User should be given privileges appropriate to a user
    # with no context role, which could be that they are denied access

  Scenario: Test 3.8 - Launch as a user with an unrecognised role
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: User should be given privileges appropriate to a user
    # with no context role, which could be that they are denied access
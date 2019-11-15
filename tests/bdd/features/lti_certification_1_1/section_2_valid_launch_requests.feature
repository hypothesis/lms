Feature: Section 2 - Valid Launch Requests

  This section performs a variety of launch requests for instructors and
  students. Each launch changes one or more of the following parameters:

   * context
   * resource link
   * user
   * user role
   * user information

  Scenario: Test 2.1 - Launch as an instructor
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: User should have whatever privileges are appropriate to
    # an instructor; e.g. able to edit

  Scenario: Test 2.2 - Launch as an instructor from a different resource link
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: The user should have whatever privileges are appropriate
    # to an instructor (e.g. able to edit) but within a new instance of the
    # tool in the same course (context) as the previous test

  Scenario: Test 2.3 - Launch as a learner
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: User should be given whatever privileges are appropriate
    # to a student

  Scenario: Test 2.4 - Launch as a learner from a different resource link
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: User should be given whatever privileges are appropriate
    # to a student
Feature: Section 2 - Valid Launch Requests

  This section performs a variety of launch requests for instructors and
  students. Each launch changes one or more of the following parameters:

   * context
   * resource link
   * user
   * user role
   * user information

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 2.1 - Launch as an instructor
    # Expected result: User should have whatever privileges are appropriate to
    # an instructor; e.g. able to edit

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 2.2 - Launch as an instructor from a different resource link
    # Expected result: The user should have whatever privileges are appropriate
    # to an instructor (e.g. able to edit) but within a new instance of the
    # tool in the same course (context) as the previous test

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 2.3 - Launch as a learner
    # Expected result: User should be given whatever privileges are appropriate
    # to a student

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 2.4 - Launch as a learner from a different resource link
    # Expected result: User should be given whatever privileges are appropriate
    # to a student
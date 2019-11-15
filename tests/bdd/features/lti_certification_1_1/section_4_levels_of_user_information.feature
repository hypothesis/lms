Feature: Section 4 - Levels of User Information

  This section performs a series of tests that each provides less and less
  information until they get to the minimum possible. Each test uses the
  same resource_link_id (in a new context) but a different value for the
  user_id parameter. These tests only apply to LTI 1.

  Scenario: Test 4.1 - Launch as a learner with email but no name
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: The tool should handle the lack of name information in
    # a user-friendly manner, which could be that they are denied access

  Scenario: Test 4.2 - Launch as a learner with given/family but no full name
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: The tool should detect the user's name

  Scenario: Test 4.3 - Launch as a learner with a full name but no given or family names
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: The tool should detect the user's name

  Scenario: Test 4.4 - Launch as an instructor with no personal information
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: User should have privileges appropriate to an instructor
    # (e.g. able to edit) unless personal information is required in which case
    # access should be denied and the user returned to the Tool Consumer with
    # a user-friendly message

  Scenario: Test 4.5 - Launch as an instructor with no context or personal information apart from the context ID
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: User should have privileges appropriate to an instructor
    # (e.g. able to edit) unless context and/or personal information is required
    # in which case access should be denied and the user returned to the Tool
    # Consumer with a user-friendly message

  Scenario: Test 4.6 - Launch as Instructor with no context information
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: User should have privileges appropriate to an instructor
    # (e.g. able to edit) unless context and/or personal information is
    # required in which case access should be denied and the user returned to
    # the Tool Consumer with a user-friendly message

  Scenario: Test 4.7 - Launch with only resource_link_id
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: The user should provide whatever access is relevant to
    # a guest or respond with an error message
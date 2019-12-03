Feature: Section 4 - Levels of User Information

  This section performs a series of tests that each provides less and less
  information until they get to the minimum possible. Each test uses the
  same resource_link_id (in a new context) but a different value for the
  user_id parameter. These tests only apply to LTI 1.

  Background:
    Given standard setup for LTI section 4

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 4.1 - Launch as a learner with email but no name
    # Expected result: The tool should handle the lack of name information in
    # a user-friendly manner, which could be that they are denied access

    Given the user is 'Sally'
      And I set the fixture 'params' key 'roles' to 'Learner'
      And I update the fixture 'params' with
      | Key                              | Value            |
      | lis_person_name_full             | *MISSING*        |
      | lis_person_name_family           | *MISSING*        |
      | lis_person_name_given            | *MISSING*        |

     When I make an LTI launch request

     Then the assigment opens successfully
      But the user only has learner privileges

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 4.2 - Launch as a learner with given/family but no full name
    # Expected result: The tool should detect the user's name

    Given the user is 'Lucky'
      And I set the fixture 'params' key 'roles' to 'Learner'
      And I update the fixture 'params' with
      | Key                              | Value            |
      | lis_person_name_full             | *MISSING*        |

     When I make an LTI launch request

     Then the assigment opens successfully
      But the user only has learner privileges

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 4.3 - Launch as a learner with a full name but no given or family names
    # Expected result: The tool should detect the user's name

    Given the user is 'Sally'
      And I set the fixture 'params' key 'roles' to 'Learner'
      And I update the fixture 'params' with
      | Key                              | Value            |
      | lis_person_name_family           | *MISSING*        |
      | lis_person_name_given            | *MISSING*        |

     When I make an LTI launch request

     Then the assigment opens successfully
      But the user only has learner privileges

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 4.4 - Launch as an instructor with no personal information
    # Expected result: User should have privileges appropriate to an instructor
    # (e.g. able to edit) unless personal information is required in which case
    # access should be denied and the user returned to the Tool Consumer with
    # a user-friendly message

    Given the user is 'Jane'
      And I set the fixture 'params' key 'roles' to 'Instructor'
      And I update the fixture 'params' with
      | Key                              | Value      |
      | lis_person_contact_email_primary | *MISSING*  |
      | lis_person_name_family           | *MISSING*  |
      | lis_person_name_given            | *MISSING*  |
      | lis_person_name_full             | *MISSING*  |

     When I make an LTI launch request

     Then the assigment opens successfully
      And the user has instructor privileges

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 4.5 - Launch as an instructor with no context or personal information apart from the context ID
    # Expected result: User should have privileges appropriate to an instructor
    # (e.g. able to edit) unless context and/or personal information is required
    # in which case access should be denied and the user returned to the Tool
    # Consumer with a user-friendly message

    Given the user is 'Jane'
      And I set the fixture 'params' key 'roles' to 'Instructor'
      And all context parameters are missing
      And I set the fixture 'params' key 'context_id' to 'con-182'
      And I update the fixture 'params' with
      | Key                              | Value      |
      | lis_person_contact_email_primary | *MISSING*  |
      | lis_person_name_family           | *MISSING*  |
      | lis_person_name_given            | *MISSING*  |
      | lis_person_name_full             | *MISSING*  |

     When I make an LTI launch request

     Then the app redirects to the LTI tool with message matching '.*'

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 4.6 - Launch as Instructor with no context information
    # Expected result: User should have privileges appropriate to an instructor
    # (e.g. able to edit) unless context and/or personal information is
    # required in which case access should be denied and the user returned to
    # the Tool Consumer with a user-friendly message

     Given the user is 'Jane'
      And I set the fixture 'params' key 'roles' to 'Instructor'
      And all context parameters are missing
      And I update the fixture 'params' with
      | Key                              | Value                             |
      | custom_context_memberships_url   | $ToolProxyBinding.memberships.url |
      | custom_context_setting_url       | *MISSING*                         |
      | custom_link_setting_url          | *MISSING*                         |

     When I make an LTI launch request

     Then the app redirects to the LTI tool with message matching '.*'

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 4.7 - Launch with only resource_link_id
    # Expected result: The user should provide whatever access is relevant to
    # a guest or respond with an error message

    Given I set the fixture 'params' key 'resource_link_id' to 'rli-1234'
      And all context parameters are missing
      And I update the fixture 'params' with
      | Key                              | Value                             |
      | custom_context_memberships_url   | $ToolProxyBinding.memberships.url |
      | custom_context_setting_url       | *MISSING*                         |
      | custom_link_setting_url          | *MISSING*                         |

     When I make an LTI launch request

     Then we get an HTML error with status 403
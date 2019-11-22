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

    Given I update the fixture 'params' with
      | Key                              | Value            |
      | lis_person_contact_email_primary | sally@school.edu |
      | lis_person_sourcedid             | school.edu:sally |
      | user_id                          | 543216           |

    When  I make an LTI launch request

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 4.2 - Launch as a learner with given/family but no full name
    # Expected result: The tool should detect the user's name

    Given I update the fixture 'params' with
      | Key                              | Value            |
      | lis_person_contact_email_primary | seven@school.edu |
      | lis_person_name_family           | Seven            |
      | lis_person_name_given            | Luck             |
      | lis_person_sourcedid             | school.edu:seven |
      | user_id                          | 777777           |

    When  I make an LTI launch request


  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 4.3 - Launch as a learner with a full name but no given or family names
    # Expected result: The tool should detect the user's name

    Given I update the fixture 'params' with
      | Key                              | Value            |
      | lis_person_contact_email_primary | sally@school.edu |
      | lis_person_name_full             | Sally R. Person  |
      | lis_person_sourcedid             | school.edu:sally |
      | user_id                          | 543216           |

    When  I make an LTI launch request

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 4.4 - Launch as an instructor with no personal information
    # Expected result: User should have privileges appropriate to an instructor
    # (e.g. able to edit) unless personal information is required in which case
    # access should be denied and the user returned to the Tool Consumer with
    # a user-friendly message

    Given I set the fixture 'params' key 'roles' to 'Instructor'

    When  I make an LTI launch request

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 4.5 - Launch as an instructor with no context or personal information apart from the context ID
    # Expected result: User should have privileges appropriate to an instructor
    # (e.g. able to edit) unless context and/or personal information is required
    # in which case access should be denied and the user returned to the Tool
    # Consumer with a user-friendly message

    Given I update the fixture 'params' with
      | Key                          | Value      |
      | context_label                | *MISSING*  |
      | context_title                | *MISSING*  |
      | context_type                 | *MISSING*  |
      | lis_course_section_sourcedid | *MISSING*  |
      | resource_link_title          | *MISSING*  |
      | roles                        | Instructor |

    When  I make an LTI launch request

    Then  the app redirects to the LTI tool with message matching '.*'

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 4.6 - Launch as Instructor with no context information
    # Expected result: User should have privileges appropriate to an instructor
    # (e.g. able to edit) unless context and/or personal information is
    # required in which case access should be denied and the user returned to
    # the Tool Consumer with a user-friendly message

    Given I update the fixture 'params' with
      | Key                              | Value                             |
      | context_id                       | *MISSING*                         |
      | context_label                    | *MISSING*                         |
      | context_title                    | *MISSING*                         |
      | context_type                     | *MISSING*                         |
      | custom_context_memberships_url   | $ToolProxyBinding.memberships.url |
      | custom_context_setting_url       | *MISSING*                         |
      | custom_link_setting_url          | *MISSING*                         |
      | lis_course_section_sourcedid     | *MISSING*                         |
      | lis_person_contact_email_primary | jane@school.edu                   |
      | lis_person_name_family           | Lastname                          |
      | lis_person_name_full             | Jane Q. Lastname                  |
      | lis_person_name_given            | Jane                              |
      | resource_link_title              | *MISSING*                         |
      | roles                            | Instructor                        |

    When  I make an LTI launch request

    Then  the app redirects to the LTI tool with message matching '.*'

  @v1.0 @v1.1 @v1.2 @required
  Scenario: Test 4.7 - Launch with only resource_link_id
    # Expected result: The user should provide whatever access is relevant to
    # a guest or respond with an error message

    Given I update the fixture 'params' with
      | Key                            | Value                             |
      | context_id                     | *MISSING*                         |
      | context_label                  | *MISSING*                         |
      | context_title                  | *MISSING*                         |
      | context_type                   | *MISSING*                         |
      | custom_context_memberships_url | $ToolProxyBinding.memberships.url |
      | custom_context_setting_url     | *MISSING*                         |
      | custom_link_setting_url        | *MISSING*                         |
      | lis_course_section_sourcedid   | *MISSING*                         |
      | lis_person_sourcedid           | *MISSING*                         |
      | resource_link_title            | *MISSING*                         |
      | roles                          | *MISSING*                         |
      | user_id                        | *MISSING*                         |

    When  I make an LTI launch request

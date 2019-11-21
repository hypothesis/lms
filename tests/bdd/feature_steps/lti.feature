Feature: Standard LTI setup
  Scenario: standard setup for LTI section {section}
    Given fixtures are located in '/lti_certification_1_1/section_{section}'
      And standard authentication setup
      And I load the fixture '{section}.1.ini' as 'params'
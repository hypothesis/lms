Feature: Standard LTI setup
  Scenario: standard setup for LTI section {section}
    Given fixtures are located in '/lti_certification_1_1/section_{section}'
      And standard authentication setup
      And I load the fixture 'average.ini' as 'params'

  Scenario: the app redirects to the LTI tool with message matching '{regex}'
     Then  the response status code is 302
      And   the response header 'Location' is the URL
      And   the fixture 'params' key 'launch_presentation_return_url' is the value
      And   the url matches the value
      And   the url query parameter 'lti_msg' matches '{regex}'

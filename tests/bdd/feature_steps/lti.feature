Feature: Standard LTI setup
  Scenario: standard setup for LTI section {section}
    Given fixtures are located in '/lti_certification_1_1/section_{section}'
      And standard authentication setup
      And I load the fixture '{section}.1.ini' as 'params'

  Scenario: the app redirects to the LTI tool with message matching '{regex}'
     Then  the response status code is 302
      And   the response header 'Location' is the URL
      And   the url matches 'https://apps.imsglobal.org/lti/cert/tp/tp_return.php/basic-lti-launch-request'
      And   the url query parameter 'lti_msg' matches '{regex}'

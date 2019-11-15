Feature: Section 1 - Invalid Launch Requests

  This section comprises tests using invalid launch requests.

  Scenario: Test 1.1 - No resource_link_id provided
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: Return user to the Tool Consumer with an error message

  Scenario: Test 1.2 - No resource_link_id or return URL provided
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: A user-friendly error message

  Scenario: Test 1.3 - Invalid OAuth consumer key
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: A user-friendly error message

  Scenario: Test 1.4 - Invalid OAuth signature
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: A user-friendly error message

  Scenario: Test 1.5 - Invalid LTI version
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: Return user to the Tool Consumer with an error message

  Scenario: Test 1.6 - Wrong LTI version
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: Return user to the Tool Consumer with an error message

  Scenario: Test 1.7 - Missing LTI version
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: Return user to the Tool Consumer with an error message

  Scenario: Test 1.8 - Invalid LTI message type
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: Return user to the Tool Consumer with an error message

  Scenario: Test 1.9 - Missing LTI message type
    # Applies to: 1.0, 1.1, 1.2 [required]
    # Expected result: Return user to the Tool Consumer with an error message
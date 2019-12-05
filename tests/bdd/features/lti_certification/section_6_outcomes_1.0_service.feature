Feature: Section 6 - Outcomes 1.0 service

  This section contains tests of the Outcomes 1.0 service. The tests only
  require outcomes to be sent to the Tool Consumer for users with Learner
  roles. However, it is not necessary for the grades to be returned via the
  Learner sessions; it is possible to use Instructor launches as an
  alternative mechanism for returning grades for students.

  These tests require outcomes to be generated in at least 2 different
  contexts, for at least 2 different resource links within the same context,
  and for at least 2 different users for the same resource link.

  @v1.1 @outcomes-1 @required
  Scenario: Test 6.1 - replaceResult requests
    # Expected result: All replaceResult requests for outcomes should be
    # properly formed.

  @v1.1 @outcomes-1 @optional
  Scenario: Test 6.2 - readResult requests
    # Expected result: If the tool sends any readResult requests for outcomes
    # they should be properly formed.

  @v1.1 @outcomes-1 @optional
  Scenario: Test 6.3 - deleteResult requests
    # Expected result: If the tool sends any deleteResult requests for outcomes
    # they should be properly formed.

  @v1.1 @outcomes-1 @required
  Scenario: Test 6.4 - Processing of Gradebook entries
    # Expected result: This test is passed when all the required outcome values
    # listed below have been processed. You must have an outcome value set in
    # more than one context, and in at least one context there must be
    # outcomes for more than one resource link and more than one user
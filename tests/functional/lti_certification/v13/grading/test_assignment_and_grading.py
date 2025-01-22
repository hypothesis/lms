class TestAssignmentAndGradingSerices:
    """
    From: https://www.imsglobal.org/spec/lti/v1p3/cert/#assignment-and-grade-services-testing

    Assignments and Grade Services (AGS) is tested as pure service (without any UI).
    The Tool is required to acquire the OAuth2 tokens from the IMS Global
    testing OAuth2 server necessary to interact with the AGS system.
    Testing for AGS for the Tool is very different from all other testing
    in the Certification Suite.

    Since it is possible to jump directly to testing for AGS, the Certification
    Suite provides the place to launch a standard, Learner-based LTI 1.3
    launch into your Tool. However, that is the only prescribed test in the
    Certification Suite.

    After that launch it is the responsibility of the Tool alone to work with
    the AGS API to create lineitems and scores in the Certification Suite.
    All interaction with the Gradebook simulated by the Certification Suite
    can be viewed on the Results page
    """

    def test_it(self):
        """
        Due to the nature of this test in the certification no actual testing happens here.

        The test in the certification tool expects the tool to initiate
        communication with the service but it's not tied to any launch or real
        flow in the app.

        We include here the script used for the certification for completeness.
        ```
        # These are included in the JWT sent by the testing tool
        # https://purl.imsglobal.org/spec/lti/claim/resource_link -> id
        RESOURCE_LINK_ID = "d57dfc1975a441da896c9d7eb0413b96"
        # https://purl.imsglobal.org/spec/lti-ags/claim/endpoint -> lineitmems
        LINE_ITEMS = "https://ltiadvantagevalidator.imsglobal.org/ltitool/rest/assignmentsgrades/16793/lineitems"

        # The line item for this assignment doesn't yet exist, we'll crate it calling the LINE_ITEMS endpoint
        LINE_ITEM = ""


        from lms.services.lti_grading._v13 import LTI13GradingService
        from lms.services import *
        from lms.product.plugin import MiscPlugin
        from lms.product import Product

        application_instance = (
            db.query(models.ApplicationInstance)
            .join(models.LTIRegistration)
            .filter_by(issuer="https://ltiadvantagevalidator.imsglobal.org")
            .one()
        )
        ltia_service = LTIAHTTPService(
            application_instance.lti_registration,
            MiscPlugin(),
            request.find_service(JWTService),
            request.find_service(name="http"),
            request.find_service(JWTOAuth2TokenService),
        )
        grading_service = LTI13GradingService(LINE_ITEM, LINE_ITEMS, ltia_service, product_family=Product.family.UNKNOWN, misc_plugin=MiscPlugin())


        # Create the line item here to hold the scores
        response = ltia_service.request(
            "POST",
            LINE_ITEMS,
            headers={"Content-Type": "application/vnd.ims.lis.v2.lineitem+json"},
            scopes=LTI13GradingService.LTIA_SCOPES,
            json={
                "scoreMaximum": 1,
                "label": "Introduction Assignment",
                "resourceId": RESOURCE_LINK_ID,
                "tag": "certification_grade",
            },
        )
        grading_service.line_item_url = response.json()["id"]

        # Record a score in the newly created line item
        grading_service.record_result("40899", 0.8)
        grade = grading_service.read_result("40899")
        print("Grade:", grade)
        ```
        """

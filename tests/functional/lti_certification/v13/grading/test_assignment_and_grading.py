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
        Due to the nature of this test in the certification no actual testing
        happens here.

        The test in the certification tool expects the tool to initiate
        communication with the service but it's not tied to any launch or real
        flow in the app.

        We include here the script used for the certification for completeness.
        ```
        # These are included in the JWT sent by the testing tool
        # https://purl.imsglobal.org/spec/lti/claim/resource_link -> id
        RESOURCE_LINK_ID = "7a3f7bed2844419caa4edf74c93f4375"
        # https://purl.imsglobal.org/spec/lti-ags/claim/endpoint -> lineitmems
        LINEITEMS = "https://ltiadvantagevalidator.imsglobal.org/ltitool/rest/assignmentsgrades/11151/lineitems"


        from lms.services.lti_grading._v13 import LTI13GradingService
        from lms.services import *

        application_instance = (
            db.query(models.ApplicationInstance)
            .join(models.LTIRegistration)
            .filter_by(issuer="https://ltiadvantagevalidator.imsglobal.org")
            .one()
        )
        ltia_service = LTIAHTTPService(
            application_instance.lti_registration,
            request.find_service(JWTService),
            request.find_service(name="http"),
        )
        grading_service = LTI13GradingService(LINEITEMS, ltia_service)


        response = ltia_service.request(
            "POST",
            LINEITEMS,
            headers={"Content-Type": "application/vnd.ims.lis.v2.lineitem+json"},
            scopes=LTI13GradingService.LTIA_SCOPES,
            json={
                "scoreMaximum": 1,
                "label": "Introduction Assignment",
                "resourceId": RESOURCE_LINK_ID,
                "tag": "certification_grade",
            },
        )
        grading_service.grading_url = response.json()["id"]
        grading_service.record_result("40899", 0.8)
        grade = grading_service.read_result("40899")
        print("Grade:", grade)
        ```
        """

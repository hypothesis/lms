from lms.product.plugin.misc import MiscPlugin


class BlackboardMiscPlugin(MiscPlugin):
    def get_grading_user_id(self, application_instance, params: dict):
        if application_instance.lti_version == "1.3.0":
            # In LTI 1.3 we use the user id of the student.
            # This happens to have the same value as lis_result_sourcedid in LTI1.3
            # which allows to account for LTI upgrades done midterm for which
            # we have the old LTI1.1 value for lis_result_sourcedid
            return params["student_user_id"]

        return super().get_grading_user_id(application_instance, params)

    @staticmethod
    def factory(_request, _context):
        return BlackboardMiscPlugin()

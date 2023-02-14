from marshmallow import Schema
from pyramid.view import view_config
from webargs import fields

from lms.product.plugin.grouping import GroupError
from lms.security import Permissions
from lms.validation._base import PyramidRequestSchema


class APISyncSchema(PyramidRequestSchema):
    class LMS(Schema):
        product = fields.Str(required=True)

    lms = fields.Nested(LMS, required=True)
    assignment_id = fields.Int(required=True)
    context_id = fields.Str(required=True)
    group_set_id = fields.Str(required=False, allow_none=True)
    group_info = fields.Dict(required=True)
    gradingStudentId = fields.Str(required=False, allow_none=True)


@view_config(
    route_name="api.sync",
    request_method="POST",
    renderer="json",
    permission=Permissions.API,
    schema=APISyncSchema,
)
def sync(request):
    grouping_service = request.find_service(name="grouping")
    course = request.find_service(name="course").get_by_context_id(
        context_id=request.parsed_params["context_id"], raise_on_missing=True
    )
    grading_student_id = request.parsed_params.get("gradingStudentId")

    if group_set_id := request.parsed_params.get("group_set_id"):
        course_copy_plugin = request.product.plugin.course_copy
        # For course copy we might have stored a mapping for this `group_set_id`
        group_set_id = course.get_mapped_group_set_id(group_set_id)
        try:
            groupings = grouping_service.get_groups(
                user=request.user,
                lti_user=request.lti_user,
                course=course,
                grading_student_id=grading_student_id,
                group_set_id=group_set_id,
            )

        except GroupError:
            # If we fail to get the list of groups, try to fix the situation for course copy
            # and try again
            if group_set_id := course_copy_plugin.find_matching_group_set_in_course(
                course, group_set_id
            ):
                groupings = grouping_service.get_groups(
                    user=request.user,
                    lti_user=request.lti_user,
                    course=course,
                    grading_student_id=grading_student_id,
                    group_set_id=group_set_id,
                )
            else:
                # Raise the original failure if we didn't get a new `group_set_id`
                raise

    else:
        groupings = grouping_service.get_sections(
            user=request.user,
            lti_user=request.lti_user,
            course=course,
            grading_student_id=grading_student_id,
        )

    # Sync the groups over to H so they are ready to be annotated against
    request.find_service(name="lti_h").sync(
        groupings, request.parsed_params["group_info"]
    )

    # Store the relationship between the assignment and the groupings
    request.find_service(name="assignment").upsert_assignment_groupings(
        assignment_id=request.parsed_params["assignment_id"], groupings=groupings
    )

    authority = request.registry.settings["h_authority"]
    return [group.groupid(authority) for group in groupings]

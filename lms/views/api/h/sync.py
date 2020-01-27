from pyramid.view import view_config


@view_config(request_method="POST", renderer="json", route_name="h_api.sync")
def sync_lti_data_to_h(request):
    lti_h_service = request.find_service(name="lti_h")
    lti_h_service.upsert_h_user()
    group_ids = lti_h_service.upsert_course_groups()
    lti_h_service.add_user_to_groups()
    return group_ids

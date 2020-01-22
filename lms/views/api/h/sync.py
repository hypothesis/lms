from pyramid.view import view_config


@view_config(request_method="POST", renderer="json", route_name="h_api.sync")
def sync_lti_data_to_h(request):
    import pdb; pdb.set_trace()
    return {}
    # lti_h_service = self.request.find_service(name="lti_h")
    # lti_h_service.upsert_h_user()
    # lti_h_service.upsert_course_groups()
    # lti_h_service.add_user_to_groups()

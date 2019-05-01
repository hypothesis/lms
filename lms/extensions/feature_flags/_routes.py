def includeme(config):
    config.add_route("feature_flags_cookie_form", "/flags")
    config.add_route("feature_flags_view_predicate_test", "/flags/test/view-predicate")

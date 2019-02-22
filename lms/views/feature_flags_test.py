from pyramid.view import view_config


@view_config(route_name="feature_flags_test", renderer="json", request_method="GET")
def test(request):
    result = {}

    if request.feature("foo"):
        result["foo"] = "Foo feature flag is enabled"
    else:
        result["foo"] = "Foo feature flag is disabled"

    if request.feature("bar"):
        result["bar"] = "Bar feature flag is enabled"
    else:
        result["bar"] = "Bar feature flag is disabled"

    if request.feature("gar"):
        result["gar"] = "Gar feature flag is enabled"
    else:
        result["gar"] = "Gar feature flag is disabled"

    return result

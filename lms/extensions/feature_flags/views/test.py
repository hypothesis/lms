from pyramid.view import view_config, view_defaults


@view_defaults(
    route_name="feature_flags_view_predicate_test",
    renderer="string",
    request_method="GET",
)
class ViewPredicateTestViews:  # pylint:disable=no-self-use
    def __init__(self, request):
        self._request = request

    @view_config(feature_flag="foo")
    def view_that_requires_feature_flag(self):
        return "Feature flag 'foo' is on"

    @view_config()
    def view_that_doesnt_require_feature_flag(self):
        return "Feature flag 'foo' is off"

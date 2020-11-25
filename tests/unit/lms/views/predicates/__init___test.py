from unittest import mock

from lms.views.predicates import includeme
from lms.views.predicates._lti_launch import (
    AuthorizedToConfigureAssignments,
    BlackboardCopied,
    CanvasFile,
    Configured,
    DBConfigured,
    URLConfigured,
)


def test_includeme_adds_the_view_predicates():
    config = mock.Mock(spec_set=["add_view_predicate"])

    includeme(config)

    assert config.add_view_predicate.call_args_list == [
        mock.call("db_configured", DBConfigured),
        mock.call("blackboard_copied", BlackboardCopied),
        mock.call("canvas_file", CanvasFile),
        mock.call("url_configured", URLConfigured),
        mock.call("configured", Configured),
        mock.call(
            "authorized_to_configure_assignments", AuthorizedToConfigureAssignments
        ),
    ]

from lms.views.api.blackboard.sync import Sync


def test_it(pyramid_request):
    result = Sync(pyramid_request).sync()

    assert result == []

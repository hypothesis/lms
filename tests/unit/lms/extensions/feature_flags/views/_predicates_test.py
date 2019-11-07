from unittest import mock

from lms.extensions.feature_flags.views._predicates import FeatureFlagViewPredicate


class TestFeatureFlagsViewPredicate:
    def test_text(self):
        assert (
            FeatureFlagViewPredicate("test_feature", mock.sentinel.config).text()
            == "feature_flag = test_feature"
        )

    def test_phash(self):
        assert (
            FeatureFlagViewPredicate("test_feature", mock.sentinel.config).phash()
            == "feature_flag = test_feature"
        )

    def test_it_delegates_to_request_dot_feature(self, pyramid_request):
        view_predicate = FeatureFlagViewPredicate("test_feature", mock.sentinel.config)

        matches = view_predicate(mock.sentinel.context, pyramid_request)

        pyramid_request.feature.assert_called_once_with("test_feature")
        assert matches == pyramid_request.feature.return_value

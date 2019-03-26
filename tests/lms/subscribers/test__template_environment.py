from lms.subscribers._template_environment import _add_js_config


class TestJSConfig:
    def test_it_adds_the_urls_to_the_template_environment(self, pyramid_request):
        event = {"request": pyramid_request}

        _add_js_config(event)

        # urls is an empty dict for now!
        assert event["js_config"]["urls"] == {}

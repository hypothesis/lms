class TestSanity:
    def test_woo(self, app):
        app.get("/not_a_url_at_all", status=404)

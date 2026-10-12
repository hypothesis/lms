import pytest

from lms.views.api.canvas.lti_embeds import open_lti_embeds_in_canvas

STUDIO_SRC = (
    "https://hypothesis.instructure.com/courses/252/external_tools/retrieve"
    "?display=borderless&amp;url=https%3A%2F%2Fhypothesis.instructuremedia.com"
    "%2Flti%2Flaunch%3Fcustom_arc_media_id%3Da103869d"
)
ZOOM_SRC = (
    "https://example.instructure.com/courses/97321/external_tools/retrieve"
    "?display=borderless&amp;resource_link_lookup_uuid=8f1c2d"
)


class TestOpenLTIEmbedsInCanvas:
    def test_it_replaces_a_studio_embed_with_a_link_to_canvas(self):
        body = f'<p>Testing</p><iframe src="{STUDIO_SRC}" width="640"></iframe>'

        result = open_lti_embeds_in_canvas(body)

        assert "<iframe" not in result
        assert f'href="{STUDIO_SRC}"' in result
        assert 'target="_blank"' in result
        assert "<p>Testing</p>" in result

    def test_it_replaces_a_zoom_embed_the_same_way(self):
        # Zoom uses the same generic Canvas route with a different lookup
        # param, so the match is on the path, not the tool.
        body = f'<iframe src="{ZOOM_SRC}"></iframe>'

        result = open_lti_embeds_in_canvas(body)

        assert "<iframe" not in result
        assert f'href="{ZOOM_SRC}"' in result

    @pytest.mark.parametrize(
        "body",
        [
            # src isn't the first attribute
            f'<iframe width="640" src="{STUDIO_SRC}" height="360"></iframe>',
            # single-quoted src
            f"<iframe src='{STUDIO_SRC}'></iframe>",
            # self-closing
            f'<iframe src="{STUDIO_SRC}" />',
            # closing tag on a later line
            f'<iframe src="{STUDIO_SRC}">\n</iframe>',
        ],
    )
    def test_it_handles_attribute_and_closing_variants(self, body):
        result = open_lti_embeds_in_canvas(body)

        assert "<iframe" not in result
        assert STUDIO_SRC in result

    @pytest.mark.parametrize(
        "body",
        [
            '<iframe src="https://www.youtube.com/embed/abc123"></iframe>',
            '<iframe srcdoc="<p>inline</p>"></iframe>',
        ],
    )
    def test_it_leaves_other_iframes_alone(self, body):
        assert open_lti_embeds_in_canvas(body) == body

    def test_it_replaces_every_lti_embed_on_the_page(self):
        body = (
            f'<iframe src="{STUDIO_SRC}"></iframe>'
            '<iframe src="https://www.youtube.com/embed/abc123"></iframe>'
            f'<iframe src="{ZOOM_SRC}"></iframe>'
        )

        result = open_lti_embeds_in_canvas(body)

        assert result.count("<iframe") == 1
        assert "youtube.com/embed/abc123" in result
        assert result.count('target="_blank"') == 2

    @pytest.mark.parametrize("body", [None, "", "<p>No embeds here</p>"])
    def test_it_passes_through_bodies_with_nothing_to_replace(self, body):
        assert open_lti_embeds_in_canvas(body) == body

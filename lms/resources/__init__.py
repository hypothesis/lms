"""
The application's Pyramid traversal resources.

See the traversal-related sections in the Pyramid docs:

* https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hellotraversal.html
* https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/muchadoabouttraversal.html
* https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/traversal.html
* https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hybrid.html
"""
from lms.resources.canvas_oauth2_redirect import CanvasOAuth2RedirectResource
from lms.resources.default import DefaultResource
from lms.resources.lti_launch import LTILaunchResource

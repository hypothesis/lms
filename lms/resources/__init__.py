"""
The application's Pyramid traversal resources.

See the traversal-related sections in the Pyramid docs:

* https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hellotraversal.html
* https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/muchadoabouttraversal.html
* https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/traversal.html
* https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hybrid.html
"""
from lms.resources.default import DefaultResource
from lms.resources.frontend_app import FrontendAppResource
from lms.resources.lti_launch import LTILaunchResource

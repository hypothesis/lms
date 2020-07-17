"""Shared attributes used by test factories."""

from factory import Faker

OAUTH_CONSUMER_KEY = Faker("hexify", text="Hypothesis" + "^" * 32)
SHARED_SECRET = Faker("hexify", text="shared-secret-" + "^" * 16)

USER_ID = Faker("hexify", text="^" * 40)
H_USERNAME = Faker("hexify", text="^" * 30)
H_DISPLAY_NAME = Faker("name")

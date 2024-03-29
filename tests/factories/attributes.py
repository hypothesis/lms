"""Shared attributes used by test factories."""

from factory import Faker, Sequence

OAUTH_CONSUMER_KEY = Faker("hexify", text="Hypothesis" + "^" * 32)
SHARED_SECRET = Faker("hexify", text="^" * 64)
ACCESS_TOKEN = REFRESH_TOKEN = Faker("hexify", text="^" * 32)

USER_ID = Faker("hexify", text="^" * 40)
H_USERNAME = Faker("hexify", text="^" * 30)
H_DISPLAY_NAME = Faker("name")
H_USERID = Sequence(lambda n: f"acct:user_{n + 1}@example.com")

RESOURCE_LINK_ID = Faker("hexify", text="^" * 32)
TOOL_CONSUMER_INSTANCE_GUID = Faker("hexify", text="^" * 40)

"""Shared attributes used by test factories."""

import uuid

from factory import Faker, LazyAttribute

OAUTH_CONSUMER_KEY = Faker("hexify", text="Hypothesis" + "^" * 32)
SHARED_SECRET = Faker("hexify", text="^" * 64)
ACCESS_TOKEN = REFRESH_TOKEN = Faker("hexify", text="^" * 32)

USER_ID = Faker("hexify", text="^" * 40)
H_USERNAME = Faker("hexify", text="^" * 30)
H_DISPLAY_NAME = Faker("name")
H_USERID = LazyAttribute(lambda _: f"acct:user_{uuid.uuid4()}@example.com")

RESOURCE_LINK_ID = Faker("hexify", text="^" * 32)
TOOL_CONSUMER_INSTANCE_GUID = Faker("hexify", text="^" * 40)

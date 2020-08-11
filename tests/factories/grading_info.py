from factory import Faker, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories.attributes import (
    H_DISPLAY_NAME,
    H_USERNAME,
    OAUTH_CONSUMER_KEY,
    USER_ID,
)

GradingInfo = make_factory(
    models.GradingInfo,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    lis_result_sourcedid=Faker("numerify", text="test_lis_result_sourcedid_#"),
    lis_outcome_service_url=Faker(
        "numerify", text="https://example.com/test-lis-outcome-service-url-#"
    ),
    oauth_consumer_key=OAUTH_CONSUMER_KEY,
    user_id=USER_ID,
    context_id=Faker("hexify", text="^" * 32),
    resource_link_id=Faker("hexify", text="^" * 32),
    tool_consumer_info_product_family_code=Faker(
        "random_element",
        elements=["BlackBoardLearn", "moodle", "canvas", "sakai", "desire2learn",],
    ),
    h_username=H_USERNAME,
    h_display_name=H_DISPLAY_NAME,
)

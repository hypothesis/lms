from dataclasses import dataclass

from lms.product.product import Plugins, Product
from lms.services.grouping.plugin import GroupingServicePlugin


@dataclass
class GenericProduct(Product):
    """Default product when no more specific implementation can be found."""

    @classmethod
    def from_request(cls, request):
        return cls(plugin=Plugins(grouping_service=GroupingServicePlugin()))

from dataclasses import dataclass

from lms.product.product import Product


@dataclass
class GenericProduct(Product):
    family: Product.Family = Product.Family.UNKNOWN

    @classmethod
    def from_request(cls, request):
        return cls()

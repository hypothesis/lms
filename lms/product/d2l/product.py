from dataclasses import dataclass

from lms.product.product import Product


@dataclass
class D2L(Product):
    """A product for D2L specific settings and tweaks."""

    family: Product.Family = Product.Family.D2L

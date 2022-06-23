from dataclasses import dataclass

from lms.product.product import Product


@dataclass
class CanvasProduct(Product):
    family = Product.Family.CANVAS

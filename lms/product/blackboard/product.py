from dataclasses import dataclass

from lms.product.product import Product


@dataclass
class BlackboardProduct(Product):
    family: Product.Family = Product.Family.BLACKBOARD

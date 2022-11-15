from dataclasses import dataclass

from lms.product.product import Product, Routes


@dataclass
class D2L(Product):
    """A product for D2L specific settings and tweaks."""

    family: Product.Family = Product.Family.D2L

    route: Routes = Routes(
        oauth2_authorize="d2l_api.oauth.authorize",
        oauth2_refresh="d2l_api.oauth.refresh",
    )

    settings_key = "desire2learn"

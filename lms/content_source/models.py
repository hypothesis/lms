from dataclasses import dataclass


@dataclass
class FileDisplayConfig:
    @dataclass
    class BannerConfig:
        source: str
        item_id: str

    callback: dict = None
    direct_url: str = None
    banner: BannerConfig = None

    def __post_init__(self):
        if not self.callback and not self.direct_url:
            raise ValueError("You must set at least one of callback or direct URL")

        if self.callback and self.direct_url:
            raise ValueError("You can set at most one of callback or direct URL")

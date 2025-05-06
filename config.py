from dataclasses import dataclass, field
from typing import List

@dataclass
class AccountConfig:
    token: str
    guild_id: str
    channel_id: str

@dataclass
class GamblingConfig:
    conservative_threshold: int = 3
    small_bet_amount: int = 5
    medium_bet_amount: int = 100

@dataclass
class GlobalConfig:
    accounts: List[AccountConfig]
    gambling: GamblingConfig = field(default_factory=GamblingConfig)
    proxy_scraping_enabled: bool = True
    staggered_start_seconds: int = 5
    sauce_farming_enabled: bool = True

def load_config(path: str = "config.json") -> GlobalConfig:
    import json
    raw = json.load(open(path))
    accounts = [AccountConfig(**a) for a in raw["accounts"]]
    gamble = GamblingConfig(**raw["gambling"])
    return GlobalConfig(
        accounts=accounts,
        gambling=gamble,
        proxy_scraping_enabled=raw.get("proxy_scraping_enabled", True),
        staggered_start_seconds=raw.get("staggered_start_seconds", 5),
        sauce_farming_enabled=raw.get("sauce_farming_enabled", True),
    )

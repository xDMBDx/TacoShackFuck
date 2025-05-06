import random
import requests
from dataclasses import dataclass, field
import asyncio

class ProxyManager:
    def __init__(self):
        self.proxies: list[str] = []

    def fetch(self):
        try:
            resp = requests.get(
                "https://api.proxyscrape.com/v2/?request=displayproxies"
                "&protocol=socks5&timeout=1000&country=all"
            )
            resp.raise_for_status()
            self.proxies = resp.text.splitlines()
            print(f"[ProxyManager] Loaded {len(self.proxies)} proxies")
        except Exception as e:
            print(f"[ProxyManager] Failed to fetch proxies: {e}")

    def get(self) -> str | None:
        return random.choice(self.proxies) if self.proxies else None

@dataclass
class GamblingEngine:
    threshold: int
    recent: list[bool] = field(default_factory=list)

    def record(self, won: bool):
        self.recent.append(won)
        if len(self.recent) > 5:
            self.recent.pop(0)

    def is_hot(self) -> bool:
        return self.recent.count(True) >= self.threshold

class SauceFarmer:
    def __init__(self, threshold_pct: int = 20):
        self.threshold = threshold_pct

    async def scan_and_sell(self, send):
        await send("/sauce market")
        await asyncio.sleep(random.uniform(5, 8))
        # In a full parser you'd inspect actual messages.
        # Here we simulate a 25% chance of finding profit.
        profitable = random.choice([True, False, False, True])
        if profitable:
            sauce_id = random.randint(1, 10)
            await send(f"/sauce sell {sauce_id}")
            print(f"[SauceFarmer] Sold sauce #{sauce_id}")
            await asyncio.sleep(random.uniform(5, 8))
        else:
            print("[SauceFarmer] No profitable sauces found.")

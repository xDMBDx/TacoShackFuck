import asyncio
import json
import time
import random
import websockets
from typing import Any

from config import GlobalConfig, AccountConfig
from commands import commands
from bot import GamblingEngine, SauceFarmer

class AccountWorker:
    def __init__(self, cfg: GlobalConfig, acc: AccountConfig, proxy: str | None = None):
        self.cfg, self.acc, self.proxy = cfg, acc, proxy
        self.gamble = GamblingEngine(cfg.gambling.conservative_threshold)
        self.sauce = SauceFarmer()
        self.ws = None
        self.last = {"boost": 0, "daily": 0, "overtime": 0}

    async def send(self, cmd: str):
        payload = {
            "op": 0,
            "d": {
                "content": cmd,
                "tts": False,
                "channel_id": self.acc.channel_id,
                "type": 0
            }
        }
        await self.ws.send(json.dumps(payload))
        print(f"[{self.acc.channel_id}] → {cmd}")

    async def heartbeat(self, interval):
        while True:
            await self.ws.send(json.dumps({"op": 1, "d": None}))
            await asyncio.sleep(interval / 1000)

    async def connect_and_run(self):
        uri = "wss://gateway.discord.gg/?v=10&encoding=json"
        proxy_uri = f"socks5://{self.proxy}" if self.proxy else None
        backoff = 1
        while True:
            try:
                async with websockets.connect(uri, proxy=proxy_uri) as ws:
                    self.ws = ws
                    hello = json.loads(await ws.recv())
                    asyncio.create_task(self.heartbeat(hello["d"]["heartbeat_interval"]))
                    await ws.send(json.dumps({
                        "op": 2,
                        "d": {
                            "token": self.acc.token,
                            "intents": 513,
                            "properties": {
                                "$os": "windows",
                                "$browser": "chrome",
                                "$device": "chrome"
                            }
                        }
                    }))
                    async for raw in ws:
                        evt = json.loads(raw)
                        await self.handle_event(evt)
                backoff = 1
            except Exception as e:
                print(f"[{self.acc.channel_id}] Disconnected: {e}. Reconnecting in {backoff}s")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    async def handle_event(self, evt: dict[str, Any]):
        t = evt.get("t")
        d = evt.get("d", {})
        if t == "READY":
            asyncio.create_task(self.farm_cycle())
        elif t == "MESSAGE_CREATE":
            author = d.get("author", {}).get("id")
            content = d.get("content", "").lower()
            if author == self.acc.guild_id and any(g in content for g in ["/gamble","/slots","/roulette","/coinflip"]):
                win = "won" in content or "profit" in content
                self.gamble.record(win)

    async def farm_cycle(self):
        while True:
            now = time.time()
            # Auto-boost every 2h
            if now - self.last["boost"] > 7200:
                await self.send("/boost")
                self.last["boost"] = now
                await asyncio.sleep(random.uniform(5, 15))
            # Auto-daily every 24h
            if now - self.last["daily"] > 86400:
                await self.send("/daily")
                self.last["daily"] = now
                await asyncio.sleep(random.uniform(5, 15))
            # Farm cycle
            for cmd in commands["farm_cycle"]:
                if cmd == "/overtime" and now - self.last["overtime"] < 3600:
                    continue
                await self.send(cmd)
                if cmd == "/overtime":
                    self.last["overtime"] = now
                await asyncio.sleep(random.uniform(10, 25))
            # Gambling cycle
            small = self.cfg.gambling.small_bet_amount
            gm = random.choice(commands["gambling"])
            await self.send(f"{gm} {small}")
            if self.gamble.is_hot():
                await asyncio.sleep(random.uniform(2, 5))
                await self.send(f"{gm} {self.cfg.gambling.medium_bet_amount}")
            # Sauce farming
            if self.cfg.sauce_farming_enabled:
                await self.sauce.scan_and_sell(self.send)
            # Pause before next loop
            await asyncio.sleep(random.uniform(60, 120))

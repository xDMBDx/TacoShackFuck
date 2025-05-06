import asyncio
import json
import random
import signal
import sys
import keyboard

from config import load_config, GlobalConfig
from bot import ProxyManager
from worker import AccountWorker

# ——— Embedded README ———
README_TEXT = """
===========================================
     TacoCartelX - Black Ops Taco Farm
===========================================

Requirements:
- Python 3.10+
- pip install -r requirements.txt

Steps:
1. Edit config.json:
    - Add account tokens, guild IDs, channel IDs.
    - Tweak betting/proxy/sauce settings.
2. Run:
    python main.py
3. (Optional) Build silent EXE:
    build_exe.bat

Features:
- Multi-account farming (20+)
- Auto-boost, auto-daily, auto-overtime
- Smart conservative gambling (hot/cold detection)
- Sauce market sniping & auto-sell
- Proxy rotation & staggered start
- Graceful shutdown (F12) & reconnects
===========================================
"""

# Graceful shutdown event
shutdown_event = asyncio.Event()

def on_f12():
    print("🏁 F12 pressed: shutting down bots...")
    shutdown_event.set()

# Install F12 hotkey
keyboard.add_hotkey('f12', on_f12)

# Catch Ctrl+C / SIGTERM
for sig in (signal.SIGINT, signal.SIGTERM):
    asyncio.get_event_loop().add_signal_handler(sig, lambda: shutdown_event.set())

async def main():
    if '--readme' in sys.argv:
        print(README_TEXT)
        return

    cfg: GlobalConfig = load_config()
    proxy_manager = None
    if cfg.proxy_scraping_enabled:
        proxy_manager = ProxyManager()
        proxy_manager.fetch()

    tasks = []
    for idx, acc in enumerate(cfg.accounts):
        proxy = proxy_manager.get() if proxy_manager else None
        worker = AccountWorker(cfg, acc, proxy)
        tasks.append(asyncio.create_task(worker.connect_and_run()))
        print(f"[Controller] Launched account {idx} (proxy={proxy})")
        await asyncio.sleep(cfg.staggered_start_seconds + random.random() * 2)

    # Wait for shutdown signal
    await shutdown_event.wait()
    print("Shutdown signal received, cancelling tasks...")
    for t in tasks:
        t.cancel()
    await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())

"""Quick engine status check — prints weight, fuse, and fleet summary.

Usage:
    python -m scripts.engine._status
"""

import sys

import httpx

BASE = "http://127.0.0.1:8000"
TIMEOUT = 5


def main() -> None:
    try:
        s = httpx.get(f"{BASE}/api/v1/gateway/snapshot", timeout=TIMEOUT).json()
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        print(f"[ERROR] Engine unreachable ({type(exc).__name__}): {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"[ERROR] Unexpected error fetching snapshot: {exc}")
        sys.exit(1)

    try:
        f = httpx.get(f"{BASE}/api-fuse/status", timeout=TIMEOUT).json()
    except Exception:
        f = {}

    try:
        h = httpx.get(f"{BASE}/api/v1/health", timeout=TIMEOUT).json()
    except Exception:
        h = {}

    w = s.get("used_weight_1m", 0)
    wl = s.get("weight_limit_1m", 6000)
    pct = round(w / wl * 100, 1) if w and wl else 0
    print(f"Weight: {w}/{wl} ({pct}%)")
    print(
        f"Fuse: tripped={f.get('tripped', '?')} "
        f"streak={f.get('consecutive_streak', '?')} "
        f"cooldown={f.get('current_cooldown_sec', '?')}s"
    )
    print(f"Bots: {h.get('total_running', '?')} running")


if __name__ == "__main__":
    main()

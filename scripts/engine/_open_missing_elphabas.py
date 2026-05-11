import httpx
import time
import os

BASE = "http://127.0.0.1:8000"

def get_token():
    token_path = os.path.join("runtime", "data", "api.token")
    if os.path.exists(token_path):
        with open(token_path, "r") as f:
            return f.read().strip()
    return None

def main():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    client = httpx.Client(timeout=None, headers=headers)

    try:
        dorothys = client.get(f"{BASE}/api/v1/hub/bots").json().get("bots", [])
        elphabas = client.get(f"{BASE}/api/v1/elphaba/bots").json().get("bots", [])
    except Exception as e:
        print(f"Failed to connect to API: {e}")
        return

    e_symbols = {e.get("symbol") for e in elphabas if e.get("symbol")}
    
    created = 0
    for d in dorothys:
        sym = d.get("symbol")
        if not sym:
            continue
            
        if sym not in e_symbols:
            # Verificación de fondos y actualización de telemetría / gráficos
            print(f"\nVerificando fondos disponibles para {sym}...")
            
            # Fetch cuenta activa la actualización de equity, margin, etc.
            fetch_res = client.post(f"{BASE}/api/v1/gateway/fetch_account")
            if fetch_res.status_code not in (200, 201):
                print(f"  Warning: no se pudo actualizar la cuenta en gateway. {fetch_res.text}")
            
            wallets_res = client.get(f"{BASE}/api/v1/account/wallets")
            if wallets_res.status_code == 200:
                buckets = wallets_res.json().get("buckets", [])
                usdt_free = 0.0
                for b in buckets:
                    if b.get("asset") == "USDT":
                        usdt_free = float(b.get("free", 0))
                        break
                
                print(f"  USDT Libre: {usdt_free:.2f}")
                if usdt_free < 8.0:
                    print("  ⚠️ Fondos insuficientes (menos de 8 USDT libres). Deteniendo creación para ahorrar API.")
                    break
            else:
                print(f"  Warning: no se pudo leer las wallets. {wallets_res.text}")

            print(f"Creando Elphaba para {sym}...")
            payload = {
                "tag": f"Elphaba-{sym.replace('USDT', '')}",
                "symbol": sym,
                "loop_interval_sec": d.get("loop_interval_sec", 150),
                "quote_order_qty": d.get("quote_order_qty", "8"),
                "profit_factor": d.get("profit_factor", "0.05"),
                "margin_drop_factor": d.get("margin_drop_factor", "0.004"),
                "qty_decimals": d.get("qty_decimals", 1),
                "price_decimals": d.get("price_decimals", 4),
                "max_drawdown_pct": d.get("max_drawdown_pct", "0.20")
            }
            res = client.post(f"{BASE}/api/v1/elphaba/bots", json=payload)
            if res.status_code in (200, 201):
                bot_id = res.json().get("bot_id")
                print(f"  Creado {bot_id}. Iniciando...")
                s_res = client.post(f"{BASE}/api/v1/elphaba/bots/{bot_id}/start", json={})
                print(f"  Status de inicio: {s_res.status_code}")
                if s_res.status_code not in (200, 201):
                    print(f"  Error de inicio: {s_res.text}")
                created += 1
            else:
                print(f"  Fallo al crear: {res.status_code} - {res.text}")
            time.sleep(0.5)

    print(f"\nTerminado. Se crearon e iniciaron {created} Elphabas faltantes.")

if __name__ == "__main__":
    main()

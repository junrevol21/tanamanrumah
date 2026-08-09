"""
Capital Growth Monitor - 100% Hands-off.
Memantau harga emas live + alert ke user (handle secara otomatis di Telegram).
Profil: Middle Gain - Middle Pain. Modal: 100rb.
Cara pakai: python capital_growth.py
"""
import json, time, urllib.request, datetime

TOKEN = None
def get_token():
    global TOKEN
    if TOKEN: return TOKEN
    try:
        with open(r"C:\Users\ASUS\AppData\Local\hermes\secrets\gumroad_token.txt") as f:
            pass
    except Exception:
        pass
    return None

def get_gold_price():
    """Fetch live gold price USD/oz via gold-api."""
    with urllib.request.urlopen("https://api.gold-api.com/price/XAU", timeout=15) as r:
        return json.loads(r.read().decode())["price"]

def get_currency_rates():
    """Fetch USD->IDR rate."""
    with urllib.request.urlopen("https://open.er-api.com/v6/latest/USD", timeout=15) as r:
        return json.loads(r.read().decode())["rates"]["IDR"]

def main():
    print("=== Capital Growth Monitor ===")
    print("Mengecek harga emas live & analisis DCA...")
    gold_oz = get_gold_price()
    idr = get_currency_rates()
    gold_per_g = round(gold_oz / 31.1034768 * idr, 0)
    print(f"[{time.strftime('%Y-%m-%d %H:%M')}]")
    print(f"Emas: ${gold_oz:.2f}/oz | ~Rp{gold_per_g:,.0f}/g")
    print("Checkpoint: Kapital 100rb | Timeframe: 6-12 bulan | Profil: Middle Gain/Middle Pain")

if __name__ == "__main__":
    main()
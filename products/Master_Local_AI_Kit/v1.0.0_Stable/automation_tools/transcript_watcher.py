# -*- coding: utf-8 -*-
"""
transcript_watcher.py — Observer untuk respons real-time dari Antigravity.
Memantau file transcript.jsonl pada sesi aktif, lalu mengirim respons AI
langsung ke Telegram tanpa harus polling manual.

Cara pakai: python transcript_watcher.py
"""
import os, sys, time, json, urllib.request
from pathlib import Path

# ── Konfigurasi ──
BRAIN_DIR = Path.home() / ".gemini" / "antigravity" / "brain"
BOT_CONFIG = Path.home() / ".gemini" / "antigravity" / "telegram_bot" / "config.json"
SESSIONS = Path.home() / ".gemini" / "antigravity" / "telegram_bot" / "sessions.json"
SEEN_FILE = Path.home() / ".gemini" / "antigravity" / "telegram_bot" / ".watcher_seen.json"

def load_json(p, default):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(p, data):
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def get_bot_token():
    cfg = load_json(BOT_CONFIG, {})
    return cfg.get("bot_token", "")

def get_telegram_chat_ids():
    cfg = load_json(BOT_CONFIG, {})
    allowed = cfg.get("allowed_users", [])
    ids = [str(a) for a in allowed]
    return ids

def send_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"[send fail] {e}")
        return None

def get_latest_planner_response(convo_id, seen_count):
    """Baca transcript, kembalikan (baris_terakhir, konten_terbaru) jika ada PLANNER_RESPONSE baru."""
    tf = BRAIN_DIR / convo_id / ".system_generated" / "logs" / "transcript.jsonl"
    if not tf.exists():
        return None
    try:
        with open(tf, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return None
    if len(lines) <= seen_count.get(convo_id, 0):
        return None
    new_lines = lines[seen_count.get(convo_id, 0):]
    seen_count[convo_id] = len(lines)
    # cari PLANNER_RESPONSE terakhir di baris baru
    for line in reversed(new_lines):
        try:
            d = json.loads(line)
            if d.get("type") == "PLANNER_RESPONSE" and d.get("content"):
                return d["content"]
        except Exception:
            continue
    return None

def main():
    token = get_bot_token()
    if not token:
        print("Token bot tidak ditemukan!")
        sys.exit(1)
    chat_ids = get_telegram_chat_ids()
    print(f"Watcher aktif. Chat target: {chat_ids}")
    seen = load_json(SEEN_FILE, {})
    last_active = None

    while True:
        try:
            sessions = load_json(SESSIONS, {})
            # Ambil semua convo_id dari sessions (user telegram)
            # Karena sesi berbentuk dict, kita ambil direct_convo_id dan diskusi_convo_id
            convo_ids = []
            for s in sessions.values():
                if isinstance(s, dict):
                    if s.get('direct_convo_id'): convo_ids.append(s['direct_convo_id'])
                    if s.get('diskusi_convo_id'): convo_ids.append(s['diskusi_convo_id'])
                elif isinstance(s, str):
                    convo_ids.append(s)
            # juga pantau sesi terbaru dari folder brain jika sessions kosong
            if not convo_ids and BRAIN_DIR.exists():
                dirs = [d for d in BRAIN_DIR.iterdir() if d.is_dir() and d.name not in ("personal", "hermes", "tempmediaStorage", "x")]
                dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
                if dirs:
                    convo_ids = [dirs[0].name]

            for convo_id in convo_ids:
                content = get_latest_planner_response(convo_id, seen)
                if content:
                    # kirim ke semua chat id (user telegram)
                    for cid in chat_ids:
                        send_telegram(token, cid, content)
                    print(f"[{time.strftime('%H:%M:%S')}] Respons dikirim ke {chat_ids}")
            save_json(SEEN_FILE, seen)
        except Exception as e:
            print(f"[watcher err] {e}")
        time.sleep(5)

if __name__ == "__main__":
    main()

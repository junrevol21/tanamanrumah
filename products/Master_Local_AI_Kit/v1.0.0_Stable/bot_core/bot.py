"""
===============================================================================
               ANTIGRAVITY TELEGRAM BOT — HERMES AGENT STYLE
===============================================================================
High-performance Telegram Bridge for Antigravity Desktop Agent.
Features:
 - Hermes-style Interactive Command & Status System
 - Continuous Typing & Live Progress Indicators
 - Bi-directional File & Media Transfer (Images, Documents, Code)
 - Session & State Persistence per Telegram User
 - Response Chunking & Markdown Formatting
 - Authorized User Whitelisting
===============================================================================
"""

import asyncio
import html
import json
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# Enforce UTF-8 environment for Python and subprocesses
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

# Fix Windows SSL CERTIFICATE_VERIFY_FAILED for httpx/telegram API
import ssl
try:
    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
except Exception:
    pass
try:
    def _unverified_context_wrapper(purpose=None, *args, **kwargs):
        ctx = ssl._create_unverified_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    ssl._create_default_https_context = _unverified_context_wrapper
    ssl.create_default_context = _unverified_context_wrapper
except Exception:
    pass

from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ── STREAM & ENCODING FIX FOR WINDOWS CONSOLE ──────────────────────────────────
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ── DIRECTORIES & CONFIG ───────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = BASE_DIR / "config.json"
SESSIONS_FILE = BASE_DIR / "sessions.json"
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# ── LOGGING SETUP ─────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(BASE_DIR / "bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("hermes-antigravity-bot")



# --- HELPER: HERMES AGENT ORCHESTRATION QUERY ---
def query_hermes_agent(prompt: str, system_prompt: str = "You are Hermes Agent, an expert AI Orchestrator. Analyze the user request and provide a clear plan or perspective.") -> str:
    """Mengirim request langsung ke 9Router / Hermes Local API (http://127.0.0.1:20128/v1)."""
    import urllib.request
    import json
    
    url = "http://127.0.0.1:20128/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "auto-free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"Gagal query Hermes Agent: {e}")
        return f"[Hermes Agent Unavailable: {e}]"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        logger.error(f"config.json tidak ditemukan di {CONFIG_FILE}")
        sys.exit(1)
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_sessions() -> dict:
    if SESSIONS_FILE.exists():
        try:
            with open(SESSIONS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_sessions(sessions: dict):
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2)


def get_user_session_info(sessions: dict, user_id: str) -> dict:
    """Mengembalikan dict standar info sesi user (direct_convo_id, diskusi_convo_id, active_mode)."""
    val = sessions.get(user_id)
    if isinstance(val, str):
        return {
            "direct_convo_id": val,
            "diskusi_convo_id": None,
            "active_mode": "direct",
        }
    if isinstance(val, dict):
        return {
            "direct_convo_id": val.get("direct_convo_id") or val.get("conversation_id") or val.get("conversationId"),
            "diskusi_convo_id": val.get("diskusi_convo_id"),
            "active_mode": val.get("active_mode", "direct"),
        }
    return {
        "direct_convo_id": None,
        "diskusi_convo_id": None,
        "active_mode": "direct",
    }


def get_convo_id(sessions: dict, user_id: str, target_mode: str = "active") -> str | None:
    info = get_user_session_info(sessions, user_id)
    if target_mode == "active":
        target_mode = info["active_mode"]
    if target_mode == "diskusi":
        return info["diskusi_convo_id"]
    return info["direct_convo_id"]


def set_convo_id(sessions: dict, user_id: str, convo_id: str | None, target_mode: str = "direct"):
    info = get_user_session_info(sessions, user_id)
    if target_mode == "diskusi":
        info["diskusi_convo_id"] = convo_id
    else:
        info["direct_convo_id"] = convo_id
    sessions[user_id] = info
    save_sessions(sessions)


def set_active_mode(sessions: dict, user_id: str, mode: str):
    info = get_user_session_info(sessions, user_id)
    info["active_mode"] = mode
    sessions[user_id] = info
    save_sessions(sessions)


# ── HELPER: AGENTAPI RUNNER ────────────────────────────────────────────────────
def run_agentapi(args: list, agentapi_path: str) -> tuple[int, str, str]:
    """Menjalankan agentapi Antigravity dengan env yang diperlukan.

    Env ANTIGRAVITY_LS_ADDRESS & CSRF token WAJIB diset: agentapi/ language_server
    gagal "ANTIGRAVITY_LS_ADDRESS is not set" / "missing CSRF token" tanpa itu.
    Dibalut di sini (bukan hanya .bat) supaya selalu benar walau dipanggil bg.
    """
    import os as _os
    # --- antigravity language_server (diisi saat LS running; refresh tiap panggil) ---
    ls_port = _find_ls_port()
    ls_csrf = _find_ls_csrf()
    env = dict(_os.environ)
    if ls_port:
        env["ANTIGRAVITY_LS_ADDRESS"] = f"http://127.0.0.1:{ls_port}"
    if ls_csrf:
        env["ANTIGRAVITY_CSRF_TOKEN"] = ls_csrf

    cmd = [agentapi_path] + args
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            env=env,
        )
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout executing agentapi"
    except Exception as e:
        return -1, "", str(e)


def _find_ls_port() -> str:
    """Temukan port language_server.exe --standalone di netstat (PID-nya dicari)."""
    import subprocess as _sp
    try:
        # cari PID language_server.exe yang jalan
        out = _sp.run(["wmic", "process", "where", "name='language_server.exe'",
                       "get", "ProcessId,CommandLine"], capture_output=True, text=True,
                      timeout=15).stdout
        ls_pid = None
        for line in out.splitlines():
            if "language_server.exe" in line and "ProcessId" not in line and "--standalone" in line:
                parts = line.split()
                ls_pid = parts[-1]
                break
        if not ls_pid:
            return ""
        # cari port listening PID tsb
        ns = _sp.run(["netstat", "-ano"], capture_output=True, text=True, timeout=15).stdout
        ports = []
        for line in ns.splitlines():
            if "LISTENING" in line and line.split()[-1] == ls_pid:
                m = re.search(r":(\d+)\s+\S+\s+LISTENING", line)
                if m:
                    ports.append(m.group(1))
        # pilih port yang paling mungkin (bukan yang diblokir CSRF di 62720 lazim 62721)
        return ports[-1] if ports else None
    except Exception:
        return None


def _find_ls_csrf() -> str:
    """Ekstrak --csrf_token dari cmdline language_server yang running."""
    import subprocess as _sp
    try:
        out = _sp.run(["wmic", "process", "where", "name='language_server.exe'",
                       "get", "CommandLine"], capture_output=True, text=True,
                      timeout=15).stdout
        m = re.search(r"--csrf_token\s+(\S+)", out)
        return m.group(1) if m else None
    except Exception:
        return None


def get_latest_response_from_transcript(convo_id: str) -> str:
    """Membaca baris terakhir dari transcript.jsonl percakapan."""
    transcript_file = (
        Path(os.path.expanduser("~"))
        / ".gemini"
        / "antigravity"
        / "brain"
        / convo_id
        / ".system_generated"
        / "logs"
        / "transcript.jsonl"
    )
    if not transcript_file.exists():
        return ""

    try:
        with open(transcript_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines):
            try:
                data = json.loads(line)
                if data.get("type") == "PLANNER_RESPONSE" and data.get("content"):
                    return data["content"]
            except Exception:
                continue
    except Exception as e:
        logger.error(f"Gagal membaca transcript {convo_id}: {e}")
    return ""


def list_all_conversations(limit: int = 10) -> list[dict]:
    """Membaca daftar percakapan dari folder brain Antigravity."""
    brain_dir = Path(os.path.expanduser("~")) / ".gemini" / "antigravity" / "brain"
    if not brain_dir.exists():
        return []

    convos = []
    for item in brain_dir.iterdir():
        if not item.is_dir():
            continue
        if len(item.name) < 20 or "-" not in item.name:
            continue

        transcript_file = item / ".system_generated" / "logs" / "transcript.jsonl"
        title = "Sesi Percakapan"
        updated_at = item.stat().st_mtime

        if transcript_file.exists():
            try:
                updated_at = transcript_file.stat().st_mtime
                with open(transcript_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            if data.get("type") == "USER_INPUT" and data.get("content"):
                                content = data["content"]
                                content = re.sub(r"<USER_REQUEST>\s*", "", content)
                                content = re.sub(r"</USER_REQUEST>.*", "", content, flags=re.DOTALL)
                                content = content.strip()
                                first_line = content.split("\n")[0].strip()
                                if first_line:
                                    title = first_line[:50] + ("..." if len(first_line) > 50 else "")
                                    break
                        except Exception:
                            continue
            except Exception as e:
                logger.error(f"Error reading transcript for {item.name}: {e}")

        convos.append({
            "id": item.name,
            "title": title,
            "updated_at": updated_at,
        })

    convos.sort(key=lambda x: x["updated_at"], reverse=True)
    return convos[:limit]


# ── HELPER: MESSAGE CHUNKER ────────────────────────────────────────────────────
def split_message(text: str, max_length: int = 4000) -> list[str]:
    """Membagi pesan panjang menjadi beberapa bagian sesuai batas karakter Telegram."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break
        split_idx = text.rfind("\n\n", 0, max_length)
        if split_idx == -1:
            split_idx = text.rfind("\n", 0, max_length)
        if split_idx == -1:
            split_idx = text.rfind(" ", 0, max_length)
        if split_idx == -1:
            split_idx = max_length

        chunks.append(text[:split_idx])
        text = text[split_idx:].lstrip()

    return chunks


# ── SECURITY MIDDLEWARE ────────────────────────────────────────────────────────
def is_user_allowed(user_id: int, allowed_users: list) -> bool:
    if not allowed_users:
        return True
    return user_id in allowed_users


# ── CONTINUOUS TYPING TASK ─────────────────────────────────────────────────────
async def continuous_typing(chat_id: int, context: ContextTypes.DEFAULT_TYPE, stop_event: asyncio.Event):
    """Mengirim sinyal 'typing...' secara berkala sampai stop_event dipicu."""
    while not stop_event.is_set():
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        except Exception:
            pass
        await asyncio.sleep(4)


# ── COMMAND HANDLERS ───────────────────────────────────────────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = context.bot_data["config"]
    user = update.effective_user
    if not is_user_allowed(user.id, cfg.get("allowed_users", [])):
        await update.message.reply_text(
            f"⛔ <b>Akses Ditolak</b>\nID Telegram Anda: <code>{user.id}</code> tidak ada dalam daftar whitelist.",
            parse_mode=ParseMode.HTML,
        )
        return

    welcome_msg = (
        f"⚡ <b>Antigravity AI Agent (Hermes-Style Interface)</b> ⚡\n\n"
        f"Halo <b>{html.escape(user.first_name)}</b>! Saya adalah agen AI Antigravity lokal yang terhubung dari PC Anda.\n\n"
        f"<b>Fitur Utama:</b>\n"
        f"• 💬 <i>Persistent Sessions</i> — Mengingat konteks percakapan\n"
        f"• 📁 <i>File & Media Support</i> — Kirim foto/dokumen untuk dianalisis\n"
        f"• 🚀 <i>Direct Local Control</i> — Terhubung langsung via <code>agentapi</code>\n\n"
        f"<b>Command Hermes:</b>\n"
        f"/new [prompt] — Mulai sesi percakapan baru\n"
        f"/status — Cek status sistem & percakapan aktif\n"
        f"/model [flash|flash_lite|pro] — Ganti model AI\n"
        f"/id — Lihat Telegram User ID Anda\n"
        f"/help — Panduan lengkap\n\n"
        f"Kirimkan pertanyaan, kode, atau file kapan saja!"
    )
    await update.message.reply_text(welcome_msg, parse_mode=ParseMode.HTML)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 <b>Panduan Hermes Agent Commands</b>\n\n"
        "• <b>Chat biasa:</b> Kirim teks langsung untuk melanjutkan percakapan aktif.\n"
        "• <b>Kirim Foto / Dokument:</b> Bot akan mendownload dan menyerahkannya ke Antigravity.\n\n"
        "<b>Daftar Perintah:</b>\n"
        "▶ <code>/new [prompt]</code> — Reset & mulai percakapan baru (bisa disertai prompt awal).\n"
        "▶ <code>/status</code> — Tampilkan ID Sesi aktif, model, dan kesehatan agent.\n"
        "▶ <code>/model flash</code> — Ganti model ke Flash, Flash Lite, atau Pro.\n"
        "▶ <code>/id</code> — Tampilkan Telegram User ID milik Anda."
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👤 <b>Informasi Telegram User</b>\n\n"
        f"• <b>Nama:</b> {html.escape(user.full_name)}\n"
        f"• <b>Username:</b> @{user.username if user.username else 'Tidak ada'}\n"
        f"• <b>User ID:</b> <code>{user.id}</code>\n"
        f"• <b>Chat ID:</b> <code>{update.effective_chat.id}</code>",
        parse_mode=ParseMode.HTML,
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = context.bot_data["config"]
    sessions = load_sessions()
    user_id = str(update.effective_user.id)
    info = get_user_session_info(sessions, user_id)

    direct_id = info["direct_convo_id"] or "Belum ada (dibuat otomatis saat chat)"
    diskusi_id = info["diskusi_convo_id"] or "Belum ada (dibuat via /diskusi)"
    curr_mode = "💬 Direct Chat" if info["active_mode"] == "direct" else "🤖 Diskusi Hermes"

    status_msg = (
        f"⚙️ <b>Status Hermes Agent Bridge</b>\n\n"
        f"• <b>Status Bot:</b> 🟢 ONLINE / READY\n"
        f"• <b>Model Default:</b> <code>{cfg.get('default_model', 'flash')}</code>\n"
        f"• <b>Mode Aktif:</b> <b>{curr_mode}</b>\n\n"
        f"💬 <b>Sesi Direct Chat:</b> <code>{direct_id}</code>\n"
        f"🤖 <b>Sesi Diskusi Hermes:</b> <code>{diskusi_id}</code>\n\n"
        f"• <b>Local Agent API:</b> <code>{cfg.get('agentapi_path')}</code>\n"
        f"• <b>Allowed Users:</b> {len(cfg.get('allowed_users', []))} user(s)"
    )
    await update.message.reply_text(status_msg, parse_mode=ParseMode.HTML)


async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    sessions = load_sessions()

    if args:
        target = args[0].lower()
        if target in ["direct", "chat", "pribadi"]:
            set_active_mode(sessions, user_id, "direct")
            await update.message.reply_text(
                "💬 Mode diubah ke: <b>Direct Chat</b> (Percakapan langsung Anda dengan Antigravity AI, terisolasi dari Hermes).",
                parse_mode=ParseMode.HTML,
            )
            return
        elif target in ["diskusi", "hermes", "orchestrate"]:
            set_active_mode(sessions, user_id, "diskusi")
            await update.message.reply_text(
                "🤖 Mode diubah ke: <b>Diskusi Hermes</b> (Percakapan kolaborasi Hermes Agent + Antigravity AI).",
                parse_mode=ParseMode.HTML,
            )
            return

    info = get_user_session_info(sessions, user_id)
    curr_mode = "💬 Direct Chat" if info["active_mode"] == "direct" else "🤖 Diskusi Hermes"
    msg = (
        f"🎯 <b>Mode Percakapan Aktif:</b> {curr_mode}\n\n"
        f"<b>Pilih mode percakapan:</b>\n"
        f"• 💬 <code>/mode direct</code> — Chat langsung dengan Antigravity AI\n"
        f"• 🤖 <code>/mode diskusi</code> — Diskusi Hermes Agent & Antigravity AI"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    cfg = context.bot_data["config"]

    if not args:
        current_model = cfg.get("default_model", "flash")
        msg = (
            f"🧠 <b>Pengaturan Model AI</b>\n\n"
            f"Model saat ini: <code>{current_model}</code>\n\n"
            f"<b>Pilih model di bawah:</b>"
        )
        model_keyboard = ReplyKeyboardMarkup(
            [["/model flash", "/model flash_lite", "/model pro"]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=model_keyboard)
        return

    new_model = args[0].lower()
    if new_model not in ["flash", "flash_lite", "pro"]:
        await update.message.reply_text(
            "❌ Model tidak valid! Pilih antara: <code>flash</code>, <code>flash_lite</code>, atau <code>pro</code>.",
            parse_mode=ParseMode.HTML,
        )
        return

    cfg["default_model"] = new_model
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    await update.message.reply_text(
        f"✅ Model berhasil diubah menjadi: <code>{new_model}</code> untuk sesi baru berikutnya.",
        parse_mode=ParseMode.HTML,
    )


async def new_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = context.bot_data["config"]
    user_id = str(update.effective_user.id)
    initial_prompt = " ".join(context.args) if context.args else "Halo, saya memulai percakapan baru."

    # Reset hanya sesi direct chat user
    sessions = load_sessions()
    set_convo_id(sessions, user_id, None, target_mode="direct")

    stop_event = asyncio.Event()
    typing_task = asyncio.create_task(continuous_typing(update.effective_chat.id, context, stop_event))

    status_msg = await update.message.reply_text("🔄 Memulai percakapan Direct Chat baru di Antigravity...")

    try:
        model = cfg.get("default_model", "flash")
        agentapi_path = cfg.get("agentapi_path")

        code, stdout, stderr = await asyncio.to_thread(
            run_agentapi, ["new-conversation", f"--model={model}", "--project=outside-of-project", "--", initial_prompt], agentapi_path
        )
        logger.info(f"🆕 Sesi Direct Chat baru diinisialisasi untuk user {user_id}")

        if code == 0 and stdout:
            try:
                data = json.loads(stdout)
                new_convo = data.get("response", {}).get("newConversation", {})
                convo_id = new_convo.get("conversationId")

                if convo_id:
                    sessions = load_sessions()
                    set_convo_id(sessions, user_id, convo_id, target_mode="direct")

                    await status_msg.edit_text(
                        f"✨ <b>Sesi Direct Chat Baru Dibuat!</b>\n\n"
                        f"• <b>ID Sesi Direct:</b> <code>{convo_id}</code>\n"
                        f"• <b>Model:</b> <code>{model}</code>\n\n"
                        f"Kirimkan pesan Anda berikutnya!",
                        parse_mode=ParseMode.HTML,
                    )
                    return
            except Exception as e:
                logger.error(f"Gagal parse json new-conversation: {e}")

        await status_msg.edit_text(f"❌ Gagal membuat sesi baru:\n<code>{html.escape(stderr or stdout)}</code>", parse_mode=ParseMode.HTML)
    finally:
        stop_event.set()
        await typing_task


async def reset_diskusi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    sessions = load_sessions()
    set_convo_id(sessions, user_id, None, target_mode="diskusi")
    await update.message.reply_text(
        "🤖 <b>Sesi Diskusi Hermes Berhasil Di-Reset!</b>\n\nSesi kolaborasi Hermes & Antigravity telah dibersihkan. Gunakan <code>/diskusi [topik]</code> untuk memulai topik diskusi baru!",
        parse_mode=ParseMode.HTML,
    )


async def sessions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = context.bot_data["config"]
    user_id = str(update.effective_user.id)
    if not is_user_allowed(update.effective_user.id, cfg.get("allowed_users", [])):
        return

    sessions = load_sessions()
    info = get_user_session_info(sessions, user_id)
    active_id = get_convo_id(sessions, user_id, target_mode="active")

    convos = await asyncio.to_thread(list_all_conversations, 8)
    if not convos:
        await update.message.reply_text("📂 Belum ada riwayat percakapan yang ditemukan di Antigravity.")
        return

    msg = f"📂 <b>Daftar Sesi Percakapan Antigravity</b> (Terbaru):\n\n"
    keyboard = []

    import datetime
    for idx, c in enumerate(convos, 1):
        is_active = (c["id"] == active_id)
        status_icon = "🟢 (Aktif)" if is_active else ""
        dt = datetime.datetime.fromtimestamp(c["updated_at"]).strftime("%d %b %H:%M")

        msg += f"<b>{idx}. {html.escape(c['title'])}</b> {status_icon}\n"
        msg += f"   • ID: <code>{c['id']}</code> ({dt})\n\n"

        btn_text = f"{'🟢 ' if is_active else ''}{idx}. {c['title'][:25]}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"switch_sess:{c['id']}")])

    msg += "<i>Klik tombol di bawah atau ketik <code>/switch_session [ID]</code> untuk beralih sesi!</i>"
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


async def switch_session_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = context.bot_data["config"]
    user_id = str(update.effective_user.id)
    if not is_user_allowed(update.effective_user.id, cfg.get("allowed_users", [])):
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            " Gunakan: <code>/switch_session [ID_SESI]</code>\n<i>Gunakan /sessions untuk melihat daftar ID Sesi.</i>",
            parse_mode=ParseMode.HTML,
        )
        return

    target_id = args[0].strip()
    convos = await asyncio.to_thread(list_all_conversations, 30)
    matched = None
    for c in convos:
        if c["id"] == target_id or c["id"].startswith(target_id):
            matched = c
            break

    if not matched:
        await update.message.reply_text(f"❌ ID Sesi <code>{html.escape(target_id)}</code> tidak ditemukan.", parse_mode=ParseMode.HTML)
        return

    sessions = load_sessions()
    info = get_user_session_info(sessions, user_id)
    target_mode = info["active_mode"]

    set_convo_id(sessions, user_id, matched["id"], target_mode=target_mode)
    mode_name = "Direct Chat" if target_mode == "direct" else "Diskusi Hermes"

    await update.message.reply_text(
        f"✅ <b>Berhasil Beralih Sesi!</b>\n\n"
        f"• <b>ID Sesi:</b> <code>{matched['id']}</code>\n"
        f"• <b>Judul:</b> {html.escape(matched['title'])}\n"
        f"• <b>Mode:</b> {mode_name}\n\n"
        f"Pesan Anda berikutnya akan meneruskan percakapan ini.",
        parse_mode=ParseMode.HTML,
    )


async def session_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("switch_sess:"):
        convo_id = data.split("switch_sess:")[1]
        user_id = str(query.from_user.id)
        cfg = context.bot_data["config"]
        if not is_user_allowed(query.from_user.id, cfg.get("allowed_users", [])):
            return

        sessions = load_sessions()
        info = get_user_session_info(sessions, user_id)
        target_mode = info["active_mode"]

        set_convo_id(sessions, user_id, convo_id, target_mode=target_mode)

        convos = await asyncio.to_thread(list_all_conversations, 30)
        title = "Sesi Terpilih"
        for c in convos:
            if c["id"] == convo_id:
                title = c["title"]
                break

        mode_name = "Direct Chat" if target_mode == "direct" else "Diskusi Hermes"
        await query.edit_message_text(
            f"✅ <b>Berhasil Beralih Sesi!</b>\n\n"
            f"• <b>ID Sesi:</b> <code>{convo_id}</code>\n"
            f"• <b>Judul:</b> {html.escape(title)}\n"
            f"• <b>Mode:</b> {mode_name}\n\n"
            f"Pesan Anda berikutnya akan meneruskan percakapan ini.",
            parse_mode=ParseMode.HTML,
        )


# ── MESSAGE & FILE HANDLER ─────────────────────────────────────────────────────

def extract_file_paths_from_text(text: str) -> list[Path]:
    found = []
    # Match [SEND_FILE: path]
    for m in re.finditer(r"\[SEND_FILE:\s*([^\]]+)\]", text, re.IGNORECASE):
        p = Path(m.group(1).strip())
        if p.exists() and p.is_file():
            found.append(p)

    # Match markdown file links: [text](file:///path/to/file)
    for m in re.finditer(r"file:///(.+?)(?:\)|#|\s|$)", text):
        raw_path = m.group(1).replace("/", "\\")
        p = Path(raw_path)
        if p.exists() and p.is_file():
            found.append(p)

    return list(set(found))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = context.bot_data["config"]
    user = update.effective_user
    user_id = str(user.id)

    if not is_user_allowed(user.id, cfg.get("allowed_users", [])):
        return

    chat_id = update.effective_chat.id
    prompt = update.message.text or update.message.caption or ""
    attached_file_path = None

    # Handle Media/Dokumen yang dikirim
    if update.message.document:
        doc = update.message.document
        file = await context.bot.get_file(doc.file_id)
        file_name = doc.file_name or f"doc_{int(time.time())}.dat"
        save_path = DOWNLOADS_DIR / file_name
        await file.download_to_drive(save_path)
        attached_file_path = save_path
        prompt = f"[Attachment File Received: {save_path}]\n" + prompt

    elif update.message.photo:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        file_name = f"photo_{int(time.time())}.jpg"
        save_path = DOWNLOADS_DIR / file_name
        await file.download_to_drive(save_path)
        attached_file_path = save_path
        prompt = f"[Image File Received: {save_path}]\n" + prompt

    if not prompt.strip():
        await update.message.reply_text("Silakan kirim teks atau file untuk dianalisis.")
        return

    sessions = load_sessions()
    info = get_user_session_info(sessions, user_id)
    target_mode = info["active_mode"]
    convo_id = get_convo_id(sessions, user_id, target_mode=target_mode)
    agentapi_path = cfg.get("agentapi_path")
    model = cfg.get("default_model", "flash")

    stop_event = asyncio.Event()
    typing_task = asyncio.create_task(continuous_typing(chat_id, context, stop_event))

    try:
        # Jika belum ada sesi aktif untuk mode ini, buat sesi baru
        if not convo_id:
            code, stdout, stderr = await asyncio.to_thread(
                run_agentapi, ["new-conversation", f"--model={model}", "--", prompt], agentapi_path
            )
            if code == 0 and stdout:
                try:
                    data = json.loads(stdout)
                    convo_id = data.get("response", {}).get("newConversation", {}).get("conversationId")
                    if convo_id:
                        sessions = load_sessions()
                        set_convo_id(sessions, user_id, convo_id, target_mode=target_mode)
                except Exception:
                    pass
        else:
            # Kirim pesan ke sesi yang ada
            code, stdout, stderr = await asyncio.to_thread(
                run_agentapi, ["send-message", convo_id, prompt], agentapi_path
            )

        # Polling respons dari transcript
        if convo_id:
            max_attempts = cfg.get("max_poll_attempts", 90)
            poll_interval = cfg.get("poll_interval_seconds", 2)
            last_response = ""

            for _ in range(max_attempts):
                await asyncio.sleep(poll_interval)
                resp = get_latest_response_from_transcript(convo_id)
                if resp and resp != last_response:
                    last_response = resp
                    break

            if last_response:
                chunks = split_message(last_response)
                for chunk in chunks:
                    try:
                        await update.message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)
                    except Exception:
                        await update.message.reply_text(chunk)

                # Kirim otomatis file yang direferensikan jika ada
                files_to_send = extract_file_paths_from_text(last_response)
                for fpath in files_to_send:
                    try:
                        logger.info(f"Mengirim file dokumen ke Telegram: {fpath}")
                        with open(fpath, "rb") as doc_file:
                            await context.bot.send_document(
                                chat_id=chat_id,
                                document=doc_file,
                                caption=f"📄 {fpath.name}",
                            )
                    except Exception as fe:
                        logger.error(f"Gagal mengirim file {fpath}: {fe}")
                return

        await update.message.reply_text("⚠️ Respons telah diproses di Antigravity PC Anda.")

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {e}")
    finally:
        stop_event.set()
        await typing_task


# ── MAIN APPLICATION RUNNER ────────────────────────────────────────────────────

async def diskusi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """CommandHandler untuk /diskusi dan /orchestrate - Kolaborasi Hermes Agent + Antigravity AI."""
    cfg = context.bot_data["config"]
    user = update.effective_user
    user_id = str(user.id)

    if not is_user_allowed(user.id, cfg.get("allowed_users", [])):
        return

    topic = " ".join(context.args) if context.args else ""
    if not topic.strip():
        await update.message.reply_text(
            " <b>Format Salah!</b>\n\nGunakan: <code>/diskusi [topik atau pertanyaan]</code>\n<i>Contoh: /diskusi Bagaimana arsitektur microservices terbaik untuk e-commerce?</i>",
            parse_mode=ParseMode.HTML
        )
        return

    chat_id = update.effective_chat.id
    stop_event = asyncio.Event()
    typing_task = asyncio.create_task(continuous_typing(chat_id, context, stop_event))

    status_msg = await update.message.reply_text(" <b>Memulai Orchestration: Hermes Agent + Antigravity AI...</b>", parse_mode=ParseMode.HTML)

    try:
        # Step 1: Hermes Agent Orchestrator Response
        await status_msg.edit_text(" <b>[1/2] Hermes Agent (Orchestrator) sedang menganalisis topik...</b>", parse_mode=ParseMode.HTML)
        hermes_resp = await asyncio.to_thread(query_hermes_agent, topic)

        # Send Hermes Response to Telegram
        hermes_header = " <b>Hermes Agent (AI Orchestrator)</b>\n\n"
        chunks = split_message(hermes_header + hermes_resp)
        for chunk in chunks:
            try:
                await update.message.reply_text(chunk, parse_mode=ParseMode.HTML)
            except Exception:
                await update.message.reply_text(chunk)

        # Step 2: Antigravity AI Review & Execution
        await status_msg.edit_text(" <b>[2/2] Antigravity AI sedang melakukan tinjauan teknis & eksekusi...</b>", parse_mode=ParseMode.HTML)
        
        antigravity_prompt = f"[Orchestrated Task from User]\nTopic: {topic}\n\n[Hermes Agent Initial Plan]:\n{hermes_resp}\n\nBerikan tanggapan teknis mendalam, validasi kode, dan rekomendasi eksekusi dari sudut pandang Antigravity AI."
        
        sessions = load_sessions()
        convo_id = get_convo_id(sessions, user_id, target_mode="diskusi")
        agentapi_path = cfg.get("agentapi_path")
        model = cfg.get("default_model", "flash")

        if not convo_id:
            code, stdout, stderr = await asyncio.to_thread(
                run_agentapi, ["new-conversation", f"--model={model}", "--", antigravity_prompt], agentapi_path
            )
            if code == 0 and stdout:
                try:
                    data = json.loads(stdout)
                    convo_id = data.get("response", {}).get("newConversation", {}).get("conversationId")
                    if convo_id:
                        sessions = load_sessions()
                        set_convo_id(sessions, user_id, convo_id, target_mode="diskusi")
                except Exception:
                    pass
        else:
            code, stdout, stderr = await asyncio.to_thread(
                run_agentapi, ["send-message", convo_id, antigravity_prompt], agentapi_path
            )

        if convo_id:
            max_attempts = cfg.get("max_poll_attempts", 90)
            poll_interval = cfg.get("poll_interval_seconds", 2)
            last_response = ""

            for _ in range(max_attempts):
                await asyncio.sleep(poll_interval)
                resp = get_latest_response_from_transcript(convo_id)
                if resp and resp != last_response:
                    last_response = resp
                    break

            if last_response:
                anti_header = " <b>Antigravity AI (Technical Execution)</b>\n\n"
                chunks = split_message(anti_header + last_response)
                for chunk in chunks:
                    try:
                        await update.message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)
                    except Exception:
                        await update.message.reply_text(chunk)

                await status_msg.edit_text(" <b>Orchestration Selesai! Hermes Agent & Antigravity AI telah berkolaborasi.</b>", parse_mode=ParseMode.HTML)
                return

        await status_msg.edit_text(" Orchestration selesai di Antigravity PC Anda.", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error during orchestration: {e}")
        await status_msg.edit_text(f" Terjadi kesalahan: {e}", parse_mode=ParseMode.HTML)
    finally:
        stop_event.set()
        await typing_task



async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """CommandHandler untuk /reset dan /clear - Membersihkan sesi Telegram & membuat konteks baru yang bersih."""
    cfg = context.bot_data["config"]
    user = update.effective_user
    user_id = str(user.id)

    if not is_user_allowed(user.id, cfg.get("allowed_users", [])):
        return

    sessions = load_sessions()
    set_convo_id(sessions, user_id, None, target_mode="direct")

    await update.message.reply_text(
        "💬 <b>Sesi Direct Chat Berhasil Di-Reset!</b>\n\nKonteks percakapan pribadi Anda telah dibersihkan. Kirim pesan baru kapan saja!",
        parse_mode=ParseMode.HTML
    )


def main():
    # ── SINGLE-INSTANCE LOCK (anti Telegram getUpdates Conflict) ──
    # Pakai file lock atomik (msvcrt) — dua proses yg start bersamaan: yg pertama
    # dapat lock, yg kedua menolak & keluar. Ini yang mencegah "Conflict: terminated
    # by other getUpdates request" (bot api menolak >1 polling instance).
    lock_held = False
    try:
        import msvcrt
        lockfile = str(BASE_DIR / "bot.lock")
        global _LOCKFILE_HANDLE
        _LOCKFILE_HANDLE = open(lockfile, "a+")
        msvcrt.locking(_LOCKFILE_HANDLE.fileno(), msvcrt.LK_NBLCK, 1)
        lock_held = True
        _LOCKFILE_HANDLE.seek(0)
        _LOCKFILE_HANDLE.truncate()
        _LOCKFILE_HANDLE.write(str(os.getpid()))
        _LOCKFILE_HANDLE.flush()
        logger.info(f"🔒 Lock diperoleh (PID {os.getpid()}) — instance ini aktif.")
    except (OSError, IOError):
        logger.warning("⚠️ Bot lain sedang berjalan (lock terkunci). Keluar.")
        sys.exit(0)
    except Exception as e:
        logger.warning(f"lock skip (non-fatal): {e}")

    cfg = load_config()
    token = cfg.get("bot_token")

    logger.info("⚡ [START] Launching Hermes-Style Antigravity Telegram Bot...")
    logger.info(f"   • Model default: {cfg.get('default_model')}")
    logger.info(f"   • Allowed Users: {cfg.get('allowed_users')}")
    logger.info(f"   • agentapi path: {cfg.get('agentapi_path')}")
    logger.info(f"   • LS: {_find_ls_port() or '?'} | CSRF: {'set' if _find_ls_csrf() else '?'}")

    from telegram.request import HTTPXRequest
    req = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30,
        httpx_kwargs={"verify": False},
    )
    app = Application.builder().token(token).request(req).build()
    app.bot_data["config"] = cfg

    # Register Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("mode", mode_command))
    app.add_handler(CommandHandler("switch", mode_command))
    app.add_handler(CommandHandler("sessions", sessions_command))
    app.add_handler(CommandHandler("list_sessions", sessions_command))
    app.add_handler(CommandHandler("switch_session", switch_session_command))
    app.add_handler(CommandHandler("model", model_command))
    app.add_handler(CommandHandler("new", new_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("clear", reset_command))
    app.add_handler(CommandHandler("new_diskusi", reset_diskusi_command))
    app.add_handler(CommandHandler("reset_diskusi", reset_diskusi_command))
    app.add_handler(CommandHandler("diskusi", diskusi_command))
    app.add_handler(CommandHandler("orchestrate", diskusi_command))

    # Register Callback Query Handler
    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(session_callback_handler, pattern="^switch_sess:"))

    # Register Message Handler (Text & Attachments)
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.ALL, handle_message))

    logger.info("🟢 [READY] Bot is active and listening for Telegram updates...")
    
    # ── NETWORK RESILIENCY: anti-internet-loss crash ──
    # Kalau internet putus (httpx.ReadError/NetworkError), app.run_polling akan
    # raise exception. Kita tangkap & retry otomatis tiap 10 detik — bot tidak
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
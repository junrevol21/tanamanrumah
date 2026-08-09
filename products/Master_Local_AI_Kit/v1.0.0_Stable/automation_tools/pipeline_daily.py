"""
Pipeline harian YouTube timelapse (100% otomatis):
  1. Ambil topik berikutnya dari antrian (kalau proyek sebelumnya selesai)
  2. Omni bikin script timelapse (18-24 segmen, EN)
  3. Generate klip vertikal 8-10/hari (multi-akun, rotasi, auto-switch kuota)
  4. Kalau klip sudah cukup (>= target) → rakit (musik + label, tanpa TTS) → upload YouTube
  5. Status disimpan di state_pipeline.json — jalan tiap hari via cron

Cara pakai: python pipeline_daily.py
"""
import json, os, subprocess, sys, time, glob, re

BASE = r"C:\Users\ASUS\projects\tanamanrumah\youtube"
TOOLS = os.path.join(BASE, "tools")
SCRIPTS = os.path.join(BASE, "scripts")
CLIPS_ROOT = os.path.join(BASE, "veo_clips", "vertikal")
STATE_FILE = os.path.join(SCRIPTS, "state_pipeline.json")
LOG_FILE = os.path.join(BASE, "pipeline_status.txt")

# antrian topik timelapse (global, EN) — bisa diedit/ditambah
DEFAULT_QUEUE = [
    "The complete life cycle of a butterfly, from egg to caterpillar to chrysalis to butterfly",
    "A tiny seed growing into a full bean plant, timelapse over 60 days",
    "Mushroom growth from tiny pins to full fruiting bodies, timelapse",
    "A flower bud slowly blooming into a full blossom, timelapse",
    "The life cycle of a frog, from eggs to tadpole to froglet to adult frog",
    "Crystals growing from a saturated solution, timelapse",
    "A fallen leaf decomposing into soil, macro timelapse",
    "Mold and fungi taking over a forgotten orange, macro timelapse",
    "Bread rising and baking in the oven, timelapse",
    "Plants turning to face the sun through the day, timelapse",
]

TARGET_CLIPS = 24  # 24 x 8s ≈ 3.2 menit (3-5 mnt = naikkan 30+); 9 klip/hari → ~3 hari/proyek
MAX_CLIPS_PER_DAY = 9

def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M')}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"queue": DEFAULT_QUEUE, "project": None, "history": []}

def save_state(st):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)

def slugify(topic):
    s = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    return s[:60]

def count_clips(d):
    try:
        return len([f for f in os.listdir(d) if f.startswith("clip") and f[4:-4].isdigit()])
    except OSError:
        return 0

def run(cmd, timeout=1800):
    log("RUN: " + " ".join(cmd)[:150])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    out = (r.stdout or "")[-400:]
    log(f"EXIT {r.returncode}: {out.strip()[:250]}")
    return r.returncode == 0, r.stdout or ""

def main():
    st = load_state()
    proj = st.get("project")

    # 1) proyek baru kalau belum ada / sudah selesai
    if not proj or proj.get("done"):
        if not st["queue"]:
            log("ANTRIAN KOSONG — tambah topik di DEFAULT_QUEUE atau state_pipeline.json")
            return
        topic = st["queue"].pop(0)
        slug = slugify(topic)
        script = os.path.join(SCRIPTS, f"timelapse_{slug}.json")
        log(f"PROYEK BARU: {topic}")
        ok, _out = run(["python", os.path.join(TOOLS, "gemini_script.py"), "--timelapse", topic, script])
        if not ok or not os.path.exists(script):
            log("SCRIPT GAGAL — coba lagi run berikutnya")
            st["queue"].insert(0, topic)
            save_state(st)
            return
        try:
            with open(script, encoding="utf-8") as f:
                data = json.load(f)
            n_seg = len(data.get("segmen", []))
        except Exception:
            n_seg = TARGET_CLIPS
        proj = {"topic": topic, "slug": slug, "script": script, "out_dir": os.path.join(CLIPS_ROOT, slug),
                "target": max(n_seg, TARGET_CLIPS), "done": False}
        st["project"] = proj
        save_state(st)
        log(f"PROYEK: {n_seg} segmen, target {proj['target']} klip")

    # 2) generate klip hari ini (sisanya, maks 9/akun-max 2)
    have = count_clips(proj["out_dir"])
    need = proj["target"] - have
    if need <= 0:
        have = proj["target"]
    else:
        with open(proj["script"], encoding="utf-8") as f:
            data = json.load(f)
        segmen = data.get("segmen", [])
        batch = segmen[have:have + MAX_CLIPS_PER_DAY]
        log(f"GENERATE {len(batch)} klip (sudah {have}/{proj['target']})")
        if batch:
            tmp = os.path.join(SCRIPTS, f"batch_{proj['slug']}.json")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"judul": data.get("judul", ""), "segmen": batch}, f, ensure_ascii=False)
            run(["python", os.path.join(TOOLS, "gemini_multi.py"), tmp, proj["out_dir"], "2"])
        have = count_clips(proj["out_dir"])
        log(f"SETELAH GENERATE: {have}/{proj['target']} klip")

    # 3) rakit + upload kalau cukup
    if have >= proj["target"]:
        video = os.path.join(BASE, "video3", f"{proj['slug']}.mp4")
        log(f"RAKIT VIDEO dari {have} klip...")
        ok, _out = run(["python", os.path.join(TOOLS, "build_content_video.py"),
                 proj["script"], video, str(have), proj["out_dir"], "--timelapse"], timeout=1800)
        if ok and os.path.exists(video):
            with open(proj["script"], encoding="utf-8") as f:
                data = json.load(f)
            title = data.get("judul", proj["topic"])[:95]
            desc_file = os.path.join(SCRIPTS, f"desc_{proj['slug']}.txt")
            desc = data.get("deskripsi", "") + "\n\n#timelapse #plants #nature #shorts #garden #satisfying"
            with open(desc_file, "w", encoding="utf-8") as f:
                f.write(desc)
            log(f"UPLOAD: {title}")
            ok_up, up_out = run(["python", os.path.join(TOOLS, "upload_video.py"), video, title, desc_file], timeout=600)
            # ekstrak URL YouTube dari output upload_video.py
            yt_url = ""
            m = re.search(r"https://youtu\.be/([A-Za-z0-9_-]{6,})", up_out or "")
            if m:
                yt_url = m.group(0)
            if ok_up:
                entry = {"topic": proj["topic"], "video": video, "when": time.strftime("%Y-%m-%d %H:%M")}
                if yt_url:
                    entry["url"] = yt_url
                st["history"].append(entry)
                proj["done"] = True
                log(f"✅ PROYEK SELESAI & DIUPLOAD {yt_url}")
            else:
                log("UPLOAD GAGAL — video tersimpan, coba manual nanti")
            # --- Shorts reuse: bikin 2 Shorts + upload ---
            if ok_up:
                short_dir = os.path.join(BASE, "video3")
                for pola in (1, 2):
                    ok_s, _out = run(["python", os.path.join(TOOLS, "build_shorts.py"),
                                proj["script"], proj["out_dir"], short_dir, f"--pola={pola}"], timeout=600)
                    short_path = os.path.join(short_dir, f"short_{pola}.mp4")
                    if ok_s and os.path.exists(short_path):
                        s_title = title[:55] + " #shorts"
                        s_desc = os.path.join(SCRIPTS, f"desc_short_{pola}_{proj['slug']}.txt")
                        with open(s_desc, "w", encoding="utf-8") as f:
                            f.write(desc + "\n#shorts #timelapse #satisfying")
                        log(f"UPLOAD SHORT {pola}: {s_title}")
                        run(["python", os.path.join(TOOLS, "upload_video.py"), short_path, s_title, s_desc], timeout=600)
                    else:
                        log(f"SHORT {pola} gagal/gak cukup klip")
        else:
            log("RAKIT GAGAL")
        save_state(st)
    else:
        log(f"BELUM CUKUP ({have}/{proj['target']}) — lanjut besok")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        log(f"PIPELINE ERROR: {e}")

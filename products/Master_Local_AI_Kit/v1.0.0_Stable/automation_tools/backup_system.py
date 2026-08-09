# -*- coding: utf-8 -*-
"""
backup_system.py — Backup otomatis seluruh sistem Hermes + proyek + Antigravity.
Cara pakai: python backup_system.py [--push]
  - Tanpa --push: buat zip lokal + salin ke OneDrive
  - Dengan --push: tambah push ke GitHub private repo (jika ada)
Lokasi: C:\\Users\\ASUS\\backups\\hermes_system\\ + OneDrive\\HermesBackup\\
"""
import os, sys, shutil, datetime, glob, zipfile

BACKUP_DEST = r"C:\Users\ASUS\backups\hermes_system"
ONEDRIVE_DEST = os.path.join(os.path.expanduser("~"), "OneDrive", "HermesBackup")
GIT_REPO = r"C:\Users\ASUS\backups\hermes_system\repo"

# Sumber data yang wajib dibackup
SOURCES = {
    "hermes": [
        r"C:\Users\ASUS\AppData\Local\hermes\memories",
        r"C:\Users\ASUS\AppData\Local\hermes\skills",
        r"C:\Users\ASUS\AppData\Local\hermes\cron",
        r"C:\Users\ASUS\AppData\Local\hermes\secrets",
        r"C:\Users\ASUS\AppData\Local\hermes\config.yaml",
    ],
    "proyek_tanamanrumah": [
        r"C:\Users\ASUS\projects\tanamanrumah",
    ],
    "antigravity_bridge": [
        r"C:\Users\ASUS\.gemini\antigravity\telegram_bot",
        r"C:\Users\ASUS\.gemini\antigravity\brain",
        r"C:\Users\ASUS\.gemini\antigravity\scratch",
        r"C:\Users\ASUS\AppData\Local\hermes\scripts\antigravity_subagent.py",
    ],
}

def make_backup():
    os.makedirs(BACKUP_DEST, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    zip_path = os.path.join(BACKUP_DEST, f"hermes_backup_{ts}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for label, paths in SOURCES.items():
            for src in paths:
                if os.path.exists(src):
                    base = os.path.dirname(src)
                    for root, dirs, files in os.walk(src):
                        dirs[:] = [d for d in dirs if d not in ("node_modules", "__pycache__", ".next-cli-build", "cache", ".git")]
                        for f in files:
                            full = os.path.join(root, f)
                            arc = os.path.join(label, os.path.relpath(full, base))
                            try:
                                zf.write(full, arc)
                            except Exception:
                                pass
    # simpan 7 backup terakhir di lokal
    for old in sorted(glob.glob(os.path.join(BACKUP_DEST, "hermes_backup_*.zip")))[:-7]:
        try: os.remove(old)
        except Exception: pass
    size_mb = os.path.getsize(zip_path) / 1024 / 1024
    print(f"BACKUP LOKAL: {os.path.basename(zip_path)} ({size_mb:.1f} MB)")
    return zip_path

def copy_to_onedrive(zip_path):
    """Salin ZIP ke OneDrive (sinkron otomatis ke cloud)."""
    if not os.path.isdir(ONEDRIVE_DEST):
        try:
            os.makedirs(ONEDRIVE_DEST, exist_ok=True)
        except Exception as e:
            print(f"OneDrive folder tidak bisa dibuat: {e}")
            return False
    try:
        dest = os.path.join(ONEDRIVE_DEST, os.path.basename(zip_path))
        shutil.copy2(zip_path, dest)
        # hapus backup OneDrive lama (simpan 14)
        for old in sorted(glob.glob(os.path.join(ONEDRIVE_DEST, "hermes_backup_*.zip")))[:-14]:
            try: os.remove(old)
            except Exception: pass
        print(f"BACKUP CLOUD (OneDrive): OK -> {dest}")
        return True
    except Exception as e:
        print(f"BACKUP CLOUD GAGAL: {e}")
        return False

def push_to_github(zip_path):
    if not os.path.isdir(os.path.join(GIT_REPO, ".git")):
        print("SKIP PUSH: repo git belum diinisialisasi di", GIT_REPO)
        return False
    shutil.copy2(zip_path, GIT_REPO)
    import subprocess
    subprocess.run(["git", "-C", GIT_REPO, "add", "."], check=False, capture_output=True)
    subprocess.run(["git", "-C", GIT_REPO, "commit", "-m", f"backup {datetime.datetime.now():%Y-%m-%d %H:%M}"], check=False, capture_output=True)
    r = subprocess.run(["git", "-C", GIT_REPO, "push"], check=False, capture_output=True, text=True)
    print("PUSH GITHUB:", "OK" if r.returncode == 0 else r.stderr[-200:])
    return r.returncode == 0

if __name__ == "__main__":
    z = make_backup()
    copy_to_onedrive(z)
    if "--push" in sys.argv:
        push_to_github(z)

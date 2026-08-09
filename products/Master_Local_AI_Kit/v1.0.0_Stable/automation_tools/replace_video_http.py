"""Ganti file video YouTube via protokol resumable upload (HTTP langsung, tanpa library)."""
import json
import os
import sys
import urllib.request

DIR = os.path.dirname(os.path.abspath(__file__))
tok = json.load(open(os.path.join(DIR, "token.json")))
token = tok["token"]

VIDEO_ID = sys.argv[1] if len(sys.argv) > 1 else "PmguEE0K8eY"
FILE = sys.argv[2] if len(sys.argv) > 2 else r"C:\Users\ASUS\projects\tanamanrumah\youtube\video1\tanamanrumah-lampu-tanam-v2.mp4"
DESC_FILE = sys.argv[3] if len(sys.argv) > 3 else r"C:\Users\ASUS\projects\tanamanrumah\youtube\video1\deskripsi.txt"
desc = open(DESC_FILE, encoding="utf-8").read() if os.path.exists(DESC_FILE) else ""
size = os.path.getsize(FILE)

meta = {
    "id": VIDEO_ID,
    "snippet": {
        "title": "Lampu Tanam untuk Pemula - 5 Hal Wajib Tahu (2026)",
        "description": desc,
        "categoryId": "27",
    },
    "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
}

# 1. Initiate resumable session
req = urllib.request.Request(
    "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
    method="POST",
)
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Content-Type", "application/json; charset=UTF-8")
req.add_header("X-Upload-Content-Type", "video/mp4")
req.add_header("X-Upload-Content-Length", str(size))
with urllib.request.urlopen(req, data=json.dumps(meta).encode(), timeout=60) as r:
    loc = r.headers["Location"]
print("Sesi upload dibuat")

# 2. Upload file (single PUT dengan Content-Range)
with open(FILE, "rb") as f:
    data = f.read()
req2 = urllib.request.Request(loc, method="PUT", data=data)
req2.add_header("Content-Type", "video/mp4")
req2.add_header("Content-Length", str(size))
req2.add_header("Content-Range", f"bytes 0-{size - 1}/{size}")
with urllib.request.urlopen(req2, timeout=900) as r:
    resp = json.loads(r.read())
print("SELESAI! Video ID:", resp["id"])
print("URL: https://youtu.be/" + resp["id"])
print("Status:", resp["status"]["uploadStatus"])

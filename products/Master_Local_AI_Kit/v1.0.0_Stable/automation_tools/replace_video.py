"""Ganti file video YouTube (videos.update) — URL & ID tetap, file baru."""
import os
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

DIR = os.path.dirname(os.path.abspath(__file__))
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
creds = Credentials.from_authorized_user_file(os.path.join(DIR, "token.json"), SCOPES)
yt = build("youtube", "v3", credentials=creds)

VIDEO_ID = sys.argv[1] if len(sys.argv) > 1 else "PmguEE0K8eY"
FILE = sys.argv[2] if len(sys.argv) > 2 else r"C:\Users\ASUS\projects\tanamanrumah\youtube\video1\tanamanrumah-lampu-tanam-v2.mp4"
DESC_FILE = sys.argv[3] if len(sys.argv) > 3 else r"C:\Users\ASUS\projects\tanamanrumah\youtube\video1\deskripsi.txt"

desc = open(DESC_FILE, encoding="utf-8").read() if os.path.exists(DESC_FILE) else ""

body = {
    "id": VIDEO_ID,
    "snippet": {
        "title": "Lampu Tanam untuk Pemula - 5 Hal Wajib Tahu (2026)",
        "description": desc,
        "categoryId": "27",
    },
    "status": {
        "privacyStatus": "public",
        "selfDeclaredMadeForKids": False,
    },
}
media = MediaFileUpload(FILE, chunksize=1024 * 1024, resumable=True, mimetype="video/mp4")
req = yt.videos().update(part="snippet,status", body=body, media_body=media)
resp = None
while resp is None:
    status, resp = req.next_chunk()
    if status:
        print(f"Ganti file {int(status.progress() * 100)}%")
print("SELESAI! Video diupdate:", resp["id"], "-> https://youtu.be/" + resp["id"])

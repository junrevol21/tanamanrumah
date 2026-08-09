"""Upload video ke YouTube via Data API v3 (OAuth sekali, token tersimpan lokal).

Setup (sekali): taruh client_secret.json dari Google Cloud di folder ini,
lalu jalankan. Browser akan terbuka untuk login & approve — setelah itu
upload berikutnya TANPA login lagi.
"""
import json
import os
import sys

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly"]
DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_FILE = os.path.join(DIR, "client_secret.json")
TOKEN_FILE = os.path.join(DIR, "token.json")


def get_creds():
    if os.path.exists(TOKEN_FILE):
        return Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())
    return creds


def main():
    if len(sys.argv) < 3:
        print("Pakai: python upload_video.py <video.mp4> <judul> [file_deskripsi.txt]")
        sys.exit(1)
    video_path = sys.argv[1]
    title = sys.argv[2]
    desc = ""
    if len(sys.argv) > 3 and os.path.exists(sys.argv[3]):
        with open(sys.argv[3], encoding="utf-8") as f:
            desc = f.read()
    tags = ["lampu tanam", "grow light", "tanaman indoor", "urban farming",
            "berkebun", "tanaman hias", "hidroponik"]

    creds = get_creds()
    yt = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {
            "title": title,
            "description": desc,
            "tags": tags,
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids": False,
        },
    }
    media = MediaFileUpload(video_path, chunksize=1024 * 1024, resumable=True,
                            mimetype="video/mp4")
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"Upload {int(status.progress() * 100)}%")
    print(f"SELESAI! Video ID: {resp['id']}")
    print(f"URL: https://youtu.be/{resp['id']}")


if __name__ == "__main__":
    main()

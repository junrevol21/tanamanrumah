"""Update judul/deskripsi video YouTube via API (butuh scope youtube — hasil reauth)."""
import json
import os
import sys
import urllib.request

DIR = os.path.dirname(os.path.abspath(__file__))
tok = json.load(open(os.path.join(DIR, "token.json")))
token = tok["token"]

video_id = sys.argv[1]
title = sys.argv[2]
desc_file = sys.argv[3] if len(sys.argv) > 3 else None
desc = open(desc_file, encoding="utf-8").read() if desc_file and os.path.exists(desc_file) else ""

# Ambil snippet/status lama agar tidak kehilangan data
req = urllib.request.Request(f"https://www.googleapis.com/youtube/v3/videos?part=snippet,status&id={video_id}")
req.add_header("Authorization", f"Bearer {token}")
d = json.load(urllib.request.urlopen(req, timeout=30))
v = d["items"][0]
old = v["snippet"]

body = {
    "id": video_id,
    "snippet": {
        "title": title,
        "description": desc if desc else old.get("description", ""),
        "categoryId": old.get("categoryId", "27"),
    },
    "status": {"privacyStatus": v["status"].get("privacyStatus", "public"),
               "selfDeclaredMadeForKids": False},
}

req2 = urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?part=snippet,status", method="PUT")
req2.add_header("Authorization", f"Bearer {token}")
req2.add_header("Content-Type", "application/json")
try:
    with urllib.request.urlopen(req2, data=json.dumps(body).encode(), timeout=60) as r:
        out = json.loads(r.read())
        print("OK:", out["id"], "| judul baru:", out["snippet"]["title"][:50])
except urllib.error.HTTPError as e:
    print("ERROR", e.code, e.read().decode()[:300])

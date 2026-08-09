"""
Buat produk digital di Gumroad via API (presign flow terbaru 2025+).
Cara pakai:
  python gumroad_product.py <spec.json> [cover.png]
spec.json: {"name","description","price_cents","currency","file":"path.pdf"}
Token: C:\\Users\\ASUS\\AppData\\Local\\hermes\\secrets\\gumroad_token.txt
"""
import json, sys, os, urllib.request, urllib.parse, uuid

SECRETS = r"C:\Users\ASUS\AppData\Local\hermes\secrets"
TOKEN_FILE = os.path.join(SECRETS, "gumroad_token.txt")
API = "https://api.gumroad.com/v2"

def api_token():
    try:
        with open(TOKEN_FILE) as f: return f.read().strip()
    except Exception: return None

def http_json(url, data=None, headers=None, method=None, timeout=120):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def upload_file(file_path):
    """Presign → upload S3 → complete → return URL."""
    token = api_token()
    # 1. presign
    resp = http_json(f"{API}/files/presign?access_token={token}", method="POST")
    if not resp.get("success"):
        raise RuntimeError(f"presign gagal: {resp}")
    parts = resp["upload_parts"]          # [{key, url, ...}]
    guid = resp["guid"]
    urls = []
    for i, part in enumerate(parts):
        with open(file_path, "rb") as f:
            content = f.read()
        # upload ke S3 (PUT)
        s3req = urllib.request.Request(part["url"], data=content, method="PUT",
                                       headers={"Content-Type": "application/octet-stream"})
        with urllib.request.urlopen(s3req, timeout=180) as r:
            if r.status not in (200, 201):
                raise RuntimeError(f"S3 upload part {i} gagal: {r.status}")
        urls.append(part["key"])
    # 2. complete
    complete = http_json(
        f"{API}/files/complete?access_token={token}&guid={guid}",
        data=json.dumps({"file_urls": urls}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    if not complete.get("success"):
        raise RuntimeError(f"complete gagal: {complete}")
    return complete.get("file_url") or complete.get("url")

def create_product(spec):
    token = api_token()
    if not token:
        print("TOKEN_TIDAK_ADA"); return
    # upload file dulu
    file_url = None
    if "file" in spec and os.path.exists(spec["file"]):
        print("Upload file...")
        file_url = upload_file(spec["file"])
        print(f"  file URL: {file_url[:80]}...")
    data = urllib.parse.urlencode({
        "access_token": token,
        "name": spec["name"],
        "description": spec.get("description", ""),
        "price": int(spec.get("price_cents", 400)),
        "price_currency_type": spec.get("currency", "usd"),
        "native_type": spec.get("native_type", "digital"),
    }).encode()
    if file_url:
        data += urllib.parse.urlencode({"files[][url]": file_url}).encode()
    req = urllib.request.Request(f"{API}/products", data=data)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            out = json.loads(resp.read().decode())
        if out.get("success"):
            p = out["product"]
            print(f"OK: {p.get('name')} | {p.get('short_url')} | id={p.get('id')}")
            # auto publish
            publish(out["product"]["id"], token)
        else:
            print(f"GAGAL: {out.get('message')}")
    except Exception as e:
        print(f"GAGAL: {e}")

def publish(product_id, token):
    data = urllib.parse.urlencode({"access_token": token, "published": "true"}).encode()
    req = urllib.request.Request(f"{API}/products/{product_id}", data=data, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            out = json.loads(resp.read().decode())
        print(f"PUBLISH: {'OK' if out.get('success') else out.get('message')}")
    except Exception as e:
        print(f"PUBLISH GAGAL: {e}")

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    create_product(spec)

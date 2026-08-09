"""
Upload file (ebook PDF) ke Gumroad via presigned S3 flow, lalu buat produk dgn file tsb.
4 langkah: presign -> PUT parts -> complete -> create product dgn files[][url]

Cara pakai:
  python gumroad_ebook.py <file.pdf> <nama> <deskripsi> <price_cents> [currency]
Token: C:\\Users\\ASUS\\AppData\\Local\\hermes\\secrets\\gumroad_token.txt
"""
import sys, os, json, urllib.request, urllib.parse, uuid

SECRETS = r"C:\Users\ASUS\AppData\Local\hermes\secrets"
TOKEN_FILE = os.path.join(SECRETS, "gumroad_token.txt")
API = "https://api.gumroad.com/v2"

def token():
    with open(TOKEN_FILE) as f:
        return f.read().strip()

def req_json(url, data=None, method=None, headers=None):
    h = {"Authorization": f"Bearer {token()}"}
    if headers:
        h.update(headers)
    if data is not None and not isinstance(data, bytes):
        data = urllib.parse.urlencode(data).encode()
    r = urllib.request.Request(url, data=data, method=method, headers=h)
    with urllib.request.urlopen(r, timeout=120) as resp:
        return json.loads(resp.read().decode())

def upload_file(path):
    size = os.path.getsize(path)
    fname = os.path.basename(path)
    # 1) presign
    d = req_json(f"{API}/files/presign", {"filename": fname, "file_size": size})
    if not d.get("success"):
        raise RuntimeError(f"presign gagal: {d}")
    upload_id, key = d["upload_id"], d["key"]
    # 2) PUT parts
    etags = []
    with open(path, "rb") as f:
        for part in d["parts"]:
            f.seek((part["part_number"] - 1) * 100 * 1024 * 1024)
            chunk = f.read(100 * 1024 * 1024)
            req = urllib.request.Request(part["presigned_url"], data=chunk, method="PUT")
            with urllib.request.urlopen(req, timeout=300) as resp:
                etag = resp.headers.get("ETag", "")
            etags.append({"part_number": part["part_number"], "etag": etag})
    # 3) complete
    body = {"upload_id": upload_id, "key": key}
    for e in etags:
        body[f"parts[][part_number]"] = e["part_number"]
        body[f"parts[][etag]"] = e["etag"]
    d2 = req_json(f"{API}/files/complete", body)
    if not d2.get("success"):
        raise RuntimeError(f"complete gagal: {d2}")
    return d2["file_url"]

def create_product(file_url, name, desc, price_cents, currency="usd"):
    body = {
        "native_type": "digital",
        "name": name,
        "description": desc,
        "price": int(price_cents),
        "price_currency_type": currency,
        "files[][url]": file_url,
        "files[][position]": 1,
    }
    d = req_json(f"{API}/products", body)
    if not d.get("success"):
        raise RuntimeError(f"create gagal: {d}")
    return d["product"]

if __name__ == "__main__":
    path, name, desc, price = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    curr = sys.argv[5] if len(sys.argv) > 5 else "usd"
    print("Upload file ke S3...")
    url = upload_file(path)
    print("File URL:", url[:80])
    print("Buat produk...")
    p = create_product(url, name, desc, price, curr)
    print(f"OK: {p.get('name')} | {p.get('short_url')}")

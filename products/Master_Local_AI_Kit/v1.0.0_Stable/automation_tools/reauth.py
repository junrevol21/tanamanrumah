"""Re-auth OAuth dengan scope PENUH (youtube) agar bisa update & delete video via API."""
import os
from google_auth_oauthlib.flow import InstalledAppFlow

DIR = os.path.dirname(os.path.abspath(__file__))
SCOPES = ["https://www.googleapis.com/auth/youtube"]
flow = InstalledAppFlow.from_client_secrets_file(os.path.join(DIR, "client_secret.json"), SCOPES)
creds = flow.run_local_server(port=0)
with open(os.path.join(DIR, "token.json"), "w") as f:
    f.write(creds.to_json())
print("TOKEN BARU DISIMPAN dengan scope: youtube (full)")

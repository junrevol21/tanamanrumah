import os
import sys
import time
import json
import asyncio
import subprocess

# Rencana: Sequential Runner yang tahan banting (resilient)
# Memanggil gemini_multi.py satu per satu secara berurutan, bukan parallel.

PROMPTS_PATH = r"C:\Users\ASUS\projects\tanamanrumah\youtube\scripts\batch_the-complete-life-cycle-of-a-butterfly-from-egg-to-caterpill.json"
OUT_DIR = r"C:\Users\ASUS\projects\tanamanrumah\youtube\veo_clips\vertikal\the-complete-life-cycle-of-a-butterfly-from-egg-to-caterpill"
PYTHON_PATH = r"C:\Python314\python.exe"
SCRIPT_PATH = r"C:\Users\ASUS\projects\tanamanrumah\youtube\tools\gemini_multi.py"

async def run_resilient():
    with open(PROMPTS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    
    prompts = data["segmen"]
    print(f"Total segmen: {len(prompts)}")
    
    # Jalankan satu per satu (Sequential)
    for i, segmen in enumerate(prompts):
        print(f"=== Menjalankan segmen {i+1}/{len(prompts)}: {segmen['label']} ===")
        
        # Simpan sementara segmen ini ke file kecil agar gemini_multi.py hanya proses satu
        temp_batch = {"segmen": [segmen]}
        temp_path = os.path.join(os.path.dirname(PROMPTS_PATH), "temp_segmen.json")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(temp_batch, f)
            
        success = False
        for attempt in range(3): # Maksimal 3 kali retry per segmen
            try:
                # Panggil gemini_multi.py dengan max_per_account 1 (Sequential)
                cmd = [PYTHON_PATH, SCRIPT_PATH, temp_path, OUT_DIR, "1"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ Segmen {i+1} sukses.")
                    success = True
                    break
                else:
                    print(f"⚠️ Segmen {i+1} gagal (Attempt {attempt+1}): {result.stderr[:100]}")
            except Exception as e:
                print(f"❌ Segmen {i+1} error (Attempt {attempt+1}): {e}")
            time.sleep(10) # Jeda antar retry
            
        if not success:
            print(f"❌ Segmen {i+1} gagal setelah 3 percobaan, lanjut ke segmen berikutnya.")
            
    print("=== Pipeline Selesai ===")

if __name__ == "__main__":
    asyncio.run(run_resilient())

"""
Potong video timelapse panjang menjadi Shorts 45-60 detik (reuse klip, tanpa quota tambahan).
Pola: hook (awal) + tengah + payoff (akhir) — struktur Shorts yang retensi-nya bagus.

Cara pakai:
  python build_shorts.py <script.json> <clips_dir> <out_dir> [--pola 1|2]
  pola 1: 6 segmen awal (hook + progres)
  pola 2: hook + tengah + akhir (payoff)  [default]
Output: <out_dir>/short_1.mp4, short_2.mp4
"""
import json, subprocess, sys, os, glob, tempfile

TIMELAPSE = "--timelapse" in sys.argv
MUSIC = r"C:\Users\ASUS\projects\tanamanrumah\youtube\music\bg.mp3"
FFDIR = r"C:\Users\ASUS\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin"
FFMPEG = os.path.join(FFDIR, "ffmpeg.exe")
FFPROBE = os.path.join(FFDIR, "ffprobe.exe")

def run(cmd, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if r.returncode != 0:
        raise RuntimeError(f"CMD FAIL: {' '.join(cmd)[:180]}\n{r.stderr[-300:]}")
    return r

def duration(path):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", path], capture_output=True, text=True)
    return float(r.stdout.strip())

def wrap_text(text, max_chars=28):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= max_chars:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return "\n".join(lines)

def main():
    script_path, clips_dir, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    pola = 2
    if "--pola=1" in sys.argv:
        pola = 1
    with open(script_path, encoding="utf-8") as f:
        data = json.load(f)
    segmen = data.get("segmen", [])
    clips = sorted(glob.glob(os.path.join(clips_dir, "clip*.mp4")))[:len(segmen)]
    if len(clips) < 6:
        print(f"KLIP KURANG ({len(clips)}) — butuh minimal 6")
        return
    os.makedirs(out_dir, exist_ok=True)

    # pilih indeks segmen per pola
    n = len(clips)
    if pola == 1:
        idxs = list(range(min(6, n)))
    else:
        idxs = [0, 1, max(2, n // 2 - 1), n // 2, n - 2, n - 1]
    idxs = sorted(set(i for i in idxs if 0 <= i < n))
    print(f"Pola {pola}: segmen {idxs} ({len(idxs)} klip, ~{len(idxs)*10}s)")

    tmp = tempfile.mkdtemp(prefix="shorts_")
    import shutil
    shutil.copy(r"C:\Windows\Fonts\arialbd.ttf", os.path.join(tmp, "arialbd.ttf"))
    seg_files = []
    for i, (si, clip) in enumerate(zip(idxs, [clips[j] for j in idxs])):
        seg = segmen[si] if si < len(segmen) else {}
        text = seg.get("label") or seg.get("overlay") or f"Day {si+1}"
        ovl = os.path.join(tmp, f"ovl_{i}.txt")
        with open(ovl, "w", encoding="utf-8") as f:
            f.write(wrap_text(text))
        d_clip = duration(clip)
        out_seg = os.path.join(tmp, f"seg_{i}.mp4")
        fc = (f"[0:v]drawtext=textfile=ovl_{i}.txt:fontfile=arialbd.ttf:fontsize=46:"
              f"fontcolor=white:borderw=3:bordercolor=black@0.85:"
              f"x=(w-text_w)/2:y=h-text_h-220[vt]")
        run([FFMPEG, "-y", "-i", clip, "-filter_complex", fc, "-map", "[vt]",
             "-t", str(d_clip), "-c:v", "libx264", "-preset", "fast", "-crf", "22",
             "-pix_fmt", "yuv420p", out_seg], cwd=tmp)
        seg_files.append(out_seg)

    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        for s in seg_files:
            f.write(f"file '{s.replace(chr(92), '/')}'\n")
    concat_out = os.path.join(tmp, "concat.mp4")
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", concat_out])
    out_path = os.path.join(out_dir, f"short_{pola}.mp4")
    if os.path.exists(MUSIC):
        run([FFMPEG, "-y", "-i", concat_out, "-stream_loop", "-1", "-i", MUSIC,
             "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
             "-shortest", out_path])
    else:
        os.replace(concat_out, out_path)
    print(f"SHORT JADI: {out_path} ({duration(out_path):.1f}s)")

if __name__ == "__main__":
    main()

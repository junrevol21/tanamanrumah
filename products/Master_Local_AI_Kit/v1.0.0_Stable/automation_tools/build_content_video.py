"""
Rakit video konten dari JSON script + klip Veo:
  segmen[i].narasi -> edge-tts (id-ID-GadisNeural)
  segmen[i].overlay -> drawtext di atas klip
  concat semua segmen -> video final

Mode timelapse (--timelapse): tanpa narasi, teks = segmen.label, + musik latar opsional.

Cara pakai:
  python build_content_video.py <script.json> <output.mp4> [jumlah_segmen] [dir_klip] [--timelapse]
Klip diambil dari veo_clips/clip1.mp4, clip2.mp4, dst (urut).
"""
import json, subprocess, sys, os, glob, tempfile

TIMELAPSE = "--timelapse" in sys.argv
MUSIC = r"C:\Users\ASUS\projects\tanamanrumah\youtube\music\bg.mp3"

FFDIR = r"C:\Users\ASUS\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin"
FFMPEG = os.path.join(FFDIR, "ffmpeg.exe")
FFPROBE = os.path.join(FFDIR, "ffprobe.exe")
VOICE = "id-ID-GadisNeural"
FONT = r"C:/Windows/Fonts/arialbd.ttf"
CLIPS_DIR = r"C:\Users\ASUS\projects\tanamanrumah\youtube\veo_clips"
TMP = tempfile.mkdtemp(prefix="rakit_")

def run(cmd, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if r.returncode != 0:
        raise RuntimeError(f"CMD FAIL: {' '.join(cmd)[:200]}\n{r.stderr[-500:]}")
    return r

def duration(path):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", path],
                       capture_output=True, text=True)
    return float(r.stdout.strip())

def wrap_text(text, max_chars=28):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= max_chars:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return "\n".join(lines)

def main():
    script_path, out_path = sys.argv[1], sys.argv[2]
    n_max = int(sys.argv[3]) if len(sys.argv) > 3 else 99
    clips_dir = sys.argv[4] if len(sys.argv) > 4 else CLIPS_DIR
    with open(script_path, encoding="utf-8") as f:
        script = json.load(f)
    segmen = script["segmen"][:n_max]
    clips = sorted(glob.glob(os.path.join(clips_dir, "clip*.mp4")))[:len(segmen)]
    if not clips:
        print("TIDAK ADA KLIP di", clips_dir); return
    print(f"Segmen: {len(segmen)}, klip: {len(clips)} (dari {clips_dir})")

    seg_files = []
    # font & cwd relatif (hindari masalah colon di path filter ffmpeg)
    import shutil
    shutil.copy(r"C:\Windows\Fonts\arialbd.ttf", os.path.join(TMP, "arialbd.ttf"))
    for i, (seg, clip) in enumerate(zip(segmen, clips)):
        # 1) teks (overlay ID / label EN tergantung mode)
        text = seg.get("overlay") or seg.get("label") or ""
        ovl = os.path.join(TMP, f"overlay_{i}.txt")
        with open(ovl, "w", encoding="utf-8") as f:
            f.write(wrap_text(text))
        # 2) render segmen (path relatif + cwd=TMP)
        d_clip = duration(clip)
        out_seg = os.path.join(TMP, f"seg_{i}.mp4")
        if TIMELAPSE:
            # tanpa narasi: video + drawtext saja
            fc = (
                f"[0:v]drawtext=textfile=overlay_{i}.txt:fontfile=arialbd.ttf:fontsize=46:"
                f"fontcolor=white:borderw=3:bordercolor=black@0.85:"
                f"x=(w-text_w)/2:y=h-text_h-220[vt]"
            )
            run([FFMPEG, "-y", "-i", clip, "-filter_complex", fc,
                 "-map", "[vt]", "-t", str(d_clip),
                 "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                 "-pix_fmt", "yuv420p", out_seg], cwd=TMP)
        else:
            narasi = os.path.join(TMP, f"narasi_{i}.mp3")
            run(["python", "-m", "edge_tts", "--voice", VOICE,
                 "--text", seg["narasi"], "--write-media", narasi])
            fc = (
                f"[0:v]drawtext=textfile=overlay_{i}.txt:fontfile=arialbd.ttf:fontsize=46:"
                f"fontcolor=white:borderw=3:bordercolor=black@0.85:"
                f"x=(w-text_w)/2:y=h-text_h-220[vt];"
                f"[1:a]adelay=400:all=1[a]"
            )
            run([FFMPEG, "-y", "-i", clip, "-i", narasi,
                 "-filter_complex", fc,
                 "-map", "[vt]", "-map", "[a]",
                 "-t", str(d_clip),
                 "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                 "-c:a", "aac", "-b:a", "128k",
                 "-pix_fmt", "yuv420p", out_seg], cwd=TMP)
        seg_files.append(out_seg)
        print(f"  segmen {i+1}: ok ({d_clip:.1f}s) text='{text[:40]}'")

    # concat
    lst = os.path.join(TMP, "list.txt")
    with open(lst, "w") as f:
        for s in seg_files:
            f.write(f"file '{s.replace(chr(92), '/')}'\n")
    concat_out = os.path.join(TMP, "concat.mp4")
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-c", "copy", concat_out])
    if TIMELAPSE and os.path.exists(MUSIC):
        run([FFMPEG, "-y", "-i", concat_out, "-stream_loop", "-1", "-i", MUSIC,
             "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
             "-shortest", out_path])
        print(f"FINAL (dengan musik): {out_path} ({duration(out_path):.1f}s)")
    else:
        os.replace(concat_out, out_path)
        note = "" if not TIMELAPSE else " (tanpa musik — taruh bg.mp3 di youtube/music/ utk musik)"
        print(f"FINAL: {out_path} ({duration(out_path):.1f}s){note}")

if __name__ == "__main__":
    main()

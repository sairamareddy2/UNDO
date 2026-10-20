import os
import sys
import subprocess
import glob

FFMPEG_EXE = r"C:\Users\ADMIN\Downloads\undo\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
RAW_VIDEO_DIR = "artifacts/raw_video"
AUDIO_TRACK = "artifacts/master_narration.wav"
OUTPUT_MP4 = "artifacts/UNDO_Hackathon_Demo.mp4"

def render_final_video():
    print("[RENDER] Searching for raw recorded video in:", RAW_VIDEO_DIR)
    webms = glob.glob(os.path.join(RAW_VIDEO_DIR, "*.webm"))
    if not webms:
        print("[RENDER] ERROR: No .webm video files found in", RAW_VIDEO_DIR)
        sys.exit(1)

    raw_video = webms[0]
    print("[RENDER] Found raw video:", raw_video)

    if not os.path.exists(AUDIO_TRACK):
        print("[RENDER] ERROR: Master narration audio not found at", AUDIO_TRACK)
        sys.exit(1)

    # Probe raw video duration
    res_probe = subprocess.run([FFMPEG_EXE, "-i", raw_video], capture_output=True, text=True)
    raw_dur = 0.0
    for line in res_probe.stderr.splitlines():
        if "Duration:" in line:
            part = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = part.split(":")
            raw_dur = float(h)*3600 + float(m)*60 + float(s)
            break
    print(f"[RENDER] Raw video duration: {raw_dur:.2f}s")

    # Probe master audio duration
    res_probe_a = subprocess.run([FFMPEG_EXE, "-i", AUDIO_TRACK], capture_output=True, text=True)
    audio_dur = 0.0
    for line in res_probe_a.stderr.splitlines():
        if "Duration:" in line:
            part = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = part.split(":")
            audio_dur = float(h)*3600 + float(m)*60 + float(s)
            break
    print(f"[RENDER] Master audio duration: {audio_dur:.2f}s")

    target_duration = min(raw_dur, audio_dur)
    if target_duration == 0:
        target_duration = 161.0

    print(f"[RENDER] Rendering final video to: {OUTPUT_MP4}")
    print(f"[RENDER] Target duration: {target_duration:.2f}s (~{target_duration/60:.2f} min)")

    cmd_render = [
        FFMPEG_EXE, "-y",
        "-i", raw_video,
        "-i", AUDIO_TRACK,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-profile:v", "high",
        "-level", "4.1",
        "-preset", "medium",
        "-crf", "20",
        "-r", "25",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-ac", "2",
        "-shortest",
        "-movflags", "+faststart",
        OUTPUT_MP4
    ]

    print("[RENDER] Executing FFmpeg command...")
    res = subprocess.run(cmd_render, capture_output=True, text=True)
    if res.returncode != 0:
        print("[RENDER] FFmpeg ERROR:", res.stderr)
        sys.exit(1)

    print("[RENDER] Final video render SUCCESSFUL!")

    # Verify final output with FFprobe
    probe_final = subprocess.run([FFMPEG_EXE, "-i", OUTPUT_MP4], capture_output=True, text=True)
    print("\n" + "="*60)
    print("FINAL RENDERED VIDEO SPECIFICATIONS:")
    for line in probe_final.stderr.splitlines():
        if "Duration:" in line or "Stream #0" in line:
            print(" ", line.strip())
    filesize_mb = os.path.getsize(OUTPUT_MP4) / (1024 * 1024)
    print(f"  File size: {filesize_mb:.2f} MB")
    print(f"  Saved path: {os.path.abspath(OUTPUT_MP4)}")
    print("="*60)

if __name__ == "__main__":
    render_final_video()

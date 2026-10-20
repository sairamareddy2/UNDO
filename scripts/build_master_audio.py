import os
import sys
import subprocess
import json

FFMPEG_EXE = r"C:\Users\ADMIN\Downloads\undo\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
AUDIO_DIR = "artifacts/audio"
TIMESTAMPS_FILE = "artifacts/scene_timestamps.json"
OUTPUT_AUDIO = "artifacts/master_narration.wav"

def build_master_audio():
    if not os.path.exists(TIMESTAMPS_FILE):
        print(f"[AUDIO MASTER] ERROR: {TIMESTAMPS_FILE} not found!")
        sys.exit(1)

    with open(TIMESTAMPS_FILE, "r") as f:
        timestamps = json.load(f)

    total_duration = timestamps.get("total_duration", 160.0)
    print(f"[AUDIO MASTER] Building master narration synchronized to {total_duration:.2f}s video...")

    scene_keys = ["scene1", "scene2", "scene3", "scene4", "scene5", "scene6", "scene7"]
    filter_inputs = []
    filter_complex = []

    for idx, key in enumerate(scene_keys):
        mp3_file = os.path.join(AUDIO_DIR, f"{key}.mp3").replace("\\", "/")
        start_time = timestamps.get(key, 0.0)
        delay_ms = int(start_time * 1000)
        filter_inputs.extend(["-i", mp3_file])
        filter_complex.append(f"[{idx}:a]adelay={delay_ms}|{delay_ms}[a{idx}]")
        print(f"  {key}: start={start_time:.2f}s (delay={delay_ms}ms)")

    mix_str = "".join(f"[a{i}]" for i in range(len(scene_keys)))
    filter_complex.append(f"{mix_str}amix=inputs={len(scene_keys)}:dropout_transition=0:normalize=0[aout]")

    cmd = [
        FFMPEG_EXE, "-y",
        *filter_inputs,
        "-filter_complex", ";".join(filter_complex),
        "-map", "[aout]",
        "-t", f"{total_duration:.2f}",
        "-ar", "44100", "-ac", "2",
        OUTPUT_AUDIO
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("[AUDIO MASTER] FFmpeg Error:", res.stderr)
        sys.exit(1)

    print(f"[AUDIO MASTER] Master audio created: {OUTPUT_AUDIO}")

    # Check duration probe
    probe = subprocess.run([FFMPEG_EXE, "-i", OUTPUT_AUDIO], capture_output=True, text=True)
    for line in probe.stderr.splitlines():
        if "Duration:" in line:
            print(" ", line.strip())
            break

    return True

if __name__ == "__main__":
    build_master_audio()

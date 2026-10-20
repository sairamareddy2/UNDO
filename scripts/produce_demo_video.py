import os
import sys
import time
import subprocess

print("="*70)
print("  UNDO — AUTONOMOUS HACKATHON DEMO VIDEO PRODUCTION PIPELINE")
print("="*70)

# 1. Synthesize narration audio
print("\n>>> STEP 1: Synthesizing narration audio tracks...")
res = subprocess.run([sys.executable, "scripts/synthesize_narration.py"], check=True)

# 2. Record full demo video with Playwright
print("\n>>> STEP 2: Recording browser interactions with Playwright...")
res = subprocess.run([sys.executable, "scripts/record_full_demo.py"], check=True)

# 3. Build synchronized master audio track
print("\n>>> STEP 3: Building synchronized master narration track...")
res = subprocess.run([sys.executable, "scripts/build_master_audio.py"], check=True)

# 4. Render final MP4 video with FFmpeg
print("\n>>> STEP 4: Rendering final MP4 with H.264 video and AAC audio...")
res = subprocess.run([sys.executable, "scripts/render_final_video.py"], check=True)

print("\n" + "="*70)
print("  DEMO VIDEO PRODUCTION COMPLETED SUCCESSFULLY!")
print("="*70)

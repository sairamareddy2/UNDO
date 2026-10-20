import os
import subprocess
import json

FFMPEG_EXE = r"C:\Users\ADMIN\Downloads\undo\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
AUDIO_DIR = "artifacts/audio"

SCENES = {
    "scene1": (
        "Meet UNDO, a reversible, risk-aware AI agent built for the Alexa-plus simulated web experience track. "
        "When autonomous conversational assistants interact with household devices and digital accounts, "
        "large language models can hallucinate or attempt risky operations. "
        "UNDO combines AI-powered action planning with deterministic risk evaluation, human approval, "
        "audit history, and the ability to reverse supported actions."
    ),
    "scene2": (
        "UNDO turns natural-language requests into structured actions. "
        "Here, we submit a request to add two cartons of organic almond milk to our grocery list. "
        "Powered by Google Gemini, the assistant extracts typed parameters, while a separate "
        "deterministic policy engine evaluates each proposed action before it can execute."
    ),
    "scene3": (
        "Low-risk actions can proceed when policy permits them. "
        "Our policy engine verifies the item and approves it with an ALLOW decision. "
        "Once executed, the item commits directly to SQLite and updates the live household view. "
        "UNDO records the relevant state and can restore the previous state for supported operations, "
        "reverting changes with a single click."
    ),
    "scene4": (
        "Sensitive actions require explicit human approval. "
        "When asking to unlock the front door, the policy engine marks the request as REQUIRE APPROVAL. "
        "The AI cannot grant itself permission, and execution is strictly gated. "
        "Once approved on the dashboard and executed, the simulated door lock state transitions to unlocked. "
        "Door operations in this demonstration are simulated in software, not connected to physical hardware."
    ),
    "scene5": (
        "Dangerous actions are blocked before execution. "
        "When a prompt requests to wipe the database and delete all application records, "
        "our security rules trigger an immediate BLOCK. Zero execution controls exist, no database queries are run, "
        "and the incident is recorded to the audit log. "
        "This demonstrates the distinction between an AI proposing an action and the policy engine authorizing it."
    ),
    "scene6": (
        "UNDO also exposes seven tools through an official Python MCP server using Streamable HTTP on port 8001, "
        "enabling compatible clients to interact with its capabilities while retaining the application's policy controls. "
        "External agents discover tools for groceries, reminders, and door locks, and cannot bypass human approval."
    ),
    "scene7": (
        "In summary, UNDO combines AI planning, deterministic risk controls, human approval, "
        "audit history, and reversible execution with 45 passing automated tests. "
        "It demonstrates how AI agents can be designed to act with greater accountability. "
        "Thank you for watching."
    ),
}

def generate_voice_offline():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    durations = {}
    total_dur = 0.0

    print("[AUDIO] Generating offline narration files using Windows Speech Synthesis...")
    for scene_id, text in SCENES.items():
        wav_path = os.path.join(AUDIO_DIR, f"{scene_id}.wav").replace("\\", "/")
        mp3_path = os.path.join(AUDIO_DIR, f"{scene_id}.mp3").replace("\\", "/")

        # PowerShell command to synthesize speech to WAV
        ps_code = f"""
        Add-Type -AssemblyName System.Speech;
        $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer;
        $synth.SelectVoice('Microsoft David Desktop');
        $synth.Rate = 1;
        $synth.SetOutputToWaveFile('{wav_path}');
        $synth.Speak(@'
{text}
'@);
        $synth.Dispose();
        """
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_code], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[AUDIO] Error synthesizing {scene_id}: {res.stderr}")
            continue

        # Convert WAV to high-quality MP3 / AAC using ffmpeg
        cmd_convert = [
            FFMPEG_EXE, "-y", "-i", wav_path,
            "-ar", "44100", "-ac", "2", "-b:a", "192k",
            mp3_path
        ]
        subprocess.run(cmd_convert, capture_output=True)

        # Probe duration
        cmd_probe = [FFMPEG_EXE, "-i", mp3_path]
        res_probe = subprocess.run(cmd_probe, capture_output=True, text=True)
        dur = 0.0
        for line in res_probe.stderr.splitlines():
            if "Duration:" in line:
                part = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = part.split(":")
                dur = float(h)*3600 + float(m)*60 + float(s)
                break

        durations[scene_id] = dur
        total_dur += dur
        print(f"[AUDIO] {scene_id}: {dur:.2f}s | {mp3_path}")

    print("\n" + "="*50)
    print(f"TOTAL SPOKEN NARRATION DURATION: {total_dur:.2f}s ({total_dur/60:.2f} min)")
    print("="*50)

    # Save durations metadata
    with open("artifacts/audio/durations.json", "w") as f:
        json.dump(durations, f, indent=2)

    return durations

if __name__ == "__main__":
    generate_voice_offline()

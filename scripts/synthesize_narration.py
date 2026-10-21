import os
import subprocess
import json

FFMPEG_EXE = r"C:\Users\ADMIN\Downloads\undo\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
AUDIO_DIR = "artifacts/audio"

SCENES = {
    "scene1": (
        "AI assistants can do more than answer questions. They can also take actions, and those actions can be risky. "
        "UNDO is a reversible, risk-aware AI agent designed to evaluate actions, enforce safeguards, and help restore supported changes."
    ),
    "scene2": (
        "UNDO accepts natural-language requests and converts them into structured action proposals. "
        "Gemini assists with planning when available, while a separate deterministic policy engine controls whether the action may proceed."
    ),
    "scene3": (
        "Before execution, UNDO can simulate supported actions in an isolated environment. "
        "The safety report shows projected changes, validation results, possible failure scenarios, and whether rollback was verified. "
        "This gives the user evidence about the operation before the real application state changes."
    ),
    "scene4": (
        "After reviewing the simulation, the user can continue through the normal execution flow. "
        "UNDO applies its policy checks, records the operation, and supports reversing this grocery change. "
        "Simulation and execution are separate steps."
    ),
    "scene5": (
        "Sensitive actions require explicit approval. Even if the simulation completes successfully, it cannot bypass the policy engine. "
        "Here, the simulated door unlock requires human approval before the application executes the change."
    ),
    "scene6": (
        "UNDO also blocks prohibited operations. This destructive request remains blocked rather than executing. "
        "A simulation result can never override a blocked policy decision."
    ),
    "scene7": (
        "UNDO also exposes seven tools through an MCP server using Streamable HTTP. "
        "Compatible clients can inspect state and invoke supported operations while the application retains its policy controls."
    ),
    "scene8": (
        "UNDO combines AI planning, test-before-execute simulation, human approval, policy enforcement, and reversible actions. "
        "It is designed to make AI agent actions more transparent, controlled, and recoverable."
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

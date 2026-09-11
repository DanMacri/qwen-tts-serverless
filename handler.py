"""RunPod serverless worker for Qwen3-TTS voice cloning (Daniel's voice).

Wraps the proven ValyrianTech FastAPI server (already in the base image): boots it,
uploads the baked reference voice once, warms the model, then answers jobs.

Job input:  { "text": "...", "voice": "daniel" (optional), "speed": 1.0 (optional) }
Job output: { "audio_base64": "<wav bytes b64>", "mime": "audio/wav", "voice": "daniel" }
"""
import base64
import os
import subprocess
import time

import requests
import runpod

BASE = "http://127.0.0.1:7860"
REF_WAV = "/app/server/resources/daniel.wav"
REF_LABEL = "daniel"

# 1) Launch the FastAPI TTS server (start.sh runs uvicorn on 7860, loads the model).
_server = subprocess.Popen(["/bin/bash", "/app/server/start.sh"])


def _wait_ready(timeout=900):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if requests.get(BASE + "/openapi.json", timeout=5).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def _register_voice():
    try:
        with open(REF_WAV, "rb") as f:
            r = requests.post(
                BASE + "/upload_audio/",
                data={"audio_file_label": REF_LABEL},
                files={"file": ("daniel.wav", f, "audio/wav")},
                timeout=180,
            )
        print("[worker] voice register:", r.status_code, r.text[:120])
    except Exception as e:
        print("[worker] voice register failed:", e)


def _warm():
    # Force the model fully hot so the first real job is fast.
    try:
        requests.get(
            BASE + "/synthesize_speech/",
            params={"text": "Hola, listo.", "voice": REF_LABEL},
            timeout=300,
        )
        print("[worker] warm synth done")
    except Exception as e:
        print("[worker] warm synth failed:", e)


print("[worker] waiting for TTS server...")
if _wait_ready():
    print("[worker] server up; registering voice + warming")
    _register_voice()
    _warm()
else:
    print("[worker] server did not become ready in time")


def handler(event):
    inp = event.get("input", {}) or {}
    text = (inp.get("text") or "").strip()
    voice = inp.get("voice") or REF_LABEL
    speed = inp.get("speed", 1.0)
    # A warmup ping with no text just boots/keeps the worker hot.
    if not text:
        return {"warmed": True}
    try:
        r = requests.get(
            BASE + "/synthesize_speech/",
            params={"text": text, "voice": voice, "speed": speed},
            timeout=300,
        )
    except Exception as e:
        return {"error": f"synth request failed: {e}"}
    if r.status_code != 200:
        return {"error": f"synth http {r.status_code}: {r.text[:160]}"}
    return {
        "audio_base64": base64.b64encode(r.content).decode(),
        "mime": "audio/wav",
        "voice": voice,
    }


runpod.serverless.start({"handler": handler})

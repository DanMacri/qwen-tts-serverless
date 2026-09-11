"""RunPod serverless worker for Qwen3-TTS voice cloning.

Contains NO personal data. The reference voice is supplied at runtime by the caller
(as base64) and registered per-worker, so the image itself is safe to be public.

Wraps the proven ValyrianTech FastAPI server (in the base image): boots it, then:
  warm/register: { "ref_b64": "<wav b64>", "ref_label": "daniel" }
  synthesize:    { "text": "...", "voice": "daniel", "ref_b64": "<wav b64>", "speed": 1.0 }
Output: { "audio_base64": "<wav b64>", "mime": "audio/wav", "voice": "daniel" }
"""
import base64
import os
import subprocess
import tempfile
import time

import requests
import runpod

BASE = "http://127.0.0.1:7860"
_server = subprocess.Popen(["/bin/bash", "/app/server/start.sh"])
_registered = set()  # labels already uploaded to THIS worker


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


def _register(ref_b64, label):
    if not ref_b64 or label in _registered:
        return label in _registered
    try:
        raw = base64.b64decode(ref_b64)
        p = os.path.join(tempfile.gettempdir(), f"{label}.wav")
        with open(p, "wb") as f:
            f.write(raw)
        with open(p, "rb") as f:
            r = requests.post(
                BASE + "/upload_audio/",
                data={"audio_file_label": label},
                files={"file": (f"{label}.wav", f, "audio/wav")},
                timeout=180,
            )
        if r.status_code == 200:
            _registered.add(label)
            print(f"[worker] registered voice '{label}'")
            return True
        print("[worker] register http", r.status_code, r.text[:120])
    except Exception as e:
        print("[worker] register failed:", e)
    return False


print("[worker] waiting for TTS server...")
_wait_ready()
print("[worker] server ready")


def handler(event):
    inp = event.get("input", {}) or {}
    label = inp.get("ref_label") or inp.get("voice") or "daniel"
    if inp.get("ref_b64"):
        _register(inp["ref_b64"], label)
    text = (inp.get("text") or "").strip()
    if not text:
        # warm-up / register-only ping
        return {"warmed": True, "registered": label in _registered}
    if label not in _registered:
        return {"error": f"voice '{label}' not registered on this worker; include ref_b64"}
    try:
        r = requests.get(
            BASE + "/synthesize_speech/",
            params={"text": text, "voice": label, "speed": inp.get("speed", 1.0)},
            timeout=300,
        )
    except Exception as e:
        return {"error": f"synth request failed: {e}"}
    if r.status_code != 200:
        return {"error": f"synth http {r.status_code}: {r.text[:160]}"}
    return {"audio_base64": base64.b64encode(r.content).decode(), "mime": "audio/wav", "voice": label}


runpod.serverless.start({"handler": handler})

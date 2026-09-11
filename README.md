# qwen-tts-serverless

RunPod serverless worker for Daniel's Qwen3-TTS cloned voice.
Built on `valyriantech/qwen3-tts_server` (models baked in) with a thin `handler.py`
that boots the server, registers the reference voice, warms it, and answers jobs.

Job input: `{ "text": "...", "voice": "daniel", "speed": 1.0 }`
Output: `{ "audio_base64": "<wav b64>", "mime": "audio/wav" }`

Deploy on RunPod Serverless from this repo. Recommended: RTX 3090/4090, min workers 0, max 1.

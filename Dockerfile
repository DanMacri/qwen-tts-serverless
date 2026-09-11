# RunPod serverless worker for Daniel's Qwen3-TTS cloned voice.
# Built on the proven ValyrianTech image (models already baked in), plus a thin
# runpod handler that boots the server, registers the voice, and answers jobs.
FROM valyriantech/qwen3-tts_server:latest

# runpod SDK + requests, into the image's venv.
RUN /opt/venv/bin/pip install --no-cache-dir runpod requests

# Bake Daniel's Spanish reference voice (sample 2).
COPY daniel.wav /app/server/resources/daniel.wav
COPY handler.py /app/server/handler.py

WORKDIR /app/server

# Replace the FastAPI entrypoint with the serverless handler (it starts the server itself).
ENTRYPOINT []
CMD ["/opt/venv/bin/python", "-u", "/app/server/handler.py"]

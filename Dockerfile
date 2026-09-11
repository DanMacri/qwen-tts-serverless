# RunPod serverless worker for Qwen3-TTS voice cloning. NO personal data in the image:
# the reference voice is supplied at runtime by the caller. Safe to be public.
# Built on the proven ValyrianTech image (Qwen model + whisper already baked in).
FROM valyriantech/qwen3-tts_server:latest

# runpod SDK + requests, into the image's venv.
RUN /opt/venv/bin/pip install --no-cache-dir runpod requests

COPY handler.py /app/server/handler.py

WORKDIR /app/server

# Replace the FastAPI entrypoint with the serverless handler (it starts the server itself).
ENTRYPOINT []
CMD ["/opt/venv/bin/python", "-u", "/app/server/handler.py"]

import whisper
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import os
import uuid
import uvicorn

# only adding this one file instead of whole service directory
# with test/test_speech_to_text_service.py

# to test using pytest:
# cd test
# pytest -v --capture=no test_speech_to_text_service.py

# Category: Speech-to-Text Service
# This FastAPI app exposes /transcribe using OpenAI Whisper.

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

model = whisper.load_model("base")

# Ensure temp folder exists
TMP_DIR = "tmp_audio"
os.makedirs(TMP_DIR, exist_ok=True)

@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    # Generate a unique filename for each request
    ext = os.path.splitext(audio.filename)[-1] or ".audio"
    temp_filename = f"{uuid.uuid4().hex}{ext}"
    temp_path = os.path.join(TMP_DIR, temp_filename)
    # Save uploaded file
    contents = await audio.read()
    with open(temp_path, "wb") as f:
        f.write(contents)
    # Transcribe
    try:
        result = model.transcribe(temp_path)
        text = result["text"]
    finally:
        # Clean up temp file
        try:
            os.remove(temp_path)
        except Exception:
            pass
    return JSONResponse({"text": text})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

# To run this service, use:
# uvicorn main:app --host "0.0.0.0" --port 8001


# The number of concurrent requests this service can handle depends on:
# - The number of Uvicorn worker processes (default is 1, can be increased with --workers)
# - Available CPU and memory (Whisper is CPU/GPU intensive)
# - Disk I/O for saving temp files
# - Model loading is shared, but each request processes audio independently

# With the current async FastAPI/Uvicorn setup and unique temp files:
# - Multiple requests can be processed in parallel, limited by hardware and worker count.
# - For true concurrency, run with multiple workers, e.g.:
#   uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
# - Each worker can process one request at a time (per process), so total concurrency = number of workers.

# In summary:
# - The service is compatible with parallel requests.
# - Actual throughput depends on hardware and Uvicorn worker configuration.
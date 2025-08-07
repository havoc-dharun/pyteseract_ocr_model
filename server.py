from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import numpy as np
import cv2
import pytesseract
from PIL import Image
from io import BytesIO
from typing import Optional

from main import parse_lead_info_basic, parse_lead_info_gemini, save_to_csv, save_to_google_sheet

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


def _bytes_to_cv2_image(data: bytes):
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


@app.post("/api/extract")
async def extract_api(file: UploadFile = File(...), use_gemini: Optional[bool] = Form(False)):
    content = await file.read()
    img = _bytes_to_cv2_image(content)
    if img is None:
        return JSONResponse(status_code=400, content={"error": "Invalid image"})
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    parsed = parse_lead_info_gemini(text) if (use_gemini and os.getenv('GEMINI_API_KEY')) else parse_lead_info_basic(text)
    return {"ocr_text": text, "fields": parsed}


@app.post("/api/save")
async def save_api(
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    company: str = Form(...),
    address: str = Form(...),
    website: str = Form(...),
    to_csv: bool = Form(True),
    to_sheet: bool = Form(False),
):
    if to_csv:
        save_to_csv(name, phone, email, company, address, website)
    if to_sheet:
        if not os.path.exists('credentials/token.json') and not os.path.exists('credentials/client_secret.json'):
            return JSONResponse(status_code=400, content={"error": "Google credentials missing"})
        save_to_google_sheet(name, phone, email, company, address, website)
    return {"status": "saved", "csv": to_csv, "sheet": to_sheet}


# Serve built frontend if available
if os.path.isdir("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=False)
# Business Card OCR + Gemini + Google Sheets

## Run locally
1. Python env
```
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```
2. System deps (Ubuntu):
```
sudo apt-get update && sudo apt-get install -y tesseract-ocr libtesseract-dev libleptonica-dev libgl1 libglib2.0-0
```
3. Frontend
```
npm ci
npm run build
```
4. Env
```
export GEMINI_API_KEY=xxxx
# Optional for hosted non-interactive Sheets
export SERVICE_ACCOUNT_FILE=/app/credentials/service-account.json
# If using Web OAuth client locally
export OAUTH_PORT=8080
```
5. Start
```
python server.py
```

## Google Sheets Auth
- Web client: place `credentials/client_secret.json` and ensure redirect `http://localhost:8080/`. First save triggers consent and writes `credentials/token.json`.
- Service Account: set `SERVICE_ACCOUNT_FILE` and share the Sheet with the service account email.

## Docker
```
docker build -t ocr-app .
docker run -p 8000:8000 -e GEMINI_API_KEY=xxxx \
  -e SERVICE_ACCOUNT_FILE=/app/credentials/service-account.json \
  -v $(pwd)/credentials:/app/credentials \
  -v $(pwd)/leads.csv:/app/leads.csv \
  ocr-app
```
Open http://localhost:8000
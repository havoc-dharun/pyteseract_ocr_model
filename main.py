import cv2
import pytesseract
import re
import csv
import os
import json

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
try:
    import google.generativeai as genai
except Exception:
    genai = None

# ---------- CONFIGURATION ----------
SPREADSHEET_ID = "1C04dxBk3Ck9PUvRLaGt5FofR24_sAUSiniXngOC6VLg"
RANGE_NAME = "Sheet1!A1"
CSV_FILE = "leads.csv"
CREDENTIALS_FILE = "credentials/client_secret.json"
TOKEN_FILE = "credentials/token.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
USE_GEMINI_DEFAULT = os.getenv('USE_GEMINI', '0') == '1'


# ---------- SAVE TO GOOGLE SHEET ----------
def save_to_google_sheet(name, phone, email, company, address, website):
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    service = build('sheets', 'v4', credentials=creds)
    values = [[name, phone, email, company, address, website]]
    body = {'values': values}
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME,
        valueInputOption="RAW",
        body=body
    ).execute()
    print("✅ Lead also saved to Google Sheet.")


# ---------- SAVE TO CSV ----------
def save_to_csv(name, phone, email, company, address, website):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Name", "Phone", "Email", "Company", "Address", "Website"])
        writer.writerow([name, phone, email, company, address, website])
    print("✅ Lead saved to 'leads.csv'")


# ---------- OCR PROCESSING ----------
def extract_lead_info(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    name = phone = email = company = address = website = "Not found"
    company_keywords = r'\b(inc|ltd|llp|pvt|private|limited|corp|technologies|solutions|systems|enterprises|group|industries|co\.?)\b'

    for line in lines:
        lower = line.lower()
        if email == "Not found":
            m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", line)
            if m: email = m.group()
        if website == "Not found" and "www" in lower:
            m = re.search(r"(www\.[^\s,]+)", line)
            if m: website = m.group()
        if phone == "Not found":
            digits = re.sub(r'\D', '', line)
            if len(digits) >= 10: phone = digits
        if address == "Not found" and "/" in line:
            address = line

    for line in lines[:6]:
        if re.search(company_keywords, line, re.IGNORECASE):
            company = line
            break
    if company == "Not found":
        for line in lines[:6]:
            if line.isupper() and len(line.split()) <= 4:
                company = line
                break
    if company == "Not found":
        for line in lines[:6]:
            words = line.split()
            if words and all(w[0].isupper() for w in words if w[0].isalpha()):
                company = line
                break

    for line in lines:
        if (name == "Not found" and
            all(val not in line for val in [email, phone, website, address, company]) and
            not any(x in line for x in ['@', 'www', '/', '.com'])):
            name = line
            break

    print("\n🎯 Extracted Lead Info:")
    print(f"  Name:    {name}")
    print(f"  Phone:   {phone}")
    print(f"  Email:   {email}")
    print(f"  Company: {company}")
    print(f"  Address: {address}")
    print(f"  Website: {website}")

    if input("\n✏️ Edit any field? (y/n): ").strip().lower() == 'y':
        name    = input(f"Name [{name}]: ") or name
        phone   = input(f"Phone [{phone}]: ") or phone
        email   = input(f"Email [{email}]: ") or email
        company = input(f"Company [{company}]: ") or company
        address = input(f"Address [{address}]: ") or address
        website = input(f"Website [{website}]: ") or website

    if input("\n💾 Save to CSV & Google Sheet? (y/n): ").strip().lower() == 'y':
        save_to_csv(name, phone, email, company, address, website)
        save_to_google_sheet(name, phone, email, company, address, website)
    else:
        print("❌ Skipped saving.")


# ---------- GEMINI-POWERED EXTRACTION ----------
def _clean_json_from_markdown(text: str) -> str:
    if not text:
        return text
    text = text.strip()
    if text.startswith("```"):
        # remove code fences if present
        lines = [ln for ln in text.splitlines() if not ln.strip().startswith("```")]
        return "\n".join(lines).strip()
    return text


def extract_lead_info_gemini(ocr_text: str):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("⚠️ GEMINI_API_KEY not set. Falling back to basic extraction.")
        return extract_lead_info(ocr_text)
    if genai is None:
        print("⚠️ google-generativeai package not available. Falling back to basic extraction.")
        return extract_lead_info(ocr_text)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL)
        instruction = (
            "Extract lead information from the OCR text of a business card and return a single JSON object "
            "with exactly these keys: Name, Phone, Email, Company, Address, Website. "
            "Rules: If a value is unknown, use 'Not found'. Phone should contain digits only (no spaces or symbols). "
            "Prefer the company legal or display name; Address is a single-line mailing/location string if present; "
            "Website may be a domain or full URL. Do not include any extra text.")
        prompt = f"OCR Text:\n{ocr_text}"
        resp = model.generate_content([
            {"text": instruction},
            {"text": prompt}
        ])
        raw = getattr(resp, 'text', None) or (resp.candidates[0].content.parts[0].text if getattr(resp, 'candidates', None) else None)
        cleaned = _clean_json_from_markdown(raw or "")
        data = json.loads(cleaned)
        name = data.get('Name', 'Not found')
        phone = data.get('Phone', 'Not found')
        email = data.get('Email', 'Not found')
        company = data.get('Company', 'Not found')
        address = data.get('Address', 'Not found')
        website = data.get('Website', 'Not found')
    except Exception as e:
        print(f"⚠️ Gemini extraction failed: {e}. Falling back to basic extraction.")
        return extract_lead_info(ocr_text)

    print("\n🤖 Gemini Extracted Lead Info:")
    print(f"  Name:    {name}")
    print(f"  Phone:   {phone}")
    print(f"  Email:   {email}")
    print(f"  Company: {company}")
    print(f"  Address: {address}")
    print(f"  Website: {website}")

    if input("\n✏️ Edit any field? (y/n): ").strip().lower() == 'y':
        name    = input(f"Name [{name}]: ") or name
        phone   = input(f"Phone [{phone}]: ") or phone
        email   = input(f"Email [{email}]: ") or email
        company = input(f"Company [{company}]: ") or company
        address = input(f"Address [{address}]: ") or address
        website = input(f"Website [{website}]: ") or website

    if input("\n💾 Save to CSV & Google Sheet? (y/n): ").strip().lower() == 'y':
        save_to_csv(name, phone, email, company, address, website)
        save_to_google_sheet(name, phone, email, company, address, website)
    else:
        print("❌ Skipped saving.")


# ---------- IMAGE CAPTURE FROM WEBCAM ----------
def capture_from_webcam():
    while True:
        print("📸 Starting webcam... Press SPACE to capture the visiting card.")
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            cv2.imshow('Visiting Card Scanner', frame)
            if cv2.waitKey(1) & 0xFF == ord(' '):
                cv2.imwrite("captured_card.jpg", frame)
                break
        cap.release()
        cv2.destroyAllWindows()

        img = cv2.imread("captured_card.jpg")
        cv2.imshow("Preview", img)
        print("👁️ Close preview window to continue...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        if input("✅ Proceed with this image? (y/n): ").strip().lower() == 'y':
            break
        print("🔁 Retake...\n")

    gray = cv2.cvtColor(cv2.imread("captured_card.jpg"), cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    use_gemini = USE_GEMINI_DEFAULT and os.getenv('GEMINI_API_KEY')
    if os.getenv('GEMINI_API_KEY') and not USE_GEMINI_DEFAULT:
        choice = input("🤖 Use Gemini for extraction? (y/n): ").strip().lower()
        use_gemini = (choice == 'y')
    if use_gemini:
        extract_lead_info_gemini(text)
    else:
        extract_lead_info(text)


# ---------- PROCESS EXISTING IMAGE ----------
def process_image_file():
    path = input("📂 Enter image filename: ").strip()
    if not os.path.exists(path):
        print("❌ File not found.")
        return
    gray = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    use_gemini = USE_GEMINI_DEFAULT and os.getenv('GEMINI_API_KEY')
    if os.getenv('GEMINI_API_KEY') and not USE_GEMINI_DEFAULT:
        choice = input("🤖 Use Gemini for extraction? (y/n): ").strip().lower()
        use_gemini = (choice == 'y')
    if use_gemini:
        extract_lead_info_gemini(text)
    else:
        extract_lead_info(text)


# ---------- MAIN MENU ----------
def main():
    print("\n🧠 Business Card OCR")
    print("1️⃣  Capture from webcam")
    print("2️⃣  Load from existing image")
    choice = input("Choose (1 or 2): ").strip()
    if choice == '1':
        capture_from_webcam()
    elif choice == '2':
        process_image_file()
    else:
        print("❌ Invalid choice.")

if __name__ == "__main__":
    main()

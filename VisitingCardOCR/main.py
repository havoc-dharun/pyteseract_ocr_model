import cv2
import pytesseract
import re

pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'  # Adjust if needed

def extract_lead_info(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    email = phone = website = address = name = company = designation = "Not found"

    used_lines = set()

    # EMAIL
    for line in lines:
        match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}", line)
        if match:
            email = match.group(0)
            used_lines.add(line)
            break

    # PHONE (10+ digits only)
    for line in lines:
        digits = re.sub(r"\D", "", line)
        if len(digits) >= 10:
            phone = digits
            used_lines.add(line)
            break

    # WEBSITE (contains www)
    for line in lines:
        if "www" in line:
            website = line.strip()
            used_lines.add(line)
            break

    # ADDRESS (contains '/')
    for line in lines:
        if "/" in line:
            address = line.strip()
            used_lines.add(line)
            break

    # DESIGNATION (contains keywords)
    designation_keywords = [
        "director", "founder", "co-founder", "ceo", "cto", "cfo", "president", "vp",
        "general manager", "assistant manager", "manager", "sales manager", "marketing manager",
        "business development", "account manager", "regional manager", "territory manager",
        "brand manager", "product manager", "strategy head", "growth lead", "consultant",
        "advisor", "partner", "owner", "proprietor", "chairman", "principal",
        "operations head", "project lead", "team lead", "coordinator", "executive",
        "intern", "recruiter", "hr", "talent acquisition", "trainer", "faculty",
        "doctor", "dr", "surgeon", "physician", "dentist", "orthopedic", "cardiologist",
        "radiologist", "lab technician", "nurse", "medical officer", "clinic head",
        "accountant", "auditor", "financial analyst", "investment banker", "cxo",
        "engineer", "software engineer", "developer", "architect", "data scientist",
        "ml engineer", "ai engineer", "tech lead", "system admin", "network engineer",
        "mechanical engineer", "civil engineer", "qa engineer", "test engineer",
        "content writer", "copywriter", "editor", "designer", "graphic designer",
        "ui designer", "ux designer", "creative head", "marketing executive",
        "digital marketer", "seo analyst", "ppc specialist", "brand strategist",
        "logistics manager", "supply chain", "warehouse head", "procurement",
        "legal advisor", "attorney", "lawyer", "advocate", "researcher",
        "scientist", "biologist", "chemist", "pharmacist", "school principal"
    ]

    for line in lines:
        if any(role.lower() in line.lower() for role in designation_keywords):
            designation = line.strip()
            used_lines.add(line)
            break

    # COMPANY (near logo/unique fonts assumed from early/top line if not used elsewhere)
    for i, line in enumerate(lines[:3]):
        if line not in used_lines and len(line.split()) <= 6:
            company = line.strip()
            used_lines.add(line)
            break

    # NAME (first non-used line, max 16 chars, not email/phone/website)
    for line in lines:
        if (
            line not in used_lines
            and not any(token in line for token in ['@', 'www', '/', '.com'])
            and len(line) <= 16
        ):
            name = line.strip()
            used_lines.add(line)
            break

    print("\n🎯  Extracted Lead Info:")
    print(f"    Name:    {name}")
    print(f"    Designation: {designation}")
    print(f"    Phone:   {phone}")
    print(f"    Email:   {email}")
    print(f"    Company: {company}")
    print(f"    Address: {address}")
    print(f"    Website: {website}")


def capture_and_extract():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open camera")
        return

    print("\n📸 Press SPACE to capture the visiting card")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        cv2.imshow("Visiting Card Scanner", frame)
        key = cv2.waitKey(1)
        if key % 256 == 32:  # Space key
            cv2.imwrite("captured_card.jpg", frame)
            print("\n✅ Image captured!")
            break

    cap.release()
    cv2.destroyAllWindows()

    img = cv2.imread("captured_card.jpg")
    text = pytesseract.image_to_string(img)
    extract_lead_info(text)


if __name__ == "__main__":
    capture_and_extract()

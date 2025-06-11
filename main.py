import cv2
import pytesseract
import re

def extract_lead_info(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    name, phone, email, company, address, website = "Not found", "Not found", "Not found", "Not found", "Not found", "Not found"

    for line in lines:
        lower_line = line.lower()

        # EMAIL
        if email == "Not found":
            match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", line)
            if match:
                email = match.group()

        # WEBSITE
        if website == "Not found" and "www" in lower_line:
            match = re.search(r"(www\.[^\s,]+)", line)
            if match:
                website = match.group()

        # PHONE
        if phone == "Not found":
            digits_only = re.sub(r'\D', '', line)
            if len(digits_only) >= 10:
                phone = digits_only

        # ADDRESS
        if address == "Not found" and "/" in line:
            address = line

        # COMPANY (UPPERCASE ONLY)
        if company == "Not found" and line.isupper():
            company = line

    # NAME (fallback)
    for line in lines:
        if (
            name == "Not found"
            and all(val not in line for val in [email, phone, website, address, company])
            and not any(x in line for x in ['@', 'www', '/', '.com'])
        ):
            name = line
            break

    print("\n🎯 Extracted Lead Info:")
    print(f"    Name:    {name}")
    print(f"    Phone:   {phone}")
    print(f"    Email:   {email}")
    print(f"    Company: {company}")
    print(f"    Address: {address}")
    print(f"    Website: {website}")

def main():
    cap = cv2.VideoCapture(0)
    print("📸 Press SPACE to capture the visiting card...")
    while True:
        ret, frame = cap.read()
        cv2.imshow('Visiting Card Scanner', frame)
        if cv2.waitKey(1) & 0xFF == ord(' '):
            cv2.imwrite("captured_card.jpg", frame)
            break

    cap.release()
    cv2.destroyAllWindows()

    img = cv2.imread("captured_card.jpg")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    extract_lead_info(text)

if __name__ == "__main__":
    main()

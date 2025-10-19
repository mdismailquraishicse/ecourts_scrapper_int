# 📌 eCourt Scraper

A Python-based scraper that fetches court case details and handles captcha-solving using Tesseract OCR.

---

## ✅ 1. Clone the Repository

```bash
git clone https://github.com/mdismailquraishicse/ecourts_scrapper_int
cd ecourts_scrapper_int
```

---

## ✅ 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ✅ 3. Install Tesseract OCR (Required for Captcha Solving)

Make sure Tesseract is installed on your local machine:

### 🔹 Ubuntu / Debian
```bash
sudo apt update
sudo apt install tesseract-ocr
```

### 🔹 macOS (Homebrew)
```bash
brew install tesseract
```

### 🔹 Windows
Download the installer from:  
https://github.com/tesseract-ocr/tesseract

After installation, ensure the Tesseract path is correctly set in your code if needed.

---

## ✅ 4.a Run the Scraper with Arguments

**Example:**
```bash
python ecourt_scrapper.py \
  --state_name "West Bengal" \
  --district_name "Paschim bardhaman" \
  --court_complex "ASANSOL COURT COMPLEX" \
  --court_name "9-Indrani Gupta-CJM" \
  --causelist_date 21-10-2025 \
  --case_type criminal
```

---

## ✅ 4.b Run FastAPI App (Optional API Mode)

```bash
uvicorn main:app --reload
```

After running, open:
```
http://127.0.0.1:8000
```

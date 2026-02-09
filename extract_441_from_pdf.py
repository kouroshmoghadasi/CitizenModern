# -*- coding: utf-8 -*-
"""
استخراج دقیقاً ۴۴۱ سوال به ترتیب فایل 2021-11-15_Citizenship 441 question.pdf
منبع تنها: همین سند PDF. اگر متن PDF کم باشد (PDF تصویری)، از OCR (Tesseract) استفاده می‌شود.
برای PDF تصویری: Tesseract را نصب کنید (https://github.com/UB-Mannheim/tesseract/wiki) سپس این اسکریپت را دوباره اجرا کنید.
خروجی: static/citizenship_441_questions.json (num, q, answer از PDF)
بعد از اجرا: python extract_441_questions.py
"""
import re
import json
import os
import io

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(SCRIPT_DIR, "2021-11-15_Citizenship 441 question.pdf")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "static", "citizenship_441_questions.json")

# حداقل طول متن برای ۴۴۱ سوال (بدون OCR)
MIN_TEXT_LENGTH = 20000


def extract_text_pypdf(path):
    """استخراج متن با pypdf (فقط برای PDFهای متنی)."""
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += (page.extract_text() or "") + "\n"
    return text


def extract_text_ocr(path):
    """استخراج متن با OCR (PyMuPDF + Tesseract) برای PDF تصویری."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("برای PDF تصویری نصب کنید: pip install pymupdf")
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        raise ImportError("برای OCR نصب کنید: pip install pytesseract Pillow")
    # مسیر رایج Tesseract در ویندوز (در صورت نصب)
    for tesseract_cmd in [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]:
        if os.path.isfile(tesseract_cmd):
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            break
    doc = fitz.open(path)
    full_text = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        png_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(png_bytes))
        text = pytesseract.image_to_string(img, lang="eng")
        full_text.append(text)
    doc.close()
    return "\n".join(full_text)


def extract_text_from_pdf(path):
    """اول pypdf؛ اگر متن کافی نبود با OCR."""
    text = extract_text_pypdf(path)
    if len(text.strip()) < MIN_TEXT_LENGTH:
        print("Text from PDF is short (likely image-based). Using OCR...")
        try:
            text = extract_text_ocr(path)
        except Exception as e:
            if "tesseract" in str(e).lower() or "TesseractNotFoundError" in type(e).__name__:
                raise  # main will write placeholders and print install instructions
            raise
    return text


def parse_441_from_text(full_text):
    """
    سوالات را با الگوی شماره (۱. یا 1. یا 1) جدا می‌کند.
    پشتیبانی از فرمت‌های متداول: "1. Question... Answer: X" یا "1. Question... \\n X"
    """
    # تقسیم با الگوی شروع سوال: عدد ۱ تا ۴۴۱ و نقطه یا پرانتز
    parts = re.split(r"(?m)^\s*(\d{1,3})[\.\)]\s+", full_text)
    questions = []
    i = 1
    seen_nums = set()
    while i + 1 < len(parts):
        num_str = parts[i].strip()
        body = parts[i + 1].strip()
        i += 2
        try:
            num = int(num_str)
        except ValueError:
            continue
        if num < 1 or num > 441 or num in seen_nums:
            continue
        seen_nums.add(num)
        # تا شروع سوال بعدی برش بزن
        body = re.sub(r"\s*\n\s*(\d{1,3})[\.\)]\s+", "\n---NEXT---\n", body, count=1)
        if "---NEXT---" in body:
            body = body.split("---NEXT---")[0].strip()
        # استخراج پاسخ: Answer: / Correct: / یا آخرین خط معقول
        answer = ""
        for pattern in [
            r"(?i)(?:Answer|Correct|پاسخ)\s*[:\-]\s*(.+?)(?=\n\n|\n\d|\Z)",
            r"(?i)(?:Answer|Correct)\s*[:\-]\s*(.+?)$",
        ]:
            m = re.search(pattern, body, re.DOTALL)
            if m:
                answer = re.sub(r"\s+", " ", m.group(1).strip())[:400]
                break
        # سوال = کل متن منهای خط پاسخ
        q = re.sub(r"(?i)(?:Answer|Correct|پاسخ)\s*[:\-]?\s*.*", "", body, flags=re.DOTALL).strip()
        q = re.sub(r"\s+", " ", q)[:1000]
        if not q:
            q = "Question %d" % num
        questions.append({"num": num, "q": q, "answer": answer})
    # مرتب‌سازی بر اساس num و پر کردن شکاف‌ها
    by_num = {it["num"]: it for it in questions}
    result = []
    for n in range(1, 442):
        if n in by_num:
            result.append(by_num[n])
        else:
            result.append({"num": n, "q": "Question %d (from PDF)" % n, "answer": ""})
    return result[:441]


def write_placeholder_json():
    """۴۴۱ placeholder وقتی استخراج از PDF ممکن نیست (بدون Tesseract)."""
    questions = [{"num": n, "q": "Question %d (from PDF)" % n, "answer": ""} for n in range(1, 442)]
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    return questions


def main():
    if not os.path.isfile(PDF_PATH):
        print("PDF not found:", PDF_PATH)
        print("Place '2021-11-15_Citizenship 441 question.pdf' in the project root.")
        return 1
    print("Reading PDF:", PDF_PATH)
    try:
        text = extract_text_from_pdf(PDF_PATH)
    except SystemExit:
        raise
    except Exception as e:
        if "tesseract" in str(e).lower() or "TesseractNotFoundError" in type(e).__name__:
            print("Tesseract OCR not found. Writing 441 placeholders (PDF order).")
            print("To extract content: install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki then re-run.")
            write_placeholder_json()
            print("Wrote 441 placeholders to", OUTPUT_PATH)
            print("Run: python extract_441_questions.py  then install Tesseract and run this again.")
            return 0
        raise
    print("Total text length:", len(text))
    print("Parsing 441 questions in PDF order...")
    questions = parse_441_from_text(text)
    if len(questions) > 441:
        questions = questions[:441]
    while len(questions) < 441:
        n = len(questions) + 1
        questions.append({"num": n, "q": "Question %d (from PDF)" % n, "answer": ""})
    questions = questions[:441]
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    with_content = sum(1 for q in questions if (q.get("q") or "").strip() and "from PDF" not in (q.get("q") or ""))
    print("Wrote %d questions to %s (%d with extracted text)." % (len(questions), OUTPUT_PATH, with_content))
    print("Now run: python extract_441_questions.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main() or 0)

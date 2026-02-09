# -*- coding: utf-8 -*-
"""
استخراج ۵۷۱ سوال از PDF «571 Question For Citizenship Test .pdf» به همان ترتیب.
خروجی: static/citizenship_571_questions.json
اجرا: python extract_571_from_pdf.py
"""
import re
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(SCRIPT_DIR, "571 Question For Citizenship Test .pdf")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "static", "citizenship_571_questions.json")


def extract_text_from_pdf(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise ImportError("Install pypdf: pip install pypdf")
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
        text += "\n"
    return text


def parse_single_block(block):
    """از یک بلوک متن، سوال، گزینه‌ها و اندیس پاسخ صحیح را استخراج می‌کند."""
    block = re.sub(r"\s+", " ", block).strip()
    options = []
    for m in re.finditer(r"\b([A-D])[\.\)]\s*([^A-D]+?)(?=\s*[A-D][\.\)]|\s*Answer\s*:|\s*Correct\s*:|\s*$)", block, re.IGNORECASE):
        options.append(m.group(2).strip())
    ans = re.search(r"(?:Answer|Correct)\s*[:\-]?\s*([A-D])\b", block, re.IGNORECASE)
    correct = ord(ans.group(1).upper()) - ord("A") if ans else 0
    q = re.sub(r"\s*[A-D][\.\)].*", "", block, flags=re.DOTALL)
    q = re.sub(r"\s*(?:Answer|Correct)\s*[:\-]?\s*[A-D].*", "", q, flags=re.IGNORECASE).strip()
    return q or "Question", options if options else ["(See PDF for options)"], min(correct, 3)


def parse_571_questions(full_text):
    """متن PDF را به بلوک‌های سوال (شماره. متن) تقسیم و هر بلوک را پارس می‌کند."""
    # تقسیم با الگوی شروع سوال: عدد ۱ تا ۳ رقمی و بعد نقطه یا پرانتز
    parts = re.split(r"(?m)^\s*(\d{1,3})[\.\)]\s+", full_text)
    questions = []
    i = 1
    while i + 1 < len(parts):
        num = parts[i].strip()
        body = parts[i + 1].strip()
        i += 2
        if not num.isdigit():
            continue
        n = int(num)
        if n < 1 or n > 571:
            continue
        q, options, correct = parse_single_block(body)
        questions.append({
            "q": q[:800],
            "q_fa": "",
            "options": options,
            "correct": min(correct, len(options) - 1) if options else 0,
            "page": 0,
            "section": "571 Question For Citizenship Test",
            "book_text": "",
        })
    return questions


def main():
    if not os.path.isfile(PDF_PATH):
        print("PDF not found:", PDF_PATH)
        return
    print("Reading PDF...")
    text = extract_text_from_pdf(PDF_PATH)
    print("Parsing questions...")
    questions = parse_571_questions(text)
    if len(questions) < 300:
        # روش ساده: هر بار که خط با عدد. شروع شد یک سوال جدید
        questions = []
        blocks = re.split(r"(?m)^\s*(\d{1,3})[\.\)]\s+", text)
        for i in range(1, len(blocks) - 1):
            if i % 2 == 0:
                continue
            num = blocks[i].strip()
            if not num.isdigit():
                continue
            body = blocks[i + 1].strip()
            q, options, correct = parse_single_block(body)
            questions.append({
                "q": q[:800],
                "q_fa": "",
                "options": options,
                "correct": min(correct, len(options) - 1) if options else 0,
                "page": 0,
                "section": "571 Question For Citizenship Test",
                "book_text": "",
            })
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print("Wrote", len(questions), "questions to", OUTPUT_PATH)


if __name__ == "__main__":
    main()

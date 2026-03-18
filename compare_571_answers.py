# -*- coding: utf-8 -*-
"""
مقایسه پاسخ‌های صحیح JSON فعلی ۵۷۱ با پاسخ‌های استخراج‌شده از PDF.
فقط آمار و لیست سوالات دارای اختلاف را چاپ می‌کند؛ تغییری اعمال نمی‌شود.
"""
import re
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(SCRIPT_DIR, "571 Question For Citizenship Test .pdf")
JSON_PATH = os.path.join(SCRIPT_DIR, "static", "citizenship_571_questions.json")


def extract_text_from_pdf(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
        text += "\n"
    return text


def parse_single_block(block):
    block = re.sub(r"\s+", " ", block).strip()
    options = []
    for m in re.finditer(r"\b([A-D])[\.\)]\s*([^A-D]+?)(?=\s*[A-D][\.\)]|\s*Answer\s*:|\s*Correct\s*:|\s*$)", block, re.IGNORECASE):
        options.append(m.group(2).strip())
    ans = re.search(r"(?:Answer|Correct)\s*[:\-]?\s*([A-D])\b", block, re.IGNORECASE)
    correct = ord(ans.group(1).upper()) - ord("A") if ans else 0
    q = re.sub(r"\s*[A-D][\.\)].*", "", block, flags=re.DOTALL)
    q = re.sub(r"\s*(?:Answer|Correct)\s*[:\-]?\s*[A-D].*", "", q, flags=re.IGNORECASE).strip()
    return q or "Question", options if options else ["(See PDF)"], min(correct, 3)


def parse_571_from_pdf(text):
    parts = re.split(r"(?m)^\s*(\d{1,3})[\.\)]\s+", text)
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
            "num": n,
            "q": q[:300],
            "options": options,
            "correct": min(correct, len(options) - 1) if options else 0,
        })
    return questions


def main():
    if not os.path.isfile(PDF_PATH):
        print("PDF not found:", PDF_PATH)
        return
    if not os.path.isfile(JSON_PATH):
        print("JSON not found:", JSON_PATH)
        return

    print("Reading PDF...")
    text = extract_text_from_pdf(PDF_PATH)
    pdf_questions = parse_571_from_pdf(text)
    print("PDF: parsed", len(pdf_questions), "questions")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        json_questions = json.load(f)
    print("JSON: loaded", len(json_questions), "questions")

    # Match by index (question 1 = index 0, ...)
    diffs = []
    for i in range(min(len(pdf_questions), len(json_questions))):
        pq = pdf_questions[i]
        jq = json_questions[i]
        pdf_correct = pq["correct"]
        json_correct = jq.get("correct", 0)
        if pdf_correct != json_correct:
            num = i + 1
            jopts = jq.get("options") or []
            popts = pq.get("options") or []
            json_ans = jopts[json_correct][:60] if json_correct < len(jopts) else "?"
            pdf_ans = popts[pdf_correct][:60] if pdf_correct < len(popts) else "?"
            diffs.append({
                "num": num,
                "json_correct": json_correct,
                "pdf_correct": pdf_correct,
                "json_answer": json_ans,
                "pdf_answer": pdf_ans,
                "q_preview": (jq.get("q") or "")[:70],
            })

    out_lines = []
    out_lines.append("")
    out_lines.append("=" * 60)
    out_lines.append("Statistics: questions where JSON correct answer differs from PDF")
    out_lines.append("=" * 60)
    out_lines.append("Total differences: " + str(len(diffs)))
    out_lines.append("PDF parsed questions: " + str(len(pdf_questions)))
    out_lines.append("JSON questions: " + str(len(json_questions)))
    out_lines.append("")
    if not diffs:
        out_lines.append("All answers match the PDF.")
    else:
        out_lines.append("List (question # | JSON correct index | PDF correct index):")
        out_lines.append("-" * 60)
        for d in diffs:
            out_lines.append("Q" + str(d["num"]) + " | JSON correct index: " + str(d["json_correct"]) + " | PDF correct index: " + str(d["pdf_correct"]))
            out_lines.append("  Question: " + d["q_preview"] + "...")
            out_lines.append("  Current answer in JSON: " + d["json_answer"])
            out_lines.append("  Correct per PDF: " + d["pdf_answer"])
            out_lines.append("")
        out_lines.append("Question numbers to fix: " + str([d['num'] for d in diffs]))

    report = "\n".join(out_lines)
    print(report)
    report_path = os.path.join(SCRIPT_DIR, "571_answer_diff_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    print("\nReport also written to:", report_path)


if __name__ == "__main__":
    main()

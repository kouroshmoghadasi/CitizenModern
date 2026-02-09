# -*- coding: utf-8 -*-
"""
استخراج دقیقاً ۵۷۱ سوال از فایل 571_Questions_English_Persian.html (همان ترتیب و محتوا).
خروجی: static/citizenship_571_questions.json
اجرا: python extract_571_from_html.py
"""
import re
import json
import os
import html

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(SCRIPT_DIR, "571_Questions_English_Persian.html")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "static", "citizenship_571_questions.json")


def strip_html(text):
    if not text:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_options(a_en_raw):
    """اگر پاسخ چندگزینه‌ای است (A. ... B. ... C. ... D. ...) به لیست گزینه تبدیل می‌کند."""
    a_en = strip_html(a_en_raw)
    a_en = re.sub(r"^\s*A:\s*", "", a_en, flags=re.IGNORECASE).strip()
    raw = a_en_raw.replace("<br>", "\n").replace("<br/>", "\n")
    parts = re.split(r"\s*[A-Da-d][\.\)]\s*", raw)
    parts = [strip_html(p).replace("A:", "").strip() for p in parts if strip_html(p).strip()]
    if len(parts) >= 2 and len(parts) <= 6:
        opts = [re.sub(r"^\s*A:\s*", "", p, flags=re.I).strip()[:500] for p in parts if p]
        if len(opts) >= 2:
            return opts, 0
    return [a_en[:500] or "(Answer)"], 0


def extract_one_block(block):
    """از یک بلوک <div class="qa">...</div> فیلدها را استخراج می‌کند."""
    num_m = re.search(r'<div class="num">#(\d+)</div>', block)
    q_en_m = re.search(r'<div class="q-en">(.*?)</div>', block, re.DOTALL)
    a_en_m = re.search(r'<div class="a-en">(.*?)</div>', block, re.DOTALL)
    q_fa_m = re.search(r'<div class="q-fa">(.*?)</div>', block, re.DOTALL)
    a_fa_m = re.search(r'<div class="a-fa">(.*?)</div>', block, re.DOTALL)
    if not all([num_m, q_en_m, a_en_m, q_fa_m, a_fa_m]):
        return None
    q_en = strip_html(q_en_m.group(1)).replace("Q:", "").strip()
    q_fa = strip_html(q_fa_m.group(1)).replace("س:", "").strip()
    a_en_raw = a_en_m.group(1)
    options, correct = parse_options(a_en_raw)
    return {
        "q": q_en[:1500],
        "q_fa": q_fa[:1500],
        "options": options,
        "correct": min(correct, len(options) - 1) if options else 0,
        "page": 0,
        "section": "571 Question For Citizenship Test",
        "book_text": "",
    }


def placeholder_question(num):
    return {
        "q": "Question #%d (missing in source HTML – see PDF)." % num,
        "q_fa": "سوال #%d (در منبع HTML موجود نیست – به PDF مراجعه کنید)." % num,
        "options": ["(See PDF)"],
        "correct": 0,
        "page": 0,
        "section": "571 Question For Citizenship Test",
        "book_text": "",
    }


def extract_questions():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # پیدا کردن هر سوال با <div class="num">#N</div> و شماره آن
    num_matches = list(re.finditer(r'<div class="num">#(\d+)</div>', content))
    questions = []
    for i, m in enumerate(num_matches):
        num = int(m.group(1))
        start = m.start()
        end = num_matches[i + 1].start() if i + 1 < len(num_matches) else len(content)
        block = content[start:end]
        # در فایل HTML سوال #275 غایب است (#274 بعد #276) — جای خالی می‌گذاریم تا ترتیب ۱ تا ۵۷۱ حفظ شود
        if i > 0 and num > int(num_matches[i - 1].group(1)) + 1:
            for missing in range(int(num_matches[i - 1].group(1)) + 1, num):
                questions.append(placeholder_question(missing))
        q = extract_one_block(block)
        if q:
            questions.append(q)
        else:
            q_en_m = re.search(r'<div class="q-en">(.*?)</div>', block, re.DOTALL)
            q_fa_m = re.search(r'<div class="q-fa">(.*?)</div>', block, re.DOTALL)
            a_en_m = re.search(r'<div class="a-en">(.*?)</div>', block, re.DOTALL)
            if q_en_m and a_en_m:
                questions.append({
                    "q": strip_html(q_en_m.group(1)).replace("Q:", "").strip()[:1500],
                    "q_fa": strip_html(q_fa_m.group(1)).replace("س:", "").strip()[:1500] if q_fa_m else "",
                    "options": [re.sub(r"^\s*A:\s*", "", strip_html(a_en_m.group(1)), flags=re.I).strip()[:500] or "(Answer)"],
                    "correct": 0,
                    "page": 0,
                    "section": "571 Question For Citizenship Test",
                    "book_text": "",
                })
    # سوال ۵۷۱ در منبع HTML با بخش «Dates» ادغام شده؛ طبق PDF اصلاح می‌کنیم
    if len(questions) >= 571 and "How many judges are serving in Supreme Court of Canada?" in (questions[570].get("q") or ""):
        opt = questions[570].get("options") or []
        if len(opt) == 1 and (len(opt[0]) > 400 or "Dates" in opt[0]):
            questions[570]["options"] = ["9", "7", "10", "5"]
            questions[570]["correct"] = 0
            questions[570]["book_text"] = "The Supreme Court of Canada has nine judges. (Source: 571 Question For Citizenship Test .pdf)"
    return questions


def main():
    if not os.path.isfile(HTML_PATH):
        print("File not found:", HTML_PATH)
        return
    print("Extracting from", HTML_PATH)
    questions = extract_questions()
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print("Wrote", len(questions), "questions to", OUTPUT_PATH)
    if len(questions) != 571:
        print("Warning: expected 571 questions, got", len(questions))


if __name__ == "__main__":
    main()

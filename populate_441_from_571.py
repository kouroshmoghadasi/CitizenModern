# -*- coding: utf-8 -*-
"""
پر کردن همه ۴۴۱ سوال از بانک ۵۷۱؛ سوال ۱ و ۲ مطابق فایل اصلی حفظ می‌شوند.
خروجی: static/citizenship_441_questions.json
بعد از اجرا: python extract_441_questions.py
"""
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_441 = os.path.join(SCRIPT_DIR, "static", "citizenship_441_questions.json")
PATH_571 = os.path.join(SCRIPT_DIR, "static", "citizenship_571_questions.json")


def to_441_item(idx_1based, item_571):
    """یک آیتم ۵۷۱ را به فرمت ۴۴۱ (با num, و در صورت امکان answer) تبدیل می‌کند."""
    opts = item_571.get("options") or []
    correct = item_571.get("correct", 0)
    if correct < 0 or correct >= len(opts):
        correct = 0
    answer = ""
    if opts:
        letter = chr(65 + correct) if correct < 26 else ""
        answer = ("%s. " % letter + opts[correct]) if letter else opts[correct]
    return {
        "num": idx_1based,
        "q": item_571.get("q") or "",
        "q_fa": item_571.get("q_fa") or item_571.get("q") or "",
        "options": opts,
        "correct": correct,
        "book_text": item_571.get("book_text") or "",
        "answer": answer,
    }


def main():
    with open(PATH_441, "r", encoding="utf-8") as f:
        current_441 = json.load(f)
    with open(PATH_571, "r", encoding="utf-8") as f:
        bank_571 = json.load(f)

    # سوال ۱ و ۲ رسمی را حفظ کن
    q1 = current_441[0] if len(current_441) > 0 else {}
    q2 = current_441[1] if len(current_441) > 1 else {}

    # اطمینان از وجود num
    if "num" not in q1:
        q1["num"] = 1
    if "num" not in q2:
        q2["num"] = 2

    out = [q1, q2]
    # سوالات ۳ تا ۴۴۱ از بانک ۵۷۱: ایندکس‌های ۲ تا ۴۴۰ (۴۳۹ سوال)
    for i in range(2, 441):
        if i < len(bank_571):
            out.append(to_441_item(i + 1, bank_571[i]))
        else:
            out.append({
                "num": i + 1,
                "q": "Question %d (see study guide)" % (i + 1),
                "q_fa": "سوال %d (راهنما را ببینید)" % (i + 1),
                "options": ["See Discover Canada study guide."],
                "correct": 0,
                "book_text": "",
                "answer": "",
            })

    with open(PATH_441, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("Written 441 questions to %s (Q1,Q2 preserved; Q3–441 from 571 bank)." % PATH_441)


if __name__ == "__main__":
    main()

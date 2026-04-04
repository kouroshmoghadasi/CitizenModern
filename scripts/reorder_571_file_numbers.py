# -*- coding: utf-8 -*-
"""یک‌بار: شمارهٔ سوال در سایت = شمارهٔ فایل (images_N → سوال N).
جابه‌جایی: بلوک فعلی سوالات ~Q38–Q50 از جایگاه‌های زودهنگام به ایندکس 37..49."""
import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH_571 = ROOT / "static" / "citizenship_571_questions.json"
PATH_CH1 = ROOT / "static" / "chapter1_questions.json"

FILLER_Q = (
    "Mobility rights allow Canadians to live and work in any province or territory "
    "and to enter and leave Canada freely, within the law."
)


def ch1_pick_filler():
    with PATH_CH1.open(encoding="utf-8") as f:
        ch1 = json.load(f)
    for item in ch1:
        if item.get("q") == "What are \"mobility rights\"?":
            return {
                "q": item["q"],
                "q_fa": item.get("q_fa") or "",
                "options": list(item["options"]),
                "correct": item["correct"],
                "page": 0,
                "section": "Citizenship practice (50-item set)",
                "book_text": FILLER_Q,
                "q_fr": item.get("q_fr") or item["q"],
                "options_fr": list(item.get("options_fr") or item["options"]),
                "expl_fr": item.get("expl_fr") or FILLER_Q,
            }
    return None


def ch1_to_571(item):
    return {
        "q": item["q"],
        "q_fa": item.get("q_fa") or "",
        "options": list(item["options"]),
        "correct": item["correct"],
        "page": 0,
        "section": "Citizenship practice (50-item set)",
        "book_text": item.get("book_text") or "",
        "q_fr": item.get("q_fr") or item["q"],
        "options_fr": list(item.get("options_fr") or item["options"]),
        "expl_fr": item.get("expl_fr") or item.get("book_text") or "",
    }


def main():
    d = json.loads(PATH_571.read_text(encoding="utf-8"))
    if len(d) != 50:
        raise SystemExit(f"Expected 50 questions, got {len(d)}")

    head = [deepcopy(x) for x in d[0:7]]
    misplaced_tail = [deepcopy(x) for x in d[7:19]]
    mid_raw = [deepcopy(x) for x in d[19:49]]

    def _norm_q(s):
        return (s or "").strip().lower().rstrip("?")

    dup_phrase = _norm_q("What are the two principles upon which Canada is founded?")
    mid = []
    for x in mid_raw:
        if _norm_q(x.get("q")) == dup_phrase:
            continue
        mid.append(x)

    while len(mid) < 30:
        with PATH_CH1.open(encoding="utf-8") as f:
            ch1 = json.load(f)
        for item in ch1:
            cand = ch1_to_571(item)
            key = _norm_q(cand["q"])
            if key == dup_phrase:
                continue
            if any(_norm_q(y.get("q")) == key for y in mid + head):
                continue
            mid.append(cand)
            if len(mid) >= 30:
                break

    if len(mid) != 30:
        raise SystemExit(f"mid length {len(mid)}, need 30")

    if len(misplaced_tail) != 12:
        raise SystemExit(f"misplaced_tail {len(misplaced_tail)}, need 12")

    filler39 = ch1_pick_filler()
    if not filler39:
        raise SystemExit("no filler for Q39")

    tail = [misplaced_tail[0], filler39] + misplaced_tail[1:]

    out = head + mid + tail
    if len(out) != 50:
        raise SystemExit(f"out len {len(out)}")

    PATH_571.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK: 1-7 head, 8-37 middle, 38-50 tail (Q38 Constitutional … + Q39 filler mobility … Q50 Métis)")


if __name__ == "__main__":
    main()

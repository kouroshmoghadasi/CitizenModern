# -*- coding: utf-8 -*-
"""Q6 = images_6 (ordered liberty age 800); shift old Q6 (two principles) to Q7; drop dup mobility."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "static" / "citizenship_571_questions.json"

ORDERED = {
    "q": "How old is the tradition of ordered liberty that Canada contains?",
    "q_fa": "سنت «آزادی نظم‌مند» (ordered liberty) که کانادا دارد، چند سال قدمت دارد؟",
    "options": ["1000", "800", "700", "900"],
    "correct": 1,
    "book_text": "Canada contains an 800 years old tradition of ordered liberty, which dates back to the signing of Magna Carta.",
    "q_fr": "Quel âge a la tradition de liberté ordonnée que compte le Canada ?",
    "options_fr": ["1000", "800", "700", "900"],
    "expl_fr": "Le Canada compte une tradition de liberté ordonnée vieille de 800 ans, remontant à la signature de la Magna Carta.",
    "page": 0,
    "section": "Citizenship practice (50-item set)",
}

MOBILITY_Q = 'What are "mobility rights"?'


def main():
    d = json.loads(PATH.read_text(encoding="utf-8"))
    if len(d) != 50:
        raise SystemExit(f"expected 50, got {len(d)}")

    two_p = d[5]
    d[5] = ORDERED
    d.insert(6, two_p)
    if len(d) != 51:
        raise SystemExit("insert failed")

    mob = [i for i, x in enumerate(d) if x.get("q") == MOBILITY_Q]
    if len(mob) < 2:
        raise SystemExit(f"expected 2 mobility dupes, got {mob}")
    del d[mob[-1]]

    if len(d) != 50:
        raise SystemExit(f"after dedupe len {len(d)}")

    PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    for i in range(5, 9):
        print(i + 1, d[i]["q"][:72])


if __name__ == "__main__":
    main()

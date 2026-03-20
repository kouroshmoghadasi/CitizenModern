# -*- coding: utf-8 -*-
"""Extract Chapter 4 (Modern Canada) from `templates/scripts.html`.

Writes: `static/chapter4_questions.json`

Note: options_fa is not included; backend fills it using _fa_lookup,
unless we later provide `static/chapter4_options_fa.json` for missing keys.
"""

import json
import os
import re


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(BASE, "templates", "scripts.html")
OUT_PATH = os.path.join(BASE, "static", "chapter4_questions.json")

with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    s = f.read()

# Stop at Chapter 5 comment.
m = re.search(r"const chapter4Questions = \[(.*?)\];\s*\n\s*// Chapter 5", s, re.DOTALL)
if not m:
    raise SystemExit("chapter4 block not found")

block = m.group(1)
parts = re.split(r"\},\s*\n\s*\{", block)

out = []
for i, p in enumerate(parts):
    p = p.strip()
    if not p.startswith("{"):
        p = "{" + p
    if not p.endswith("}"):
        p = p + "}"

    # Remove book_text field to keep JSON small.
    p = re.sub(r",\s*book_text:\s*\"[^\"]*\"\s*", "", p)

    try:
        q = re.search(r'q:\s*"((?:[^"\\]|\\.)*)"', p)
        q_fa = re.search(r'q_fa:\s*"((?:[^"\\]|\\.)*)"', p)
        q_fr = re.search(r'q_fr:\s*"((?:[^"\\]|\\.)*)"', p)
        opts_m = re.search(r"options:\s*\[(.*?)\]\s*,", p, re.DOTALL)
        opts_fr_m = re.search(r"options_fr:\s*\[(.*?)\]\s*,", p, re.DOTALL)
        correct_m = re.search(r"correct:\s*(\d+)", p)

        if not all([q, q_fa, q_fr, opts_m, opts_fr_m, correct_m]):
            continue

        def get_strings(x: str):
            return re.findall(r'"((?:[^"\\]|\\.)*)"', x)

        def unescape_js_string(t: str) -> str:
            # In scripts.html, quotes are escaped as \" inside strings.
            return t.replace('\\"', '"')

        opt_list = get_strings(opts_m.group(1))
        opt_fr_list = get_strings(opts_fr_m.group(1))

        out.append(
            {
                "q": unescape_js_string(q.group(1)),
                "q_fa": unescape_js_string(q_fa.group(1)),
                "q_fr": unescape_js_string(q_fr.group(1)),
                "options": [unescape_js_string(x) for x in opt_list],
                "options_fr": [unescape_js_string(x) for x in opt_fr_list],
                "correct": int(correct_m.group(1)),
            }
        )
    except Exception as e:
        print("err at", i, e)
        continue

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("Written", len(out), "questions to", OUT_PATH)


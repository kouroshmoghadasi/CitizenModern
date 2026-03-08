# -*- coding: utf-8 -*-
"""خروجی: لیست کامل متن‌های یکتای گزینه (همهٔ گزینه‌ها در همهٔ سوالات) برای ترجمه."""
import json
import os

base = os.path.join(os.path.dirname(__file__), '..')
path_571 = os.path.join(base, 'static', 'citizenship_571_questions.json')

with open(path_571, 'r', encoding='utf-8') as f:
    data = json.load(f)

seen = set()
for q in data:
    for opt in (q.get('options') or []):
        if opt and isinstance(opt, str):
            seen.add(opt.strip())

have = set()
for name in ('571_options_fa.json', '571_options_fa_extra.json'):
    path_fa = os.path.join(base, 'static', name)
    if os.path.isfile(path_fa):
        with open(path_fa, 'r', encoding='utf-8') as f:
            fa = json.load(f)
        for k, v in (fa or {}).items():
            if isinstance(k, str) and not k.strip().startswith('_') and v:
                have.add(k.strip())

missing = sorted(seen - have)
out_path = os.path.join(base, 'static', '571_options_missing.txt')
with open(out_path, 'w', encoding='utf-8') as out:
    for m in missing:
        out.write(m + '\n')
print("Missing count:", len(missing), "->", out_path)
for m in missing:
    print(m)

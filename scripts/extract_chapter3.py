# -*- coding: utf-8 -*-
"""Extract Chapter 3 (Canada's History) from scripts.html to static/chapter3_questions.json.
   options_fa: backend will fill from _fa_lookup when missing."""
import re, json, os
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(base, 'templates', 'scripts.html')
with open(path, 'r', encoding='utf-8') as f:
    s = f.read()
m = re.search(r"const chapter3Questions = \[(.*?)\];\s*\n\s*// Chapter 4", s, re.DOTALL)
if not m:
    raise SystemExit('chapter3 block not found')
block = m.group(1)
parts = re.split(r'\},\s*\n\s*\{', block)
out = []
for i, p in enumerate(parts):
    p = p.strip()
    if not p.startswith('{'):
        p = '{' + p
    if not p.endswith('}'):
        p = p + '}'
    p = re.sub(r',\s*book_text:\s*"[^"]*"\s*', '', p)
    try:
        q = re.search(r'q:\s*"((?:[^"\\]|\\.)*)"', p)
        q_fa = re.search(r'q_fa:\s*"((?:[^"\\]|\\.)*)"', p)
        q_fr = re.search(r'q_fr:\s*"((?:[^"\\]|\\.)*)"', p)
        opts_m = re.search(r'options:\s*\[(.*?)\]\s*,', p, re.DOTALL)
        opts_fr_m = re.search(r'options_fr:\s*\[(.*?)\]\s*,', p, re.DOTALL)
        correct_m = re.search(r'correct:\s*(\d+)', p)
        if not all([q, q_fa, q_fr, opts_m, opts_fr_m, correct_m]):
            continue
        def get_strings(s):
            return re.findall(r'"((?:[^"\\]|\\.)*)"', s)
        opt_list = get_strings(opts_m.group(1))
        opt_fr_list = get_strings(opts_fr_m.group(1))
        out.append({
            "q": q.group(1).replace('\\"', '"'),
            "q_fa": q_fa.group(1).replace('\\"', '"'),
            "q_fr": q_fr.group(1).replace('\\"', '"'),
            "options": opt_list,
            "options_fr": opt_fr_list,
            "correct": int(correct_m.group(1))
        })
    except Exception as e:
        print('err at', i, e)
        continue

out_path = os.path.join(base, 'static', 'chapter3_questions.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print('Written', len(out), 'questions to', out_path)

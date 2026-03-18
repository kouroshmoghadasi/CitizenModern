# -*- coding: utf-8 -*-
"""List option texts from Q9+ that have no Persian translation in the FA lookup."""
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(SCRIPT_DIR, 'static')


def build_map():
    en_to_fa = {}
    # 414
    try:
        path414 = os.path.join(BASE, 'citizenship_414_questions.json')
        with open(path414, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for q in data:
            opts_en = q.get('options_en') or []
            opts_fa = q.get('options_fa') or []
            for j, en in enumerate(opts_en):
                if j < len(opts_fa) and en and opts_fa[j]:
                    en_to_fa[en.strip()] = opts_fa[j].strip()
    except Exception:
        pass
    for name in ('571_options_fa.json', '571_options_fa_extra.json', '571_options_fa_complete.json'):
        p = os.path.join(BASE, name)
        if os.path.isfile(p):
            with open(p, 'r', encoding='utf-8') as f:
                d = json.load(f)
            if isinstance(d, dict):
                for k, v in d.items():
                    if k and isinstance(k, str) and not k.strip().startswith('_') and v:
                        en_to_fa[k.strip()] = v.strip()
    def _norm(t):
        if not t:
            return t
        t = t.strip()
        t = t.replace('\u2019', "'")
        return t
    for k in list(en_to_fa.keys()):
        low = k.lower()
        if low not in en_to_fa:
            en_to_fa[low] = en_to_fa[k]
        kn = _norm(k)
        if kn and kn not in en_to_fa:
            en_to_fa[kn] = en_to_fa[k]
    return en_to_fa


def fa_lookup(en_to_fa, text):
    t = text.strip() if text else ''
    if not t:
        return t
    if t in en_to_fa:
        return en_to_fa[t]
    if t.lower() in en_to_fa:
        return en_to_fa[t.lower()]
    t_norm = t.replace('\u2019', "'")
    if t_norm in en_to_fa:
        return en_to_fa[t_norm]
    return text


def main():
    with open(os.path.join(BASE, 'citizenship_571_questions.json'), 'r', encoding='utf-8') as f:
        questions = json.load(f)
    en_to_fa = build_map()
    missing = set()
    for i in range(8, len(questions)):  # Q9 = index 8
        opts = questions[i].get('options') or []
        for o in opts:
            if not o or not o.strip():
                continue
            o = o.strip()
            if fa_lookup(en_to_fa, o) == o:
                missing.add(o)
    for s in sorted(missing):
        print(s)
    print("\nTotal missing:", len(missing))


if __name__ == "__main__":
    main()

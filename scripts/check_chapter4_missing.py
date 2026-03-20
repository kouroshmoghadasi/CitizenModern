# -*- coding: utf-8 -*-
import json
import os


def build_map():
    en_to_fa = {}
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
    static_dir = os.path.abspath(static_dir)

    for name in (
        "571_options_fa.json",
        "571_options_fa_extra.json",
        "571_options_fa_complete.json",
        "571_options_fa_q9.json",
        "chapter3_options_fa.json",
        "chapter4_options_fa.json",
    ):
        path = os.path.join(static_dir, name)
        if not os.path.isfile(path):
            continue
        try:
            extra = json.load(open(path, "r", encoding="utf-8"))
        except Exception:
            continue
        if isinstance(extra, dict):
            for k, v in extra.items():
                if k and isinstance(k, str) and not k.strip().startswith("_") and v:
                    en_to_fa[k.strip()] = str(v).strip()

    # mimic app.py normalization
    def _norm(t):
        if not t:
            return t
        t = t.strip()
        t = t.replace("\u2019", "'")
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
    t = (text or "").strip()
    if not t:
        return t
    if t in en_to_fa:
        return en_to_fa[t]
    low = t.lower()
    if low in en_to_fa:
        return en_to_fa[low]
    t_norm = t.replace("\u2019", "'")
    if t_norm in en_to_fa:
        return en_to_fa[t_norm]
    return text


def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chapter_path = os.path.join(base, "static", "chapter4_questions.json")

    with open(chapter_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    opts = set()
    for q in data:
        for o in q.get("options", []):
            opts.add(o)

    en_to_fa = build_map()
    missing = []
    for o in sorted(opts):
        fa = fa_lookup(en_to_fa, o)
        if fa == o:
            missing.append(o)

    print("unique options:", len(opts))
    print("missing translations:", len(missing))
    print("first 200 missing:")
    for x in missing[:200]:
        print("-", x)

    # Save for accurate key matching (UTF-8)
    out_txt = os.path.join(base, "static", "chapter4_missing_options.txt")
    out_json = os.path.join(base, "static", "chapter4_missing_options.json")
    with open(out_txt, "w", encoding="utf-8") as f:
        for x in missing:
            f.write(x + "\n")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(missing, f, ensure_ascii=False, indent=2)

    print("Saved missing list to:")
    print("-", out_txt)
    print("-", out_json)


if __name__ == "__main__":
    main()


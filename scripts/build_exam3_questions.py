# -*- coding: utf-8 -*-
"""
Build static/exam3_questions.json from Canadas History-2.docx.
Same pipeline as exam2; CORRECT verified against chapter3 / Discover Canada.
"""
import difflib
import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "static", "exam3_questions.json")
DOCX = r"e:\OK Projects\Nemoneh Question Citizen CA\Canadas History-2.docx"

# ۲۸ سوال — ترکیب تطبیق بانک + تأیید دستی (chapter3 / کتاب رسمی)
CORRECT = [
    3,
    3,
    0,
    2,
    1,
    1,
    2,
    3,
    0,
    0,
    0,
    0,
    2,
    3,
    3,
    3,
    3,
    2,
    3,
    1,
    0,
    3,
    0,
    2,
    3,
    0,
    0,
    0,
]


def _clean_text(s: str) -> str:
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    s = s.replace("George-tienne", "George-Étienne").replace("Georgetienne", "George-Étienne")
    s = s.replace("Mtis", "Métis").replace("Kanata", "Kanata")
    s = s.replace("Sir George-tienne", "Sir George-Étienne")
    s = s.replace("Canadas", "Canada's").replace("Lauriers", "Laurier's")
    s = s.replace("\ufffd", "é")
    s = re.sub(r"^\d+\.\s*", "", s)
    return s.strip()


def _parse_docx(path: str):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    paras = []
    for p in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
        texts = []
        for t in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
            if t.text:
                texts.append(t.text)
            if t.tail:
                texts.append(t.tail)
        line = "".join(texts).strip()
        if line:
            paras.append(_clean_text(line))
    blocks = paras[1:]
    qs = []
    i = 0
    while i < len(blocks):
        q = blocks[i]
        if not q.endswith("?"):
            i += 1
            continue
        q = _clean_text(q)
        i += 1
        opts = []
        while i < len(blocks) and not blocks[i].endswith("?"):
            opts.append(_clean_text(blocks[i]))
            i += 1
        qs.append((q, opts))
    return qs


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().strip())


def _options_tuple_key(opts_en: list) -> tuple:
    return tuple(_norm(x) for x in opts_en)


def _build_options_lookup(bank: list):
    fa_map = {}
    fr_map = {}
    for item in bank:
        oen = item.get("options") or item.get("options_en") or []
        if not oen:
            continue
        ofa = item.get("options_fa")
        ofr = item.get("options_fr")
        key = _options_tuple_key(oen)
        if ofa and len(ofa) == len(oen):
            fa_map[key] = ofa
        if ofr and len(ofr) == len(oen):
            fr_map[key] = ofr
    return fa_map, fr_map


def _load_json_questions(*filenames):
    base = os.path.join(ROOT, "static")
    out = []
    for fn in filenames:
        p = os.path.join(base, fn)
        if not os.path.isfile(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                out.extend(data)
        except Exception:
            pass
    return out


def _best_bank_match(q_en: str, n_opts: int, bank: list, min_ratio: float = 0.68):
    nq = _norm(q_en)
    best = None
    best_r = 0.0
    for item in bank:
        bq = item.get("q") or ""
        if not bq:
            continue
        opts = item.get("options") or item.get("options_en") or []
        if len(opts) != n_opts:
            continue
        r = difflib.SequenceMatcher(None, nq, _norm(bq)).ratio()
        if r > best_r:
            best_r = r
            best = item
    if best_r >= min_ratio and best:
        return best, best_r
    return None, 0.0


def _fa_fr_from_bank(item: dict, opts_en: list):
    q_fa = item.get("q_fa") or item.get("q")
    q_fr = item.get("q_fr") or item.get("q")
    o_en = item.get("options") or item.get("options_en") or []
    opts_fa = item.get("options_fa")
    opts_fr = item.get("options_fr")
    if not opts_fa or len(opts_fa) != len(opts_en):
        opts_fa = None
    if not opts_fr or len(opts_fr) != len(opts_en):
        opts_fr = None
    if opts_fa:
        idx_map = []
        for i, e in enumerate(opts_en):
            best_j = max(
                range(len(o_en)),
                key=lambda j: difflib.SequenceMatcher(None, _norm(e), _norm(o_en[j])).ratio(),
            )
            idx_map.append(best_j)
        if len(set(idx_map)) == len(idx_map):
            opts_fa = [opts_fa[idx_map[i]] for i in range(len(opts_en))]
        else:
            opts_fa = None
    if opts_fr:
        idx_map = []
        for i, e in enumerate(opts_en):
            best_j = max(
                range(len(o_en)),
                key=lambda j: difflib.SequenceMatcher(None, _norm(e), _norm(o_en[j])).ratio(),
            )
            idx_map.append(best_j)
        if len(set(idx_map)) == len(idx_map):
            opts_fr = [opts_fr[idx_map[i]] for i in range(len(opts_en))]
        else:
            opts_fr = None
    return q_fa, q_fr, opts_fa, opts_fr


def main():
    qs = _parse_docx(DOCX)
    n = len(qs)
    assert n == len(CORRECT), (n, len(CORRECT))

    bank = _load_json_questions(
        "chapter3_questions.json",
        "chapter4_questions.json",
        "citizenship_571_questions.json",
        "citizenship_414_questions.json",
        "question_bank.json",
    )
    fa_by_opts, fr_by_opts = _build_options_lookup(bank)

    def _sorted_opts_key(opts):
        return tuple(sorted(_norm(x) for x in opts))

    out = []
    for i, ((q_en, opts_en), cor) in enumerate(zip(qs, CORRECT)):
        assert 0 <= cor < len(opts_en), (i, cor, len(opts_en))
        item, ratio = _best_bank_match(q_en, len(opts_en), bank, min_ratio=0.65)
        q_fa = q_fr = None
        opts_fa = opts_fr = None
        if item:
            q_fa, q_fr, opts_fa, opts_fr = _fa_fr_from_bank(item, opts_en)
        if not opts_fa:
            k = _options_tuple_key(opts_en)
            opts_fa = fa_by_opts.get(k)
            opts_fr = fr_by_opts.get(k) or opts_fr
        if not opts_fa:
            sk = _sorted_opts_key(opts_en)
            for ok, ofa in fa_by_opts.items():
                if len(ofa) != len(opts_en):
                    continue
                if _sorted_opts_key(list(ok)) != sk:
                    continue
                bank_norm = list(ok)
                idx_map = []
                for en in opts_en:
                    pn = _norm(en)
                    idx_map.append(
                        max(
                            range(len(bank_norm)),
                            key=lambda j: (
                                1.0
                                if bank_norm[j] == pn
                                else difflib.SequenceMatcher(
                                    None, pn, bank_norm[j]
                                ).ratio()
                            ),
                        )
                    )
                if len(set(idx_map)) != len(idx_map):
                    continue
                opts_fa = [ofa[idx_map[mi]] for mi in range(len(opts_en))]
                ofr = fr_by_opts.get(ok)
                if ofr and len(ofr) == len(opts_en):
                    opts_fr = [ofr[idx_map[mi]] for mi in range(len(opts_en))]
                break
        if not q_fa:
            q_fa = q_en
        if not q_fr:
            q_fr = q_en
        if not opts_fa:
            opts_fa = list(opts_en)
        if not opts_fr:
            opts_fr = list(opts_en)
        out.append(
            {
                "q": q_en,
                "q_fr": q_fr,
                "q_fa": q_fa,
                "options_en": opts_en,
                "options_fr": opts_fr,
                "options_fa": opts_fa,
                "correct": cor,
            }
        )

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("Wrote", OUT, "n=", len(out))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Extract 414 questions from 414_Question1_Display.html to static/citizenship_414_questions.json
   for use with the citizenship_414 template.
"""
import os
import re
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(SCRIPT_DIR, '414_Question1_Display.html')
OUT_PATH = os.path.join(SCRIPT_DIR, 'static', 'citizenship_414_questions.json')


def strip_html(text):
    if not text:
        return ''
    # Remove <b>Q:</b> / <b>A:</b> / <b>س:</b> / <b>ج:</b> and similar
    text = re.sub(r'<[^>]+>', '', text)
    return text.replace('&amp;', '&').replace('&#39;', "'").strip()


def main():
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by <div class="qa">; each block is until next <div class="qa"> or <footer
    parts = re.split(r'<div class="qa">', content)
    blocks = []
    for p in parts[1:]:  # skip part before first qa
        end = p.find('<footer')
        if end != -1:
            p = p[:end]
        # take content until we would hit next full qa (optional)
        blocks.append(p.strip())
    out = []
    for i, block in enumerate(blocks):
        num = i + 1
        q_en_el = re.search(r'<div class="q-en">(.*?)</div>', block, re.DOTALL)
        a_en_el = re.search(r'<div class="a-en">(.*?)</div>', block, re.DOTALL)
        q_fa_el = re.search(r'<div class="q-fa">(.*?)</div>', block, re.DOTALL)
        a_fa_el = re.search(r'<div class="a-fa">(.*?)</div>', block, re.DOTALL)
        # Two <div class="explanation"> per block: first EN, second FA
        explanations = re.findall(r'<div class="explanation">(.*?)</div>', block, re.DOTALL)
        expl_en = strip_html(explanations[0]) if len(explanations) > 0 else ''
        expl_fa = strip_html(explanations[1]) if len(explanations) > 1 else expl_en

        q_en = strip_html(q_en_el.group(1)) if q_en_el else ''
        a_en = strip_html(a_en_el.group(1)) if a_en_el else ''
        q_fa = strip_html(q_fa_el.group(1)) if q_fa_el else ''
        a_fa = strip_html(a_fa_el.group(1)) if a_fa_el else ''

        out.append({
            'num': num,
            'q_en': q_en,
            'a_en': a_en,
            'expl_en': expl_en,
            'q_fa': q_fa,
            'a_fa': a_fa,
            'expl_fa': expl_fa,
        })

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print('Wrote %d questions to %s' % (len(out), OUT_PATH))


if __name__ == '__main__':
    main()

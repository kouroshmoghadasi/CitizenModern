# -*- coding: utf-8 -*-
"""
One-time script: translate all 414 questions (q_en, a_en, expl_en) to French
and save q_fr, a_fr, expl_fr into static/citizenship_414_questions.json.
Run: pip install deep-translator
     python translate_414_to_french.py
Takes about 2–3 minutes (414 questions × 3 fields, with short delay to avoid rate limit).
"""
import os
import json
import time
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(SCRIPT_DIR, 'static', 'citizenship_414_questions.json')
BACKUP_PATH = os.path.join(SCRIPT_DIR, 'static', 'citizenship_414_questions.json.bak')


def main():
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        print('Install: pip install deep-translator')
        return

    if not os.path.isfile(JSON_PATH):
        print('File not found:', JSON_PATH)
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    shutil.copy2(JSON_PATH, BACKUP_PATH)
    print('Backup saved to', BACKUP_PATH)

    translator = GoogleTranslator(source='en', target='fr')
    n = len(questions)
    for i, q in enumerate(questions):
        num = q.get('num', i + 1)
        # Translate question (strip "Q: " for natural translation)
        q_en = (q.get('q_en') or '').strip()
        if q_en:
            try:
                body = q_en[3:].strip() if q_en.startswith('Q: ') else q_en
                if body:
                    q['q_fr'] = 'Q : ' + translator.translate(body)
                else:
                    q['q_fr'] = q_en
            except Exception as e:
                q['q_fr'] = q.get('q_fr') or q_en
                print('  q%d q_en err: %s' % (num, e))
        else:
            q['q_fr'] = q.get('q_fr') or ''

        # Translate answer
        a_en = (q.get('a_en') or '').strip()
        if a_en:
            try:
                q['a_fr'] = translator.translate(a_en)
            except Exception as e:
                q['a_fr'] = q.get('a_fr') or a_en
                print('  q%d a_en err: %s' % (num, e))
        else:
            q['a_fr'] = q.get('a_fr') or ''

        # Translate explanation
        expl_en = (q.get('expl_en') or '').strip()
        if expl_en:
            try:
                q['expl_fr'] = translator.translate(expl_en)
            except Exception as e:
                q['expl_fr'] = q.get('expl_fr') or expl_en
                print('  q%d expl_en err: %s' % (num, e))
        else:
            q['expl_fr'] = q.get('expl_fr') or ''

        if (i + 1) % 20 == 0:
            print('Translated %d / %d' % (i + 1, n))
        time.sleep(0.15)

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print('Done. Saved q_fr, a_fr, expl_fr for all %d questions to %s' % (n, JSON_PATH))


if __name__ == '__main__':
    main()

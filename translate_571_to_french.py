# -*- coding: utf-8 -*-
"""
One-time script: translate 571 questions (q, options, book_text) to French
and save q_fr, options_fr, expl_fr into static/citizenship_571_questions.json.
Run: pip install deep-translator
     python translate_571_to_french.py
Takes several minutes (571 questions × question + options + book_text, with delay).
"""
import os
import json
import time
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(SCRIPT_DIR, 'static', 'citizenship_571_questions.json')
BACKUP_PATH = os.path.join(SCRIPT_DIR, 'static', 'citizenship_571_questions.json.bak')


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
    SAVE_EVERY = 50  # save progress every N questions so you can re-run if interrupted
    for i, q in enumerate(questions):
        # Skip if already has French (allows resume / re-run)
        if q.get('q_fr') and q.get('options_fr'):
            if (i + 1) % 100 == 0:
                print('Skip (already done) %d / %d' % (i + 1, n))
            continue

        # Translate question
        q_en = (q.get('q') or '').strip()
        if q_en:
            try:
                q['q_fr'] = translator.translate(q_en)
            except Exception as e:
                q['q_fr'] = q.get('q_fr') or q_en
                print('  q%d q err: %s' % (i + 1, e))
        else:
            q['q_fr'] = q.get('q_fr') or ''

        # Translate options
        opts = q.get('options') or []
        opts_fr = q.get('options_fr') or []
        if len(opts_fr) != len(opts):
            opts_fr = []
            for o in opts:
                o_str = (o or '').strip()
                if o_str:
                    try:
                        opts_fr.append(translator.translate(o_str))
                    except Exception as e:
                        opts_fr.append(o_str)
                else:
                    opts_fr.append(o_str)
            q['options_fr'] = opts_fr

        # Translate book_text -> expl_fr
        book = (q.get('book_text') or '').strip()
        if book and not q.get('expl_fr'):
            try:
                q['expl_fr'] = translator.translate(book)
            except Exception as e:
                q['expl_fr'] = q.get('expl_fr') or book
                print('  q%d book_text err: %s' % (i + 1, e))
        else:
            q.setdefault('expl_fr', '')

        if (i + 1) % 30 == 0:
            print('Translated %d / %d' % (i + 1, n))
        time.sleep(0.12)

        # Save progress every SAVE_EVERY questions
        if (i + 1) % SAVE_EVERY == 0:
            with open(JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
            print('  Saved progress at %d' % (i + 1))

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print('Done. Saved q_fr, options_fr, expl_fr for all %d questions to %s' % (n, JSON_PATH))


if __name__ == '__main__':
    main()

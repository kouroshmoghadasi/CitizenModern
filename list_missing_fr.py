# -*- coding: utf-8 -*-
"""List all questions, options, and book_text that lack a French translation."""
import sys
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from extract_441_questions import extract_questions, OPTIONS_EN_FR, translate_option_to_fr
from extract_441_questions import EXPL_EN_FR, translate_expl_to_fr

try:
    from citizenship_441_questions_fr import QUESTIONS_EN_FR
except ImportError:
    QUESTIONS_EN_FR = {}

def main():
    questions = extract_questions()
    unique_q = set()
    unique_opts = set()
    unique_expl = set()
    for q in questions:
        unique_q.add(q['q'].strip())
        for o in q.get('options') or []:
            unique_opts.add(o.strip())
        bt = (q.get('book_text') or 'See Discover Canada study guide.').strip()
        unique_expl.add(bt)

    missing_q = sorted(unique_q - set(QUESTIONS_EN_FR.keys()))
    missing_opt = sorted(unique_opts - set(OPTIONS_EN_FR.keys()))
    missing_expl = sorted(unique_expl - set(EXPL_EN_FR.keys()))

    print("=== MISSING QUESTION TRANSLATIONS (%d) ===" % len(missing_q))
    for s in missing_q:
        print(s)
    print("\n=== MISSING OPTION TRANSLATIONS (%d) ===" % len(missing_opt))
    for s in missing_opt:
        print(s)
    print("\n=== MISSING EXPLANATION TRANSLATIONS (%d) ===" % len(missing_expl))
    for s in missing_expl:
        print(s[:80] + "..." if len(s) > 80 else s)
    # Write only text options (skip pure numbers) to a file for batch translation
    text_opts = [o for o in missing_opt if not o.replace(',','').replace('.','').replace('%','').replace(' ','').replace('-','').isdigit() and len(o) > 2]
    out_path = os.path.join(SCRIPT_DIR, 'missing_options_text.txt')
    with open(out_path, 'w', encoding='utf-8') as f:
        for o in sorted(text_opts):
            f.write(o + '\n')
    print('\n(Wrote %d text options to %s)' % (len(text_opts), out_path))

if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""
Generate citizenship_441.html with 441 questions.
فقط از فایل 2021-11-15_Citizenship 441 question.pdf استفاده می‌شود؛ هیچ استفاده‌ای از ۵۷۱ یا scripts نیست.
داده از static/citizenship_441_questions.json (خروجی extract_441_from_pdf.py) خوانده می‌شود.
Run: python extract_441_questions.py
"""
import re
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    from citizenship_441_fr_data import OPTIONS_EN_FR_EXTRA, EXPL_EN_FR_EXTRA, OPTIONS_EN_FR_MISSING
except ImportError:
    OPTIONS_EN_FR_EXTRA = {}
    EXPL_EN_FR_EXTRA = {}
    OPTIONS_EN_FR_MISSING = {}
try:
    from citizenship_441_questions_fr import QUESTIONS_EN_FR
except ImportError:
    QUESTIONS_EN_FR = {}
OUTPUT_PATH = os.path.join(SCRIPT_DIR, 'templates', 'citizenship_441.html')
PDF_ORDER_JSON = os.path.join(SCRIPT_DIR, 'static', 'citizenship_441_questions.json')

def escape_html(s):
    if not s:
        return ''
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;'))


def load_pdf_order():
    """اگر فایل ترتیب PDF وجود دارد، لیست ۴۴۱ آیتم {num, q, answer} برمی‌گرداند؛ وگرنه None."""
    if not os.path.isfile(PDF_ORDER_JSON):
        return None
    try:
        with open(PDF_ORDER_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data or len(data) < 441:
            return None
        return data[:441]
    except Exception:
        return None


def questions_from_pdf_only(pdf_order):
    """فقط از دادهٔ PDF (همان JSON خروجی extract_441_from_pdf.py) لیست ۴۴۱ سوال را می‌سازد.
    هیچ منبع دیگری (۵۷۱ یا scripts) استفاده نمی‌شود."""
    result = []
    for i, item in enumerate(pdf_order):
        if item.get("options") and isinstance(item.get("options"), list) and len(item["options"]) >= 1:
            result.append({
                "q": item.get("q") or "",
                "q_fa": item.get("q_fa") or item.get("q") or "",
                "options": item["options"],
                "correct": item.get("correct", 0),
                "book_text": item.get("book_text") or "",
            })
            continue
        n = i + 1
        q = item.get("q") or item.get("question") or ("Question %d (from PDF)" % n)
        answer = item.get("answer") or ""
        result.append({
            "q": q,
            "q_fa": q,
            "options": [answer or "See 2021-11-15_Citizenship 441 question.pdf"],
            "correct": 0,
            "book_text": item.get("book_text") or "Content from 2021-11-15_Citizenship 441 question.pdf",
        })
    return result

# Common EN -> FR for options and phrases (citizenship test)
OPTIONS_EN_FR = {
    'True': 'Vrai',
    'False': 'Faux',
    'All of the above': 'Toutes ces réponses',
    'None of the above': 'Aucune de ces réponses',
    'Both Common law and Civil law': 'Le common law et le droit civil',
    'Only federal law': 'Seulement la loi fédérale',
    'Common law': 'Common law',
    'Civil law': 'Droit civil',
    'The Great Charter of Freedoms': 'La Grande Charte des libertés',
    'A Canadian law': 'Une loi canadienne',
    'A French document': 'Un document français',
    'An American treaty': 'Un traité américain',
    'Right to challenge unlawful detention': 'Droit de contester une détention illégale',
    'Right to vote': 'Droit de vote',
    'Right to free speech': 'Liberté d\'expression',
    'Right to bear arms': 'Droit de port d\'armes',
    'Based on Discover Canada': 'Basé sur Découvrir le Canada',
    'See official study guide': 'Voir le guide d\'étude officiel',
    'Refer to PDF source': 'Consulter la source PDF',
    'See Discover Canada study guide.': 'Voir le guide d\'étude Découvrir le Canada.',
}
OPTIONS_EN_FR.update(OPTIONS_EN_FR_EXTRA)
OPTIONS_EN_FR.update(OPTIONS_EN_FR_MISSING)

# Question patterns EN -> FR
Q_PATTERNS_FR = [
    (r'What is \'', 'Qu\'est-ce que \''),
    (r'What is ', 'Qu\'est-ce que '),
    (r'When was ', 'Quand a été '),
    (r'When did ', 'Quand est-ce que '),
    (r'Name one ', 'Nommez une '),
    (r'Who proclaimed ', 'Qui a proclamé '),
    (r'What does ', 'Que comprend '),
    (r'Where did ', 'Où est-ce que '),
    (r'Which ', 'Quel '),
    (r'How many ', 'Combien de '),
    (r'In what year ', 'En quelle année '),
    (r'Who passed ', 'Qui a adopté '),
    (r'Who was ', 'Qui était '),
    (r'Who are ', 'Qui sont '),
    (r'Why is ', 'Pourquoi '),
    (r'What are ', 'Quels sont '),
    (r'Name ', 'Nommez '),
    (r'Identify ', 'Identifiez '),
    (r'True or False: ', 'Vrai ou faux : '),
]
Q_SUFFIX_FR = [
    ('source of Canadian law.', 'source de la loi canadienne.'),
    ('source of Canadian law?', 'source de la loi canadienne?'),
    ('the Great Charter of Freedom include?', 'la Grande Charte des libertés?'),
    ('two principles upon which Canada is founded?', 'deux principes sur lesquels le Canada est fondé?'),
    ('three main groups of Aboriginal peoples?', 'trois principaux groupes de peuples autochtones?'),
    ('the Métis?', 'les Métis?'),
    ('the word \'Inuit\' mean?', 'le mot « Inuit » signifie-t-il?'),
    ('two key documents that contain our rights and freedoms?', 'deux documents clés qui contiennent nos droits et libertés?'),
]

# Phrase replacements for options not in OPTIONS_EN_FR (longer phrases first)
OPTION_PHRASE_FR = [
    (" head of state", " chef d'État"), (" head of government", " chef du gouvernement"),
    (" Prime Minister", " premier ministre"), (" Governor General", " gouverneur général"),
    (" House of Commons", " Chambre des communes"), (" Supreme Court", " Cour suprême"),
    (" constitutional monarchy", " monarchie constitutionnelle"),
    (" parliamentary democracy", " démocratie parlementaire"),
    (" minority government", " gouvernement minoritaire"), (" federal government", " gouvernement fédéral"),
    (" provincial government", " gouvernement provincial"), (" election ballot", " bulletin de vote"),
    (" election day", " jour du scrutin"), (" federal elections", " élections fédérales"),
    (" capital of Canada", " capitale du Canada"), (" Atlantic Region", " région de l'Atlantique"),
    (" Central Canada", " Centre du Canada"), (" Prairie Region", " région des Prairies"),
    (" West Coast", " côte Ouest"), (" capital cities", " capitales"),
    (" in Canada", " au Canada"), (" in Parliament", " au Parlement"),
    (" the law", " la loi"), (" the courts", " les tribunaux"), (" the police", " la police"),
    (" the ", " le "), (" of ", " de "), (" and ", " et "),
]

def _is_numeric_option(s):
    """Keep numbers and year-like options as-is (same in EN/FR)."""
    s = s.strip()
    if not s:
        return True
    # Pure number or with % e.g. "60% (12 correct)"
    if s.replace(',', '').replace('.', '').replace('%', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
        return True
    # Short numeric (years, counts)
    if len(s) <= 5 and s.replace(',', '').replace('.', '').isdigit():
        return True
    return False

def translate_option_to_fr(opt):
    if not opt:
        return opt
    s = opt.strip()
    out = OPTIONS_EN_FR.get(s)
    if out is not None:
        return out
    # Numbers/years stay same in French
    if _is_numeric_option(s):
        return s
    # Fallback: replace common English phrases so option is at least partly in French
    for en, fr in OPTION_PHRASE_FR:
        s = s.replace(en, fr)
    return s

def translate_question_to_fr(q):
    if not q:
        return q
    s = q.strip()
    # Use full question dictionary first so most questions are fully in French
    if s in QUESTIONS_EN_FR:
        return QUESTIONS_EN_FR[s]
    s = q
    for en, fr in Q_PATTERNS_FR:
        if en in s:
            s = s.replace(en, fr, 1)
            break
    for en_suffix, fr_suffix in Q_SUFFIX_FR:
        if en_suffix in s:
            s = s.replace(en_suffix, fr_suffix, 1)
    return s

# Short source note (EN/FR) – follows language selection
NOTE_EN = 'According to Discover Canada.'
NOTE_FR = 'Selon Découvrir le Canada.'
NOTE_EN_GUIDE = 'See Discover Canada study guide.'
NOTE_FR_GUIDE = 'Voir le guide d\'étude Découvrir le Canada.'

# Long explanation EN -> FR (common paragraphs)
EXPL_EN_FR = {
    "The Magna Carta (Great Charter of Freedoms) was signed in 1215 in England. It included rights and freedoms that were later brought to Canada.":
        "La Grande Charte des libertés (Magna Carta) a été signée en 1215 en Angleterre. Elle incluait des droits et libertés qui ont ensuite été apportés au Canada.",
    "Canada's legal system is based on a combination of common law (which applies in all provinces except Quebec) and civil law (which applies in Quebec). Common law is one source of Canadian law.":
        "Le système juridique canadien repose sur une combinaison de common law (qui s'applique dans toutes les provinces sauf le Québec) et de droit civil (qui s'applique au Québec). Le common law est une source du droit canadien.",
    "The Magna Carta included fundamental freedoms such as freedom of conscience and religion, freedom of thought, belief, opinion and expression, and freedom of peaceful assembly and association.":
        "La Grande Charte incluait des libertés fondamentales telles que la liberté de conscience et de religion, la liberté de pensée, de croyance, d'opinion et d'expression, et la liberté de réunion et d'association pacifiques.",
    "Habeas corpus is the right to challenge unlawful detention by the state. This right comes from English common law.":
        "L'habeas corpus est le droit de contester une détention illégale par l'État. Ce droit vient du common law anglais.",
    "See Discover Canada study guide.":
        "Voir le guide d'étude Découvrir le Canada.",
    "Queen Elizabeth II proclaimed the amended Constitution of Canada in Ottawa on April 17, 1982.":
        "La reine Elizabeth II a proclamé la Constitution du Canada modifiée à Ottawa le 17 avril 1982.",
    "Canada is founded on the principles of peace, order and good government.":
        "Le Canada est fondé sur les principes de paix, d'ordre et de bon gouvernement.",
    "The Canadian Charter of Rights and Freedoms begins with the words: 'Whereas Canada is founded upon principles that recognize the supremacy of God and the rule of law...'":
        "La Charte canadienne des droits et libertés commence par les mots : « Attendu que le Canada est fondé sur des principes qui reconnaissent la suprématie de Dieu et la primauté du droit... »",
    "Mobility rights include the right to enter and leave Canada, and the right to move between provinces to live and work.":
        "Les droits à la mobilité comprennent le droit d'entrer au Canada et d'en sortir, et le droit de déménager entre les provinces pour vivre et travailler.",
    "The Charter includes mobility rights, Aboriginal rights, and official language rights.":
        "La Charte comprend les droits à la mobilité, les droits des Autochtones et les droits linguistiques officiels.",
    "French and English have equal status in Parliament and throughout the government.":
        "Le français et l'anglais ont un statut égal au Parlement et dans l'ensemble du gouvernement.",
    "Canadians work hard to respect both individual rights and collective rights.":
        "Les Canadiens s'efforcent de respecter à la fois les droits individuels et les droits collectifs.",
    "Multiculturalism and bilingualism are fundamental characteristics of the Canadian heritage and identity.":
        "Le multiculturalisme et le bilinguisme sont des caractéristiques fondamentales du patrimoine et de l'identité canadienne.",
    "Responsibilities of citizenship include obeying the law, taking responsibility for oneself and one's family, and serving on a jury when called upon.":
        "Les responsabilités de la citoyenneté comprennent respecter la loi, assumer ses responsabilités et celles de sa famille, et siéger à un jury lorsqu'on est convoqué.",
    "Serving on a jury when called to do so is a legal duty of citizenship.":
        "Siéger à un jury lorsqu'on est convoqué est un devoir juridique de la citoyenneté.",
    "There is no compulsory military service in Canada.":
        "Il n'y a pas de service militaire obligatoire au Canada.",
    "Military service is a noble way to contribute to Canada and an excellent career choice.":
        "Le service militaire est une façon noble de contribuer au Canada et un excellent choix de carrière.",
    "The Constitution and the Canadian Charter of Rights and Freedoms are two key documents that contain our rights and freedoms.":
        "La Constitution et la Charte canadienne des droits et libertés sont deux documents clés qui contiennent nos droits et libertés.",
    "Canadians enjoy mobility rights, Aboriginal rights, official language rights, and multiculturalism rights.":
        "Les Canadiens jouissent des droits à la mobilité, des droits des Autochtones, des droits linguistiques officiels et des droits du multiculturalisme.",
    "Aboriginal peoples are the first people to live in Canada. The three main groups are: First Nations, Métis, and Inuit.":
        "Les peuples autochtones sont les premiers à avoir vécu au Canada. Les trois principaux groupes sont : les Premières Nations, les Métis et les Inuits.",
    "The Métis are a distinct people of mixed Aboriginal and European ancestry.":
        "Les Métis sont un peuple distinct d'ascendance autochtone et européenne.",
    "Inuit means 'the people' in the Inuktitut language.":
        "Inuit signifie « le peuple » en langue inuktitute.",
    "Habeas corpus comes from British common law.":
        "L'habeas corpus vient du common law britannique.",
    "Confederation means the union of provinces and territories into a single country, creating a federal system.":
        "La Confédération signifie l'union des provinces et des territoires en un seul pays, créant un système fédéral.",
}
EXPL_EN_FR.update(EXPL_EN_FR_EXTRA)

# When no FR translation exists for an excerpt, show generic FR so the page stays in one language
EXPL_FR_FALLBACK = "Consultez le guide Découvrir le Canada pour plus de détails."

def translate_expl_to_fr(t):
    if not t:
        return t
    t_stripped = t.strip()
    out = EXPL_EN_FR.get(t_stripped, EXPL_EN_FR.get(t, None))
    if out is not None:
        return out
    # Placeholder or unknown: show generic FR so the page stays in one language
    if "Content for this question" in t or "PDF source" in t or "2021-11-15" in t:
        return EXPL_FR_FALLBACK
    return EXPL_FR_FALLBACK

def make_html(questions):
    # Take up to 441, pad with placeholder if needed
    target = 441
    qs = questions[:target]
    while len(qs) < target:
        n = len(qs) + 1
        qs.append({
            'q': 'Question %d — Add content from PDF source (2021-11-15_Citizenship 441 question).' % n,
            'q_fr': 'Question %d — Contenu à ajouter à partir du PDF (2021-11-15_Citizenship 441 question).' % n,
            'q_fa': 'سوال %d — محتوای این سوال را از منبع PDF (2021-11-15) اضافه کنید.' % n,
            'options': ['Based on Discover Canada', 'See official study guide', 'Refer to PDF source', 'None of the above'],
            'correct': 0,
            'book_text': 'Content for this question to be added from the PDF: 2021-11-15_Citizenship 441 question.'
        })
    
    cards = []
    for i, q in enumerate(qs, 1):
        q_en = q['q']
        q_fr = q.get('q_fr') or translate_question_to_fr(q_en)
        opts_en = q['options']
        opts_fr = [translate_option_to_fr(o) for o in opts_en]
        correct_idx = q['correct']
        correct_opt_en = opts_en[correct_idx] if opts_en else ''
        correct_opt_fr = opts_fr[correct_idx] if opts_fr else ''
        expl_en = q.get('book_text') or 'See Discover Canada study guide.'
        expl_fr = translate_expl_to_fr(expl_en)
        # Short note (EN/FR) – follows language selection
        is_guide_only = (expl_en or '').strip() == 'See Discover Canada study guide.'
        note_en = NOTE_EN_GUIDE if is_guide_only else NOTE_EN
        note_fr = NOTE_FR_GUIDE if is_guide_only else NOTE_FR

        # JSON for options (escape for HTML attr)
        opts_en_json = json.dumps(opts_en, ensure_ascii=False)
        opts_fr_json = json.dumps(opts_fr, ensure_ascii=False)

        # Answer line: "B. Within 4 years..." (letter + option text)
        letter = chr(65 + correct_idx) if 0 <= correct_idx < 26 else ''
        answer_display = ('%s. ' % letter + correct_opt_en) if letter else correct_opt_en

        # Structure per reference: 1. Number (orange) 2. Question (bold) 3. Answer (orange) 4. Discover Canada (blue + icon) 5. Explanation (italic)
        cards.append('''        <div class="q-card q-card-441" id="q%d" data-en-q="%s" data-fr-q="%s" data-en-options="%s" data-fr-options="%s" data-en-answer="%s" data-fr-answer="%s" data-en-expl="%s" data-fr-expl="%s" data-en-note="%s" data-fr-note="%s" data-correct="%d">
            <div class="q-head-441">
                <span class="q-num-441">%d.</span>
                <span class="q-text-441">%s</span>
            </div>
            <div class="q-answer-441">%s</div>
            <div class="q-source-441"><span class="q-source-icon" aria-hidden="true">📖</span> <span class="q-source-text">Discover Canada</span></div>
            <div class="q-expl-441">%s</div>
        </div>''' % (
            i,
            escape_html(q_en).replace('"', '&quot;'),
            escape_html(q_fr).replace('"', '&quot;'),
            escape_html(opts_en_json).replace('"', '&quot;'),
            escape_html(opts_fr_json).replace('"', '&quot;'),
            escape_html(correct_opt_en).replace('"', '&quot;'),
            escape_html(correct_opt_fr).replace('"', '&quot;'),
            escape_html(expl_en).replace('"', '&quot;'),
            escape_html(expl_fr).replace('"', '&quot;'),
            escape_html(note_en).replace('"', '&quot;'),
            escape_html(note_fr).replace('"', '&quot;'),
            correct_idx,
            i,
            escape_html(q_en),
            escape_html(answer_display),
            escape_html(expl_en)
        ))

    return '\n'.join(cards)


def replace_cards_in_file(html_content, new_cards, second_header_start=None):
    """Replace only the q-cards section in the existing HTML; keep head, toolbar, footer."""
    section_pos = html_content.find('section-title')
    if section_pos == -1:
        return None
    start_idx = html_content.find('        <div class="q-card"', section_pos)
    if start_idx == -1:
        return None
    q441_pos = html_content.find('id="q441"', start_idx)
    if q441_pos == -1:
        return None
    if second_header_start is not None and second_header_start > q441_pos:
        ph_abs = second_header_start
    else:
        ph_abs = html_content.find('        <div class="page-header" style=', q441_pos + 1)
        if ph_abs == -1:
            ph_abs = html_content.find('        <div class="page-header"', q441_pos + 1)
    if ph_abs == -1:
        return None
    return html_content[:start_idx] + new_cards + '\n' + html_content[ph_abs:]


if __name__ == '__main__':
    pdf_order = load_pdf_order()
    if pdf_order:
        questions = questions_from_pdf_only(pdf_order)
        print('441 section: using only 2021-11-15_Citizenship 441 question.pdf (%d questions)' % len(questions))
    else:
        placeholder = [{"num": n, "q": "Question %d (from PDF)" % n, "answer": ""} for n in range(1, 442)]
        questions = questions_from_pdf_only(placeholder)
        print('No PDF JSON; using placeholders. Run: python extract_441_from_pdf.py (then this script again)')
    new_cards = make_html(questions)
    abspath = os.path.abspath(OUTPUT_PATH)
    with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
        current = f.read()
    ph_after = current.find('        <div class="page-header" style=', current.find('id="q441"') + 1)
    updated = replace_cards_in_file(current, new_cards, second_header_start=ph_after if ph_after != -1 else None)
    if updated is None:
        q1 = current.find('id="q1"')
        q441 = current.find('id="q441"')
        ph = current.find('        <div class="page-header"')
        print('Could not find cards block. len=%s q1=%s q441=%s ph=%s ph_after=%s path=%s' % (len(current), q1, q441, ph, ph_after, abspath))
        raise SystemExit(1)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(updated)
    print('Written cards to', OUTPUT_PATH)

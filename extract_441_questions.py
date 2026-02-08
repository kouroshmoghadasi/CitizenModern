# -*- coding: utf-8 -*-
"""
Extract all unique questions from scripts.html and generate citizenship_441.html with 441 questions.
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
SCRIPTS_PATH = os.path.join(SCRIPT_DIR, 'templates', 'scripts.html')
OUTPUT_PATH = os.path.join(SCRIPT_DIR, 'templates', 'citizenship_441.html')

def extract_questions():
    with open(SCRIPTS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the allTests array: from "const allTests = [" to matching "];"
    start = content.find('const allTests = [')
    if start == -1:
        return []
    start += len('const allTests = [')
    depth = 1
    i = start
    while i < len(content) and depth > 0:
        if content[i:i+1] == '[':
            depth += 1
        elif content[i:i+1] == ']':
            depth -= 1
        i += 1
    arr_content = content[start:i-1]
    
    # Extract each "questions: [" ... "]" block
    questions = []
    pattern = r'questions:\s*\[(.*?)\]\s*}\s*(?:,|$)'
    blocks = re.findall(pattern, arr_content, re.DOTALL)
    
    for block in blocks:
        # Extract each { q: "...", q_fa: "...", options: [...], correct: N, ... }
        q_pattern = r'\{\s*q:\s*"((?:[^"\\]|\\.)*)"\s*,\s*q_fa:\s*"((?:[^"\\]|\\.)*)"\s*,\s*options:\s*\[(.*?)\]\s*,\s*correct:\s*(\d+)(?:\s*,\s*page:\s*(\d+))?(?:\s*,\s*section:\s*"([^"]*)")?(?:\s*,\s*book_text:\s*"((?:[^"\\]|\\.)*)")?\s*\}'
        for m in re.finditer(q_pattern, block, re.DOTALL):
            q_en = m.group(1).replace('\\"', '"')
            q_fa = m.group(2).replace('\\"', '"')
            opts_str = m.group(3)
            correct = int(m.group(4))
            page = m.group(5) or ''
            section = m.group(6) or ''
            book_text = (m.group(7) or '').replace('\\"', '"')
            # Parse options array
            opts = re.findall(r'"((?:[^"\\]|\\.)*)"', opts_str)
            questions.append({
                'q': q_en,
                'q_fa': q_fa,
                'options': opts,
                'correct': correct,
                'page': page,
                'section': section,
                'book_text': book_text
            })
    
    # Also catch questions without q_fa (simplified pattern)
    alt_pattern = r'\{\s*q:\s*"((?:[^"\\]|\\.)*)"\s*,\s*q_fa:\s*"((?:[^"\\]|\\.)*)"\s*,\s*options:\s*\[(.*?)\]\s*,\s*correct:\s*(\d+).*?book_text:\s*"((?:[^"\\]|\\.)*)"\s*\}'
    
    # Deduplicate by q (English text), preserve order
    seen = set()
    unique = []
    for q in questions:
        key = q['q'].strip()
        if key not in seen:
            seen.add(key)
            unique.append(q)
    
    return unique

def escape_html(s):
    if not s:
        return ''
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;'))

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

        # Initial visible content = English
        opts_html = []
        for j, opt in enumerate(opts_en):
            cls = ' class="correct"' if j == correct_idx else ''
            opt_esc = escape_html(opt)
            if j == correct_idx:
                opt_esc += ' ✓'
            opts_html.append('<li%s>%s</li>' % (cls, opt_esc))

        cards.append('''        <div class="q-card" id="q%d" data-en-q="%s" data-fr-q="%s" data-en-options="%s" data-fr-options="%s" data-en-answer="%s" data-fr-answer="%s" data-en-expl="%s" data-fr-expl="%s" data-en-note="%s" data-fr-note="%s" data-correct="%d">
            <div class="q-num">سوال %d / Question %d</div>
            <div class="q-text-fa">%s</div>
            <div class="q-text-src">%s</div>
            <ul class="q-options">%s</ul>
            <div class="ans-label">پاسخ صحیح / Correct answer:</div>
            <div class="answer-src">%s</div>
            <div class="expl-note-src">%s</div>
            <div class="expl-src">%s</div>
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
            i, i,
            escape_html(q['q_fa']),
            escape_html(q_en),
            ''.join(opts_html),
            escape_html(correct_opt_en),
            escape_html(note_en),
            escape_html(expl_en)
        ))

    return '\n'.join(cards)


def replace_cards_in_file(html_content, new_cards):
    """Replace only the q-cards section in the existing HTML; keep head, toolbar, footer."""
    start_marker = '        <div class="q-card" id="q1"'
    start_idx = html_content.find(start_marker)
    if start_idx == -1:
        return None
    q441_pos = html_content.find('id="q441"', start_idx)
    if q441_pos == -1:
        return None
    end_marker = '        </div>\n        <div class="page-header"'
    end_idx = html_content.find(end_marker, q441_pos)
    if end_idx == -1:
        return None
    end_block = end_idx + len('        </div>')
    return html_content[:start_idx] + new_cards + html_content[end_block:]


if __name__ == '__main__':
    questions = extract_questions()
    print('Extracted %d unique questions' % len(questions))
    new_cards = make_html(questions)
    with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
        current = f.read()
    updated = replace_cards_in_file(current, new_cards)
    if updated is None:
        print('Could not find cards block; writing full file not supported in this script.')
        raise SystemExit(1)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(updated)
    print('Written cards to', OUTPUT_PATH)

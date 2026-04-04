# -*- coding: utf-8 -*-
"""
قرارداد ترتیب سوالات ۵۷۱ در سایت:

  شمارهٔ سوالی که کاربر می‌بیند = (ایندکس در آرایهٔ JSON) + 1

  این باید با شمارهٔ فایل تصویر شما یکسان باشد، مثلاً:
  images_1 / Question 01 → اولین آبجکت در `citizenship_571_questions.json`
  images_2 → دومی، و همین‌طور تا images_N.

هیچ وقت برای «پر کردن لیست» سوالات را از chapter1 یا منبع دیگر به انتها
نچسبانید مگر دقیقاً همان ترتیب فایل‌ها را حفظ کنید؛ وگرنه شماره با نام فایل می‌خورد.

خروجی اسکریپت فقط وقتی نوشته می‌شود که طول USER_ITEMS دقیقاً برابر
متغیر محیطی CITIZEN_571_COUNT باشد (پیش‌فرض ۵۰). وگرنه فقط هشدار می‌دهد
و فایل JSON را دست نمی‌زند — می‌توانید مستقیم همان JSON را ویرایش کنید.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "citizenship_571_questions.json"

SECTION = "Citizenship practice (50-item set)"

USER_ITEMS = [
    {
        "q": "Who are regulated by the Laws in Canada?",
        "q_fa": "چه کسانی در کانادا توسط قوانین تنظیم می‌شوند؟",
        "options": ["Individuals", "Governments", "Both A & B", "None of Them"],
        "correct": 2,
        "book_text": "One of Canada's founding principles is the rule of law. Individuals and governments are regulated by Canada's laws.",
        "q_fr": "Qui est régi par les lois au Canada ?",
        "options_fr": [
            "Les particuliers",
            "Les gouvernements",
            "À la fois A et B",
            "Aucun de ceux-ci",
        ],
        "expl_fr": "La primauté du droit : les particuliers et les gouvernements sont régis par le droit canadien.",
    },
    {
        "q": "Together with Canadian law that was inherited from the past, Canada also has an 800 years old tradition of ordered liberty, which dates back to the signing of",
        "q_fa": "همراه با حقوق کانادا که از گذشته به ارث رسیده، کانادا همچنین سنت هشتصدسالهٔ «آزادی نظم‌مند» (ordered liberty) دارد که به امضای کدام سند برمی‌گردد؟",
        "options": ["Magna Carta", "Fleur-de-lys", "Charter of Independence", "There was no Signing"],
        "correct": 0,
        "book_text": "Canadian law has several sources; the tradition of ordered liberty is tied to Magna Carta among other historic roots.",
        "q_fr": "Outre le droit canadien hérité du passé, le Canada possède une tradition de liberté ordonnée vieille de 800 ans, remontant à la signature de",
        "options_fr": ["la Magna Carta", "la fleur de lys", "la Charte d’indépendance", "Il n’y a pas eu de signature"],
        "expl_fr": "La liberté ordonnée renvoie notamment à la Magna Carta.",
    },
    {
        "q": "Which one of the following is not a source of the Law present in Canada?",
        "q_fa": "کدام مورد زیر منبع قانون در کانادا نیست؟",
        "options": ["French Civil Code", "Law Passed by Parliament", "US Federal Law", "English Common Law"],
        "correct": 2,
        "book_text": "Canadian law draws on Parliament, provinces, English common law, French civil tradition and the Constitution — not U.S. federal law.",
        "q_fr": "Lequel des éléments suivants n’est pas une source du droit au Canada ?",
        "options_fr": [
            "Le code civil français",
            "Les lois adoptées par le Parlement",
            "Le droit fédéral des États-Unis",
            "La common law anglaise",
        ],
        "expl_fr": "Le droit fédéral américain n’est pas une source du droit canadien.",
    },
    {
        "q": "The Constitution of Canada was amended in which year ?",
        "q_fa": "قانون اساسی کانادا در کدام سال اصلاح شد؟",
        "options": ["1982", "1997", "1947", "1980"],
        "correct": 0,
        "book_text": "The Constitution of Canada was amended in 1982.",
        "q_fr": "La Constitution du Canada a été modifiée en quelle année ?",
        "options_fr": ["1982", "1997", "1947", "1980"],
        "expl_fr": "La Constitution du Canada a été modifiée en 1982.",
    },
    {
        "q": "“Whereas Canada is founded upon principles that recognize the supremacy of God and the Rule of Law”. This phrase underlines the importance of",
        "q_fa": "«چون کانادا بر اصولی بنا شده که برتری خدا و حاکمیت قانون را به رسمیت می‌شناسد». این عبارت بر اهمیت چه چیزی تأکید دارد؟",
        "options": [
            "Religious Tradition",
            "Dignity and Worth of Human Person",
            "Both A & B",
            "None of These",
        ],
        "correct": 2,
        "book_text": "This phrase indicates the importance of religious and moral traditions as well as the rule of law in Canadian society.",
        "q_fr": "« Attendu que le Canada est fondé sur des principes qui reconnaissent la suprématie de Dieu et la primauté du droit ». Cette formule souligne l’importance de",
        "options_fr": [
            "La tradition religieuse",
            "La dignité et la valeur de la personne humaine",
            "À la fois A et B",
            "Aucune de ces réponses",
        ],
        "expl_fr": "Traditions religieuses et morales ainsi que la primauté du droit.",
    },
    {
        "q": "How old is the tradition of ordered liberty that Canada contains?",
        "q_fa": "سنت «آزادی نظم‌مند» (ordered liberty) که کانادا دارد، چند سال قدمت دارد؟",
        "options": ["1000", "800", "700", "900"],
        "correct": 1,
        "book_text": "Canada contains an 800 years old tradition of ordered liberty, which dates back to the signing of Magna Carta.",
        "q_fr": "Quel âge a la tradition de liberté ordonnée que compte le Canada ?",
        "options_fr": ["1000", "800", "700", "900"],
        "expl_fr": "Le Canada compte une tradition de liberté ordonnée vieille de 800 ans, remontant à la signature de la Magna Carta.",
    },
    {
        "q": "What are the two principles upon which Canada is founded?",
        "q_fa": "دو اصلی که کانادا بر آن‌ها بنیان نهاده شده چیست؟",
        "options": [
            "The supremacy of God and freedom of speech",
            "The supremacy of God and the rule of law",
            "Mobility right and the rule of law",
            "The supremacy of law and the rule of God",
        ],
        "correct": 1,
        "book_text": "Canada is founded on principles that recognize the supremacy of God and the rule of law.",
        "q_fr": "Quels sont les deux principes sur lesquels le Canada est fondé?",
        "options_fr": [
            "La suprématie de Dieu et la liberté d'expression",
            "La suprématie de Dieu et la primauté du droit",
            "Droit à la mobilité et primauté du droit",
            "Suprématie de la loi et règle de Dieu",
        ],
        "expl_fr": "Le Canada reconnaît la suprématie de Dieu et la primauté du droit.",
    },
    {
        "q": "Through Habeas Corpus, a person can challenge unlawful detention by the state. It is derived from which Law?",
        "q_fa": "از طریق Habeas Corpus فرد می‌تواند بازداشت غیرقانونی توسط دولت را به چالش بکشد. این حق برگرفته از کدام نظام حقوقی است؟",
        "options": ["German Common Law", "English Common Law", "French Common Law", "Italian Common Law"],
        "correct": 1,
        "book_text": "Habeas corpus comes from English common law.",
        "q_fr": "Par l’habeas corpus, une personne peut contester une détention illégale par l’État. Cela tire son origine de quel droit ?",
        "options_fr": [
            "La common law allemande",
            "La common law anglaise",
            "La common law française",
            "La common law italienne",
        ],
        "expl_fr": "L’habeas corpus vient de la common law anglaise.",
    },
    {
        "q": "The Canadian system of Government is based on",
        "q_fa": "نظام حکومت کانادا بر چه اساسی استوار است؟",
        "options": ["Population Rule", "Constitutional Monarchy", "Benign Dictatorship", "Republican Democracy"],
        "correct": 1,
        "book_text": "Canada is a constitutional monarchy.",
        "q_fr": "Le système de gouvernement du Canada repose sur",
        "options_fr": [
            "La règle de la population",
            "La monarchie constitutionnelle",
            "La dictature bienveillante",
            "La démocratie républicaine",
        ],
        "expl_fr": "Le Canada est une monarchie constitutionnelle.",
    },
    {
        "q": "Territorial rights were first guaranteed through the Royal Proclamation of 1763 by",
        "q_fa": "حقوق قلمرویی نخست از طریق فرمان سلطنتی ۱۷۶۳ توسط چه کسی تضمین شد؟",
        "options": ["King George II", "St. Patrick", "King George III", "Acadians"],
        "correct": 2,
        "book_text": "The Royal Proclamation of 1763 was issued under King George III.",
        "q_fr": "Les droits territoriaux ont d’abord été garantis par la Proclamation royale de 1763 sous",
        "options_fr": ["George II", "Saint Patrick", "George III", "Les Acadiens"],
        "expl_fr": "La proclamation est associée à George III.",
    },
    {
        "q": "Most of the Metis people live in",
        "q_fa": "اکثر مردم میتیس در کجا زندگی می‌کنند؟",
        "options": ["Prairie province", "Northern territories", "Ontario", "Quebec"],
        "correct": 0,
        "book_text": "The majority of Métis live in the Prairie provinces.",
        "q_fr": "La majorité des Métis vivent",
        "options_fr": [
            "Dans les provinces des Prairies",
            "Dans les territoires du Nord",
            "En Ontario",
            "Au Québec",
        ],
        "expl_fr": "Ils sont surtout dans les Prairies.",
    },
    {
        "q": "Canadian Citizens who are neither Inuit nor Metis are known as",
        "q_fa": "شهروندان کانادایی که نه اینوت و نه میتیس هستند، چه نامیده می‌شوند؟",
        "options": ["First Nation", "Second Nation", "Quebecers", "Ontarians"],
        "correct": 0,
        "book_text": "They are known as First Nations.",
        "q_fr": "Les citoyens canadiens qui ne sont ni Inuits ni Métis sont appelés",
        "options_fr": ["Premières Nations", "Deuxième Nation", "Québécois", "Ontariens"],
        "expl_fr": "On dit les Premières Nations.",
    },
    {
        "q": "What is the meaning of the word “Inuit” in the Inuktitut language?",
        "q_fa": "کلمهٔ «Inuit» به زبان اینوکتیتوت یعنی چه؟",
        "options": ["The People", "The Farmers", "The Conquerors", "The Invaders"],
        "correct": 0,
        "book_text": "Inuit means “the people” in Inuktitut.",
        "q_fr": "Que signifie le mot « Inuit » en inuktitut ?",
        "options_fr": ["Le peuple", "Les agriculteurs", "Les conquérants", "Les envahisseurs"],
        "expl_fr": "Cela signifie « le peuple ».",
    },
    {
        "q": "Until which date did the Federal Government force Aboriginal Students to assimilate them into mainstream Canadian Culture?",
        "q_fa": "دولت فدرال تا چه تاریخی دانش‌آموزان بومی را برای همسان‌سازی با فرهنگ اصلی کانادا مجبور می‌کرد؟",
        "options": ["1970", "1980", "1990", "2000"],
        "correct": 1,
        "book_text": "Federal policy including residential schools aimed at assimilation extended into the 1980s.",
        "q_fr": "Jusqu’à quelle décennie le gouvernement fédéral a-t-il contraint de nombreux élèves autochtones à l’assimilation ?",
        "options_fr": ["1970", "1980", "1990", "2000"],
        "expl_fr": "Les pensionnats et politiques d’assimilation se sont prolongés jusqu’aux années 1980.",
    },
    {
        "q": "Thousands of years ago, where did the ancestors of Aboriginal peoples migrated from?",
        "q_fa": "هزاران سال پیش نیاکان مردمان بومی کانادا از کجا کوچ کرده‌اند؟",
        "options": ["Africa", "Asia", "Korea", "India"],
        "correct": 1,
        "book_text": "Ancestors of Indigenous peoples are believed to have come from Asia thousands of years ago.",
        "q_fr": "Il y a des milliers d’années, d’où les ancêtres des peuples autochtones sont-ils venus ?",
        "options_fr": ["Afrique", "Asie", "Corée", "Inde"],
        "expl_fr": "On estime qu’ils sont venus d’Asie.",
    },
    {
        "q": "Inuit people live across the",
        "q_fa": "مردم اینوک در کدام ناحیه پراکنده‌اند؟",
        "options": ["Arctic", "Prairie", "North", "South"],
        "correct": 0,
        "book_text": "Inuit communities are spread across the Arctic.",
        "q_fr": "Les Inuits vivent à travers",
        "options_fr": ["l’Arctique", "les Prairies", "le Nord", "le Sud"],
        "expl_fr": "Ils habitent l’Arctique.",
    },
    {
        "q": "“Should retain their individuality and each make its contribution to the national character”. This was said by",
        "q_fa": "«باید هویت خود را حفظ کنند و هر کدام سهم خود را در شخصیت ملی ایفا کنند». این سخن از زبان چه کسی است؟",
        "options": ["John Buchan", "St. Patrick", "King George III", "None of these"],
        "correct": 0,
        "book_text": "Governor General John Buchan (Lord Tweedsmuir) spoke of retaining individuality while contributing to the national character.",
        "q_fr": "« Devraient conserver leur individualité et contribuer au caractère national ». Qui a dit cela ?",
        "options_fr": ["John Buchan", "Saint Patrick", "George III", "Aucune de ces réponses"],
        "expl_fr": "John Buchan (Tweedsmuir).",
    },
    {
        "q": "In which year did Ottawa formally apologize for its treatment of Aboriginal students?",
        "q_fa": "در چه سالی اتاوا به‌طور رسمی بابت رفتار با دانش‌آموزان بومی عذرخواهی کرد؟",
        "options": ["1978", "2008", "1988", "1958"],
        "correct": 1,
        "book_text": "In 2008 the Government of Canada apologized for the residential schools policy.",
        "q_fr": "En quelle année Ottawa a-t-elle présenté des excuses officielles concernant les anciens élèves autochtones ?",
        "options_fr": ["1978", "2008", "1988", "1958"],
        "expl_fr": "Les excuses officielles datent de 2008.",
    },
    {
        "q": "How many groups of people make up the Aboriginals?",
        "q_fa": "چند گروه مردم بومی (Aboriginal) وجود دارد؟",
        "options": ["Two", "Three", "Four", "Five"],
        "correct": 1,
        "book_text": "There are three groups: First Nations, Inuit, and Métis.",
        "q_fr": "Combien de groupes distincts constituent les peuples autochtones ?",
        "options_fr": ["Deux", "Trois", "Quatre", "Cinq"],
        "expl_fr": "Trois : Premières Nations, Inuits, Métis.",
    },
    {
        "q": "The Métis are distinct people of mixed aboriginal and European ancestry. They came from",
        "q_fa": "میتیس مردمانی متمایز با تبار ترکیبی بومی و اروپایی‌اند. آن‌ها از کجا آمده‌اند؟",
        "options": [
            "Both French and English Speaking background",
            "East Asia",
            "Green Land",
            "Newfoundland",
        ],
        "correct": 0,
        "book_text": "Métis heritage includes both French- and English-speaking roots.",
        "q_fr": "Les Métis, peuple distinct d’ascendance mixte, viennent de",
        "options_fr": [
            "Des milieux francophones et anglophones",
            "Asie de l’Est",
            "Groenland",
            "Terre-Neuve",
        ],
        "expl_fr": "Ils descendent de milieux français et anglais.",
    },
]


def main():
    expected = int(os.environ.get("CITIZEN_571_COUNT", "50"))
    n = len(USER_ITEMS)
    if n != expected:
        print(
            f"[citizen 571] USER_ITEMS length is {n}, expected {expected} (set CITIZEN_571_COUNT to match). "
            "Not writing — edit static/citizenship_571_questions.json directly to keep images_N ↔ question N order."
        )
        return
    out_list = []
    for u in USER_ITEMS:
        row = dict(u)
        row["page"] = 0
        row["section"] = SECTION
        if not row.get("expl_fr") and row.get("book_text"):
            row["expl_fr"] = row["book_text"]
        out_list.append(row)
    OUT.write_text(json.dumps(out_list, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", len(out_list), "questions to", OUT, "(indices 0..N-1 → site question 1..N = your file numbers)")


if __name__ == "__main__":
    main()

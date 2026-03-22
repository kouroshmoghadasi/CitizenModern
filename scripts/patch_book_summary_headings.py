# One-off: split FA / EN titles into FA + EN + FR spans for book_summary.html
import pathlib

path = pathlib.Path(__file__).resolve().parents[1] / "templates" / "book_summary.html"
text = path.read_text(encoding="utf-8")


def wrap_section(fa: str, en: str, fr: str) -> str:
    stack = (
        f'<span class="summary-title-stack"><span class="summary-heading-fa">{fa}</span>'
        f'<span class="summary-heading-en">{en}</span>'
        f'<span class="summary-heading-fr">{fr}</span></span>'
    )
    return f'                <div class="summary-section-title">{stack}</div>'


def wrap_subsection(fa: str, en: str, fr: str) -> str:
    stack = (
        f'<span class="summary-title-stack"><span class="summary-heading-fa">{fa}</span>'
        f'<span class="summary-heading-en">{en}</span>'
        f'<span class="summary-heading-fr">{fr}</span></span>'
    )
    return f'                    <div class="summary-subsection-title">{stack}</div>'


sections = [
    ("مقدمه", "Introduction", "Introduction"),
    ("حقوق و آزادی‌ها", "Rights and Freedoms", "Droits et libertés"),
    ("تاریخ کانادا", "Canadian History", "Histoire du Canada"),
    ("دولت و حکومت", "Government", "Gouvernement"),
    ("جغرافیا", "Geography", "Géographie"),
    ("اقتصاد", "Economy", "Économie"),
    ("فرهنگ", "Culture", "Culture"),
    ("شهروندی", "Citizenship", "Citoyenneté"),
    ("قهرمانان و اشخاص مهم", "Important Figures and Heroes", "Personnages et héros importants"),
    ("قراردادها و معاهدات بین‌المللی", "International Agreements and Treaties", "Accords et traités internationaux"),
    ("اطلاعات تکمیلی مهم", "Additional Important Information", "Renseignements importants supplémentaires"),
    ("اطلاعات منطقه‌ای", "Regional Information", "Renseignements régionaux"),
    ("تاریخ‌ها و اعداد مهم", "Key Dates and Numbers", "Dates et chiffres clés"),
    ("مفاهیم و اصطلاحات مهم", "Important Concepts and Terms", "Concepts et termes importants"),
    ("نکات مطالعاتی و اطلاعات آزمون", "Study Tips and Exam Information", "Conseils d'étude et renseignements sur l'examen"),
]

subsections = [
    ("سوگند شهروندی و نقش پادشاه", "Oath of Citizenship and the Sovereign", "Serment de citoyenneté et le souverain"),
    ("شکل حکومت کانادا", "Canada's system of government", "Régime politique du Canada"),
    ("درخواست شهروندی، آزمون و مراسم", "Application, test, and ceremony", "Demande, test et cérémonie"),
    ("منشور حقوق و آزادی‌ها", "Charter of Rights and Freedoms", "Charte des droits et libertés"),
    ("مردم بومی", "Aboriginal Peoples", "Peuples autochtones"),
    ("استعمار اروپا", "European Colonization", "Colonisation européenne"),
    ("کنفدراسیون", "Confederation", "Confédération"),
    ("جنگ‌های جهانی", "World Wars", "Guerres mondiales"),
    ("تاریخ معاصر", "Modern History", "Histoire moderne"),
    ("سیستم فدرال", "Federal System", "Système fédéral"),
    ("رئیس دولت", "Head of State", "Chef de l'État"),
    ("نخست‌وزیر و کابینه", "Prime Minister and Cabinet", "Premier ministre et Cabinet"),
    ("پارلمان", "Parliament", "Parlement"),
    ("استان‌ها و قلمروها", "Provinces and Territories", "Provinces et territoires"),
    ("موقعیت و اندازه", "Location and Size", "Situation et superficie"),
    ("شهرهای مهم", "Major Cities", "Principales villes"),
    ("منابع طبیعی", "Natural Resources", "Ressources naturelles"),
    ("پایتخت‌های استان‌ها", "Provincial Capitals", "Capitales provinciales"),
    ("سیستم اقتصادی", "Economic System", "Système économique"),
    ("صنایع اصلی", "Major Industries", "Principales industries"),
    ("تجارت", "Trade", "Commerce"),
    ("زبان‌ها", "Languages", "Langues"),
    ("نمادهای ملی", "National Symbols", "Symboles nationaux"),
    ("تعطیلات ملی", "National Holidays", "Jours fériés nationaux"),
    ("ورزش", "Sports", "Sports"),
    ("چندفرهنگی", "Multiculturalism", "Multiculturalisme"),
    ("حقوق شهروندی", "Citizenship Rights", "Droits liés à la citoyenneté"),
    ("مسئولیت‌های شهروندی", "Citizenship Responsibilities", "Responsabilités liées à la citoyenneté"),
    ("رهبران سیاسی", "Political Leaders", "Dirigeants politiques"),
    ("قهرمانان نظامی", "Military Heroes", "Héros militaires"),
    ("مکتشفان و پیشگامان", "Explorers and Pioneers", "Explorateurs et pionniers"),
    ("قهرمانان حقوق مدنی", "Civil Rights Heroes", "Défenseurs des droits civils"),
    ("هنرمندان و نویسندگان", "Artists and Writers", "Artistes et écrivains"),
    ("موافقتنامه‌های تجاری", "Trade Agreements", "Accords commerciaux"),
    ("سازمان‌های بین‌المللی", "International Organizations", "Organisations internationales"),
    ("معاهدات تاریخی", "Historical Treaties", "Traités historiques"),
    ("موافقتنامه‌های مرزی", "Border Agreements", "Accords frontaliers"),
    ("قوانین و مقررات مهم", "Important Laws and Regulations", "Lois et règlements importants"),
    ("نهادهای مهم", "Important Institutions", "Institutions importantes"),
    ("رویدادهای تاریخی مهم", "Important Historical Events", "Événements historiques importants"),
    ("دستاوردهای علمی و فناوری", "Scientific and Technological Achievements", "Réalisations scientifiques et technologiques"),
    ("میراث فرهنگی", "Cultural Heritage", "Patrimoine culturel"),
    ("استان‌ها و ویژگی‌های آنها", "Provinces and Their Features", "Provinces et leurs caractéristiques"),
    ("قلمروها", "Territories", "Territoires"),
    ("تاریخ‌های مهم", "Important Dates", "Dates importantes"),
    ("اعداد و آمار مهم", "Important Numbers and Statistics", "Chiffres et statistiques importants"),
    ("مفاهیم سیاسی", "Political Concepts", "Concepts politiques"),
    ("اصطلاحات قانونی", "Legal Terms", "Termes juridiques"),
    ("مفاهیم فرهنگی و اجتماعی", "Cultural and Social Concepts", "Concepts culturels et sociaux"),
    ("اطلاعات آزمون شهروندی", "Citizenship Test Information", "Renseignements sur le test de citoyenneté"),
    ("نکات مطالعاتی", "Study Tips", "Conseils d'étude"),
]

for fa, en, fr in sections:
    old = f'                <div class="summary-section-title">{fa} / {en}</div>'
    new = wrap_section(fa, en, fr)
    if old not in text:
        raise SystemExit(f"Section not found:\n{old}")
    text = text.replace(old, new, 1)

for fa, en, fr in subsections:
    old = f'                    <div class="summary-subsection-title">{fa} / {en}</div>'
    new = wrap_subsection(fa, en, fr)
    if old not in text:
        raise SystemExit(f"Subsection not found:\n{old}")
    text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print("patched", len(sections), "sections,", len(subsections), "subsections")

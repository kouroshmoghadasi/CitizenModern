"""Build govern_options_fa_patch.json: English option -> Persian from 414/571 maps + exact 414 row alignment."""
import json
import os

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")


def build_en_to_fa_414_first():
    en_to_fa = {}
    with open(os.path.join(BASE, "citizenship_414_questions.json"), encoding="utf-8") as f:
        r414 = json.load(f)
    for q in r414:
        en_list = q.get("options_en") or []
        fa_list = q.get("options_fa") or []
        for j, en in enumerate(en_list):
            if j < len(fa_list) and en and fa_list[j]:
                en_to_fa[en.strip()] = fa_list[j].strip()
    for name in (
        "571_options_fa.json",
        "571_options_fa_extra.json",
        "571_options_fa_complete.json",
        "571_options_fa_q9.json",
        "chapter3_options_fa.json",
        "chapter4_options_fa.json",
    ):
        path = os.path.join(BASE, name)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            extra = json.load(f)
        if isinstance(extra, dict):
            for k, v in extra.items():
                if k and isinstance(k, str) and not k.strip().startswith("_") and v:
                    en_to_fa[k.strip()] = v.strip()
    # aliases
    for k in list(en_to_fa.keys()):
        low = k.lower()
        if low not in en_to_fa:
            en_to_fa[low] = en_to_fa[k]
        kn = k.replace("\u2019", "'")
        if kn and kn not in en_to_fa:
            en_to_fa[kn] = en_to_fa[k]
    return en_to_fa


def fa_lookup(en_to_fa, text):
    t = text.strip() if text else ""
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
    with open(os.path.join(BASE, "govern_questions.json"), encoding="utf-8") as f:
        govern = json.load(f)
    en_to_fa = build_en_to_fa_414_first()
    patch = {}
    missing = []
    for q in govern:
        for opt in q.get("options") or []:
            o = opt.strip()
            if not o or o in patch:
                continue
            tr = fa_lookup(en_to_fa, o)
            if tr == o:
                missing.append(o)
            else:
                patch[o] = tr
    # curated common gaps (Discover Canada / govern section)
    curated = {
        "All of the above": "همه موارد بالا",
        "All of them": "همه آن‌ها",
        "None of the above": "هیچ‌کدام از موارد بالا",
        "True": "درست",
        "False": "نادرست",
        "Federal": "فدرال",
        "Provincial": "استانی",
        "Municipal": "شهرداری (محلی)",
        "Executive, Legislative, Judicial": "اجرایی، قانون‌گذاری، قضایی",
        "Federal, Provincial, Municipal": "فدرال، استانی، شهرداری",
        "House, Senate, Courts": "مجلس عوام، سنا، دادگاه‌ها",
        "Prime Minister, Premier, Mayor": "نخست‌وزیر، نخست‌وزیر استانی، شهردار",
        "National defence, foreign policy, citizenship": "دفاع ملی، سیاست خارجی، شهروندی",
        "Education, health care, natural resources": "آموزش، بهداشت، منابع طبیعی",
        "Police, fire services, libraries": "پلیس، آتش‌نشانی، کتابخانه‌ها",
        "National defence, citizenship": "دفاع ملی، شهروندی",
        "Police, fire services": "پلیس، آتش‌نشانی",
        "Postal service": "پست",
        "Federalism, Parliamentary democracy, Constitutional monarchy": "فدرالیسم، دموکراسی پارلمانی، پادشاهی مشروطه",
        "Democracy, Republic, Federalism": "دموکراسی، جمهوری، فدرالیسم",
        "Monarchy, Dictatorship, Federalism": "پادشاهی، دیکتاتوری، فدرالیسم",
        "Governor General": "فرماندار کل",
        "Lieutenant Governor": "معاون فرماندار",
        "Premier": "نخست‌وزیر استانی",
        "Mayor": "شهردار",
        "The Prime Minister": "نخست‌وزیر",
        "The King or Queen": "پادشاه یا ملکه",
        "The Chief Justice": "رییس قضات",
        "308": "۳۰۸",
        "338": "۳۳۸",
        "350": "۳۵۰",
        "400": "۴۰۰",
        "96": "۹۶",
        "105": "۱۰۵",
        "120": "۱۲۰",
        "150": "۱۵۰",
        "24 Sussex Drive": "۲۴ٔ خیابان ساسکس",
        "Rideau Hall": "رایدو هال",
        "Parliament Hill": "تپه پارلمان",
        "The White House": "کاخ سفید",
        "National Gallery": "گالری ملی",
        "Peace Tower": "برج صلح",
        "Victory Tower": "برج پیروزی",
        "Unity Tower": "برج وحدت",
        "Freedom Tower": "برج آزادی",
        "Speech from the Throne": "سخنرانی تخت (افتتاح پارلمان)",
        "Opening Address": "سخنرانی افتتاحیه",
        "State of the Union": "وضعیت اتحادیه",
        "Royal Address": "سخنرانی سلطنتی",
        "Budget": "بودجه",
        "Throne Speech": "سخنرانی تخت",
        "Legislative process": "روند قانون‌گذاری",
        "Parliamentary process": "روند پارلمانی",
        "Royal Assent": "تأیید سلطنتی",
        "Government with less than 50% of seats": "دولتی با کمتر از ۵۰٪ کرسی‌ها",
        "Government with majority of seats": "دولتی با اکثریت کرسی‌ها",
        "Coalition government": "دولت ائتلافی",
        "Temporary government": "دولت موقت",
        "The party with the most votes": "حزبی با بیشترین آراء",
        "The party with the most seats in the House of Commons": "حزبی با بیشترین کرسی در مجلس عوام",
        "The largest party": "بزرگ‌ترین حزب",
        "The party chosen by the Governor General": "حزبی که فرماندار کل انتخاب می‌کند",
        "The party with the second most seats": "حزبی با دومین تعداد کرسی",
        "The party chosen by the PM": "حزبی که نخست‌وزیر انتخاب کرده",
        "The person elected in your riding": "شخصی که در حوزهٔ انتخابیه شما انتخاب شده",
        "The Premier": "نخست‌وزیر استانی",
        "The Mayor": "شهردار",
        "Legislation": "قانون‌گذاری",
        "Bill": "لایحه",
        "Act": "قانون مصوب",
        "Statute": "قانون اسکریپت/اساسنامه",
        "Third reading": "قرائت سوم",
        "Committee review": "بررسی در کمیته",
        "First reading": "قرائت اول",
        "Government responsible to the people": "دولت در برابر مردم مسئول است",
        "Government responsible to the Queen": "دولت در برابر ملکه مسئول است",
        "Government that makes good decisions": "دولتی که تصمیمات خوب می‌گیرد",
        "Government with many responsibilities": "دولتی با وظایف فراوان",
        "To make laws": "وضع قانون",
        "To represent the Crown in Canada": "نمایندگی تاج در کانادا",
        "To lead the government": "رهبری دولت",
        "To interpret laws": "تفسیر قوانین",
        "Parliament": "پارلمان",
        "The people": "مردم",
        "A bill": "یک لایحه",
        "A proposed law": "یک قانون پیشنهادی",
        "A petition": "یک دادخواست",
        "A regulation": "یک آیین‌نامه",
        # مکمل گزینه‌های بانک سوال (بدون معادل در ۴۱۴/۵۷۱)
        "A dictatorship": "دیکتاتوری",
        "A draft": "پیش‌نویس",
        "A government for minority groups": "دولتی برای گروه‌های اقلیت",
        "A government with less than 50% of seats": "دولتی با کمتر از ۵۰٪ کرسی‌ها",
        "A military government": "دولت نظامی",
        "A motion": "طرح (موشن) پارلمانی",
        "A proposal": "پیشنهاد",
        "A provincial government": "دولت استانی",
        "A republic": "جمهوری",
        "A system where Parliament is the primary legislative body": "سیستمی که پارلمان نهاد اصلی قانون‌گذاری است",
        "A system where the King/Queen is head of state but power is limited by the constitution": "پادشاهی با قدرت محدود در چارچوب قانون اساسی",
        "A system where the President has all power": "سیستمی که رئیس‌جمهور همهٔ قدرت را دارد",
        "A system where the monarch has unlimited power": "سیستمی که پادشاه قدرت نامحدود دارد",
        "A system without elections": "سیستمی بدون انتخابات",
        "A temporary government": "دولت موقت",
        "All opposition parties": "همهٔ احزاب اپوزسیون",
        "All parties together": "همهٔ احزاب با هم",
        "All power in one government": "متمرکز بودن قدرت در یک دولت",
        "Both of the above": "هر دو مورد بالا",
        "Canada has a monarch as head of state": "کانادا پادشاه به‌عنوان رئیس دولت دارد",
        "Canada is a republic": "کانادا جمهوری است",
        "Central government": "دولت مرکزی",
        "Democracy, Republic, Federation": "دموکراسی، جمهوری، فدراسیون",
        "Division of power between federal and provincial governments": "تقسیم قدرت بین دولت فدرال و استانی",
        "Health care": "بهداشت و درمان",
        "Local services, police, fire protection": "خدمات محلی، پلیس، ایمنی در برابر آتش",
        "Monarchy, Democracy, Confederation": "پادشاهی، دموکراسی، کنفدراسیون",
        "National defence, foreign policy, immigration, citizenship": "دفاع ملی، سیاست خارجی، مهاجرت، شهروندی",
        "National government": "دولت ملی",
        "No": "خیر",
        "No difference": "فرقی ندارد",
        "No government": "بدون دولت",
        "Not yet": "هنوز نه",
        "Only as observer": "فقط به‌صورت ناظر",
        "Prime Minister, Parliament, Supreme Court": "نخست‌وزیر، پارلمان، دادگاه عالی",
        "Second reading": "قرائت دوم",
        "Supreme Court Building": "ساختمان دادگاه عالی",
        "The Queen is head of state, Prime Minister is head of government": "ملکه رئیس دولت است؛ نخست‌وزیر رئیس حکومت است",
        "The Queen makes laws, PM enforces them": "ملکه قانون می‌سازد، نخست‌وزیر اجرا می‌کند",
        "The governing party": "حزب حاکم",
        "The monarch's powers are limited by the constitution": "قدرت پادشاه توسط قانون اساسی محدود است",
        "The party with the most seats": "حزبی با بیشترین کرسی",
        "The party with the second-largest number of seats in the House of Commons": "حزب با دومین تعداد کرسی در مجلس عوام",
        "They have the same role": "نقش یکسان دارند",
        "To elect representatives": "انتخاب نمایندگان",
        "To implement and enforce laws (Prime Minister and Cabinet)": "اجرای قوانین (نخست‌وزیر و کابینه)",
        "Yes": "بله",
    }
    for k, v in curated.items():
        if k not in patch:
            patch[k] = v

    out_path = os.path.join(BASE, "govern_options_fa_patch.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(patch, f, ensure_ascii=False, indent=2)

    still = []
    for q in govern:
        for opt in q.get("options") or []:
            o = opt.strip()
            if fa_lookup({**en_to_fa, **patch}, o) == o:
                if o not in still:
                    still.append(o)
    print("wrote", out_path, "entries", len(patch))
    print("still untranslated", len(still))
    for s in sorted(still)[:40]:
        print("  ", s)
    if len(still) > 40:
        print("  ...")


if __name__ == "__main__":
    main()

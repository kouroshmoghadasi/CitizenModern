# گزارش وضعیت SEO — CitizenTest (citizentest.invoisky.com)

تاریخ بررسی: بهمن ۱۴۰۴

---

## خلاصه وضعیت

| بخش | وضعیت | توضیح |
|-----|--------|--------|
| تگ‌های متا (title, description, keywords) | ✅ خوب | یکتا و سه‌زبان (فا/ان/فر) |
| Canonical و Robots | ✅ خوب | index, follow و canonical در همه صفحات |
| Open Graph و Twitter Card | ✅ خوب | برای اشتراک‌گذاری تنظیم شده |
| Schema.org (JSON-LD) | ✅ خوب | WebSite + LearningResource |
| Sitemap و Robots.txt | ⚠️ نیاز به تنظیم | آدرس‌ها باید HTTPS باشند |
| زبان و hreflang | ⚠️ قابل بهبود | فقط `lang="fa"`؛ hreflang برای چندزبان نیست |
| محتوای متنی و کیوردها | ✅ خوب | عبارات کلیدی در عنوان و توضیحات |
| سرعت و کش | ✅ خوب | Gzip و Cache-Control فعال است |

---

## نقاط قوت (انجام‌شده)

### ۱. تگ‌های متا
- **Title:** «آزمون شهروندی کانادا رایگان | تمرین تست شهروندی به فارسی و انگلیسی» — مناسب و حاوی کیورد.
- **Description:** توضیح روشن با عدد (۱۰۰ تست، ۴۱۴ و ۵۷۱ سوال، Discover Canada).
- **Keywords:** دامنه گسترده به سه زبان (فارسی، انگلیسی، فرانسه) شامل نمونه آزمون، آموزش، تمرین و غیره.

### ۲. ساختار فنی
- **Canonical:** هر صفحه `link rel="canonical"` دارد → کاهش duplicate content.
- **Robots:** `index, follow` → ایندکس و کراول لینک‌ها مجاز.
- **Google Site Verification:** تگ در `head_meta.html` وجود دارد.

### ۳. شبکه‌های اجتماعی
- **Open Graph:** og:title, og:description, og:image, og:url, og:locale (fa_IR), og:site_name.
- **Twitter Card:** summary_large_image با عنوان و توضیح.

### ۴. داده‌های ساختاریافته (Schema.org)
- **WebSite:** نام، alternateName، url، description، inLanguage، publisher، potentialAction.
- **LearningResource:** نوع منبع آموزشی، سطح بزرگسال، teaches.

### ۵. Sitemap و Robots
- **sitemap.xml:** چهار URL اصلی (/, book_summary.html, citizenship-414, citizenship-571) با lastmod و priority.
- **robots.txt:** Allow: / و آدرس Sitemap.

### ۶. سرعت و کش (از تغییرات قبلی)
- Gzip (Flask-Compress) و Cache-Control برای استاتیک و PDF فعال است.

---

## موارد نیاز به توجه

### ۱. آدرس Sitemap و لینک‌های Sitemap باید HTTPS باشند
- در بررسی زنده، `robots.txt` و `sitemap.xml` با **http://** برگردانده می‌شدند. گوگل ترجیح می‌دهد همهٔ آدرس‌ها در sitemap و robots **https** باشند.
- **اقدام در کد:** تابع `_seo_base_url()` اضافه شده که در صورت وجود هدر `X-Forwarded-Proto: https` (پشت پروکسی/البی)، آدرس پایه را به HTTPS تغییر می‌دهد.
- **اقدام روی سرور:** مطمئن شوید پروکسی (مثلاً Nginx یا load balancer) هدر `X-Forwarded-Proto: https` را به اپلیکیشن می‌فرستد. اگر نمی‌فرستد، می‌توان در تنظیمات سرور یا در config اپ یک BASE_URL ثابت (مثلاً `https://citizentest.invoisky.com`) برای sitemap و robots تعریف کرد.

### ۲. زبان و hreflang (اختیاری برای آینده)
- الان فقط `lang="fa"` در `<html>` تنظیم شده که برای صفحهٔ اصلی فارسی مناسب است.
- سایت محتوای سه‌زبان (فا/ان/فر) در یک URL دارد؛ برای گوگل می‌توان با **hreflang** (مثلاً fa, en, fr برای همان URL یا برای صفحات جدا در صورت داشتن URL جدا به زبان‌ها) سیگنال روشن‌تری داد. در وضع فعلی (یک صفحه با سوئیچ زبان) اولویت پایین‌تر است.

### ۳. محتوای متنی قابل مشاهده
- در صفحهٔ اصلی، راهنمای استفاده و بلوک‌های حمایت مالی متن دارند؛ خوب است در همان متن‌ها یک یا دو بار طبیعی عبارت‌هایی مثل «آزمون شهروندی کانادا» و «تست شهروندی رایگان» تکرار شود (بدون کیورد استافینگ).

---

## کارهای پیشنهادی (خارج از کد)

1. **Google Search Console (GSC)**  
   - ثبت ملک با آدرس دقیق: `https://citizentest.invoisky.com`  
   - ارسال Sitemap: `https://citizentest.invoisky.com/sitemap.xml`  
   - پایش Coverage و Enhancements

2. **Bing Webmaster Tools**  
   - اضافه کردن سایت و همان sitemap

3. **بک‌لینک و شناخته‌شدن**  
   - اشتراک لینک در گروه‌ها/انجمن‌های مرتبط با مهاجرت و شهروندی کانادا (بدون اسپم)  
   - لینک در پروفایل شبکه‌های اجتماعی

4. **پایش مداوم**  
   - در GSC: عباراتی که سایت برای آن‌ها نشان داده می‌شود، تعداد کلیک و Impression، خطاهای ایندکس

---

## جمع‌بندی

وضعیت **تکنیکال SEO** سایت قوی است: متا تگ‌ها، Schema، OG/Twitter، canonical و sitemap در جای خود هستند. با اطمینان از **HTTPS در sitemap و robots** (از طریق پروکسی یا BASE_URL) و انجام کارهای خارج از کد (GSC، Bing، لینک‌سازی)، شانس دیده‌شدن برای عبارت‌هایی مثل «آزمون شهروندی کانادا» و «تست شهروندی رایگان» بیشتر می‌شود.

import os
import re
from pathlib import Path

from PIL import Image
import pytesseract
from deep_translator import GoogleTranslator


ROOT = Path(__file__).resolve().parents[1]
IMAGES_DIR = ROOT / "static" / "book_summary_2_pages"
OUT_TEMPLATE = ROOT / "templates" / "_book_summary_2_content.html"

_FA_GLOSSARY = {
    "Magna Carta": "مگنا کارتا",
    "Habeas corpus": "هَبِئَس کورپوس",
    "Canadian Charter of Rights and Freedoms": "منشور حقوق و آزادی‌های کانادا",
    "Charter of Rights and Freedoms": "منشور حقوق و آزادی‌ها",
    "Mobility Rights": "حقوق جابه‌جایی (Mobility Rights)",
    "Aboriginal Peoples’ Rights": "حقوق مردمان بومی (Aboriginal Peoples’ Rights)",
    "Official Language Rights": "حقوق زبان‌های رسمی (Official Language Rights)",
    "Multiculturalism": "چندفرهنگی (Multiculturalism)",
    "House of Commons": "مجلس عوام",
    "Senate": "سنا",
    "Prime Minister": "نخست‌وزیر",
    "Governor General": "فرماندار کل",
    "Lieutenant Governor": "معاون فرماندار (Lieutenant Governor)",
    "MP": "نمایندهٔ پارلمان (MP)",
}


def _ensure_tesseract_cmd() -> None:
    # On Windows, winget install may not add tesseract to PATH.
    if os.name == "nt":
        candidate = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        if candidate.exists():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)


def _ocr_image(path: Path) -> str:
    img = Image.open(path)
    img = img.convert("L")
    cfg = "--oem 3 --psm 6"
    text = pytesseract.image_to_string(img, lang="eng", config=cfg)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = [ln.rstrip() for ln in text.split("\n")]
    cleaned: list[str] = []
    blank_run = 0
    for ln in lines:
        if not ln.strip():
            blank_run += 1
            if blank_run <= 1:
                cleaned.append("")
            continue
        blank_run = 0
        cleaned.append(ln)
    return "\n".join(cleaned).strip()

def _normalize_ocr_en(text: str) -> str:
    """
    Light cleanup of English OCR before translation to improve quality.
    """
    s = text
    s = s.replace("’", "'").replace("“", '"').replace("”", '"')
    s = s.replace(" |,", "").replace("|,", "")
    # Common OCR noise
    s = re.sub(r"\bjs\b", "is", s, flags=re.IGNORECASE)
    s = re.sub(r"\btight fo\b", "right to", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+\|\s*", " ", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    # Keep line structure; strip trailing spaces
    s = "\n".join(ln.rstrip() for ln in s.splitlines())
    return s.strip()


def _normalize_fa(text: str) -> str:
    """
    Post-process Persian to reduce obvious machine/OCR artifacts.
    """
    s = text
    # Fix common mojibake in console outputs
    s = s.replace("�", "")
    # Persian punctuation/spacing
    s = s.replace("ي", "ی").replace("ك", "ک")
    s = re.sub(r"\s+،", "،", s)
    s = re.sub(r"\s+\.", ".", s)
    s = re.sub(r"([\u0600-\u06FF])\s+([\u0600-\u06FF])", r"\1 \2", s)
    # Normalize quotes
    s = s.replace('"', "«").replace("««", "«").replace("»»", "»")
    # Remove stray Latin fragments like "@."
    s = re.sub(r"(^|\s)[@#]\.?\s*", r"\1", s)
    # Apply glossary
    for en, fa in _FA_GLOSSARY.items():
        s = s.replace(en, fa)
    # Collapse excessive blank lines
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def _translate(text: str, target: str) -> str:
    if not text.strip():
        return ""
    tr = GoogleTranslator(source="en", target=target)

    max_chunk = 3500
    parts: list[str] = []
    buf = ""
    for block in text.split("\n\n"):
        piece = block + "\n\n"
        if len(buf) + len(piece) > max_chunk and buf:
            parts.append(tr.translate(buf.rstrip()))
            buf = piece
        else:
            buf += piece
    if buf.strip():
        parts.append(tr.translate(buf.rstrip()))

    return "\n\n".join(p.strip() for p in parts if p is not None)


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

_RE_NUM = re.compile(r"^\s*(\d{1,3})\s*[\.\-\)]\s+(.*)\s*$")
_RE_LET = re.compile(r"^\s*([A-Za-z])\s*[\.\)]\s+(.*)\s*$")
_RE_ROM = re.compile(r"^\s*([ivxlcdmIVXLCDM]{1,6})\s*[\.\)]\s+(.*)\s*$")
_RE_BUL = re.compile(r"^\s*([*•\-o])\s+(.*)\s*$")


def _is_heading(line: str) -> bool:
    s = line.strip()
    if len(s) < 4 or len(s) > 80:
        return False
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return False
    upper_ratio = sum(1 for c in letters if c.isupper()) / max(1, len(letters))
    return upper_ratio >= 0.85


def _classify_line(line: str) -> tuple[int | None, str | None, str, str]:
    """
    Return (level, list_kind, marker, text).
    list_kind: 'num' | 'let' | 'rom' | 'bul' | None
    """
    s = line.rstrip()
    if not s.strip():
        return (None, None, "", "")
    for kind, rx in (("num", _RE_NUM), ("let", _RE_LET), ("rom", _RE_ROM), ("bul", _RE_BUL)):
        m = rx.match(s)
        if m:
            marker = m.group(1).strip()
            text = m.group(2).strip()
            level = {"num": 1, "let": 2, "rom": 3, "bul": 4}[kind]
            return (level, kind, marker, text)
    return (None, None, "", s.strip())


def _render_outline(items: list[tuple[int, str, str, str]]) -> str:
    """
    items: list of (level, kind, marker, text) for list-like lines only.
    Produces nested <ol>/<ul> structure.
    """
    out: list[str] = []
    stack: list[tuple[int, str]] = []

    def open_list(kind: str) -> None:
        if kind == "num":
            out.append('<ol class="ocr-list ocr-list-num">')
        elif kind == "let":
            out.append('<ol class="ocr-list ocr-list-let" type="a">')
        elif kind == "rom":
            out.append('<ol class="ocr-list ocr-list-rom" type="i">')
        else:
            out.append('<ul class="ocr-list ocr-list-bul">')

    def close_list() -> None:
        if not stack:
            return
        _, kind = stack.pop()
        out.append("</ol>" if kind in ("num", "let", "rom") else "</ul>")

    for level, kind, marker, text in items:
        # adjust nesting by level
        while stack and stack[-1][0] > level:
            close_list()
        if not stack or stack[-1][0] < level:
            open_list(kind)
            stack.append((level, kind))
        elif stack[-1][1] != kind:
            # same level but different kind -> close and reopen
            close_list()
            open_list(kind)
            stack.append((level, kind))

        out.append(
            "<li>"
            f'<span class="ocr-marker">{_html_escape(marker)}</span>'
            f'<span class="ocr-text">{_html_escape(text)}</span>'
            "</li>"
        )

    while stack:
        close_list()
    return "\n".join(out)


def _text_to_pdfish_html(text: str) -> str:
    """
    Convert OCR'd text into a PDF-like readable HTML:
    headings, paragraphs, and nested lists based on markers (1., a., i., -, *).
    """
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    blocks: list[str] = []
    pending_list: list[tuple[int, str, str, str]] = []

    def flush_list() -> None:
        nonlocal pending_list
        if pending_list:
            blocks.append(_render_outline(pending_list))
            pending_list = []

    para_buf: list[str] = []

    def flush_para() -> None:
        nonlocal para_buf
        if not para_buf:
            return
        p = " ".join(s.strip() for s in para_buf if s.strip()).strip()
        if p:
            blocks.append(f"<p>{_html_escape(p)}</p>")
        para_buf = []

    for ln in lines:
        if not ln.strip():
            flush_list()
            flush_para()
            continue

        if _is_heading(ln):
            flush_list()
            flush_para()
            blocks.append(f'<h3 class="ocr-heading">{_html_escape(ln.strip())}</h3>')
            continue

        level, kind, marker, txt = _classify_line(ln)
        if kind is not None and txt:
            flush_para()
            pending_list.append((level or 1, kind, marker, txt))
            continue

        # continuation line -> treat as paragraph continuation
        flush_list()
        para_buf.append(ln.strip())

    flush_list()
    flush_para()
    return "\n".join(blocks).strip()


def main() -> None:
    _ensure_tesseract_cmd()

    pages: list[tuple[int, Path]] = []
    for p in IMAGES_DIR.glob("page-*.png"):
        m = re.search(r"page-(\d+)\.png$", p.name)
        if not m:
            continue
        pages.append((int(m.group(1)), p))
    pages.sort(key=lambda x: x[0])

    if not pages:
        raise SystemExit(f"No pages found in {IMAGES_DIR}")

    sections: list[str] = []

    for n, path in pages:
        en_raw = _ocr_image(path)
        en = _normalize_ocr_en(en_raw)
        fr = _translate(en, "fr")
        fa = _normalize_fa(_translate(en, "fa"))

        en_html = _text_to_pdfish_html(en)
        fr_html = _text_to_pdfish_html(fr)
        fa_html = _text_to_pdfish_html(fa)

        if n <= 2:
            sections.append(
                '            <div class="summary-section">\n'
                f'                <div class="summary-section-title"><span class="summary-title-stack"><span class="summary-heading-fa">صفحهٔ {n}</span><span class="summary-heading-en">Page {n}</span><span class="summary-heading-fr">Page {n}</span></span></div>\n'
                '                <ul class="summary-list">\n'
                '                    <li class="summary-list-item">\n'
                f'                        <span class="summary-item-fa"><div class="summary-ocr-text summary-ocr-text-fa">{fa_html}</div></span>\n'
                f'                        <div class="summary-item-en"><div class="summary-ocr-text summary-ocr-text-en">{en_html}</div></div>\n'
                f'                        <div class="summary-item-fr"><div class="summary-ocr-text summary-ocr-text-fr">{fr_html}</div></div>\n'
                "                    </li>\n"
                "                </ul>\n"
                "            </div>\n"
            )
            continue

        sections.append('{% if can_view_book_summary_2_full %}\n')
        sections.append(
            '            <div class="summary-section">\n'
            f'                <div class="summary-section-title"><span class="summary-title-stack"><span class="summary-heading-fa">صفحهٔ {n}</span><span class="summary-heading-en">Page {n}</span><span class="summary-heading-fr">Page {n}</span></span></div>\n'
            '                <ul class="summary-list">\n'
            '                    <li class="summary-list-item">\n'
            f'                        <span class="summary-item-fa"><div class="summary-ocr-text summary-ocr-text-fa">{fa_html}</div></span>\n'
            f'                        <div class="summary-item-en"><div class="summary-ocr-text summary-ocr-text-en">{en_html}</div></div>\n'
            f'                        <div class="summary-item-fr"><div class="summary-ocr-text summary-ocr-text-fr">{fr_html}</div></div>\n'
            "                    </li>\n"
            "                </ul>\n"
            "            </div>\n"
        )
        if n == 3:
            sections.append(
                '{% else %}\n'
                '{% if show_paywall_book_summary_2 %}\n'
                '            <div class="summary-section" id="bookSummary2Paywall">\n'
                '                <div class="summary-section-title"><span class="summary-title-stack"><span class="summary-heading-fa">ادامهٔ صفحات (۳ تا ۳۵)</span><span class="summary-heading-en">Pages 3–35</span><span class="summary-heading-fr">Pages 3 à 35</span></span></div>\n'
                '                <div class="highlight-box" style="padding: 0; margin: 0; border: none;">\n'
                '                    <h2 style="margin-bottom: 12px; color: var(--bs-accent);">دسترسی به صفحات ۳ تا ۳۵</h2>\n'
                '                    <p style="margin-bottom: 16px; direction: rtl;">برای مشاهدهٔ همهٔ صفحات «خلاصهٔ ۲»، همان اشتراک یک‌ماههٔ <strong>{{ subscription_price }} دلار</strong> (۴۱۴/۵۷۱) لازم است. واریز به ایمیل زیر و ارسال رسید؛ پس از تأیید، کد کاربری و رمز ارسال می‌شود.</p>\n'
                '                    <div class="paywall-414-email-block">\n'
                '                        <span class="paywall-414-email-label">ایمیل:</span>\n'
                '                        <span class="paywall-414-email-value" id="paywall414EmailValue">Koroush.mog@gmail.com</span>\n'
                '                        <button type="button" class="paywall-414-btn-copy" id="paywall414EmailCopy" title="کپی">کپی</button>\n'
                '                    </div>\n'
                '                    <p style="margin-bottom: 14px; direction: rtl;"><strong>ورود (در صورت داشتن کد و رمز):</strong></p>\n'
                '                    <input type="text" id="paywall414Mobile" placeholder="کد کاربری (شماره موبایل)" style="width: 100%; padding: 12px; margin-bottom: 10px; border: 1px solid var(--bs-border); border-radius: 10px;">\n'
                '                    <input type="password" id="paywall414Password" placeholder="کلمه عبور" style="width: 100%; padding: 12px; margin-bottom: 10px; border: 1px solid var(--bs-border); border-radius: 10px;">\n'
                '                    <p id="paywall414Error" class="subscription-error" style="display: none; color: #c00; margin-bottom: 8px;"></p>\n'
                '                    <button type="button" id="paywall414LoginBtn" style="padding: 12px 24px; background: var(--bs-accent); color: #fff; border: none; border-radius: 10px; cursor: pointer; font-weight: 600;">ورود و مشاهده همه صفحات</button>\n'
                '                </div>\n'
                '            </div>\n'
                '            <script>\n'
                '            (function() {\n'
                '                var copyBtn = document.getElementById(\'paywall414EmailCopy\');\n'
                '                var emailEl = document.getElementById(\'paywall414EmailValue\');\n'
                '                if (copyBtn && emailEl) {\n'
                '                    copyBtn.addEventListener(\'click\', function() {\n'
                '                        var text = emailEl.textContent || \'\';\n'
                '                        if (!text) return;\n'
                '                        if (navigator.clipboard && navigator.clipboard.writeText) {\n'
                '                            navigator.clipboard.writeText(text).then(function() {\n'
                '                                copyBtn.textContent = \'کپی شد!\';\n'
                '                                copyBtn.classList.add(\'copied\');\n'
                '                                setTimeout(function() { copyBtn.textContent = \'کپی\'; copyBtn.classList.remove(\'copied\'); }, 2000);\n'
                '                            }).catch(function() {});\n'
                '                        }\n'
                '                    });\n'
                '                }\n'
                '                var btn = document.getElementById(\'paywall414LoginBtn\');\n'
                '                if (!btn) return;\n'
                '                btn.addEventListener(\'click\', function() {\n'
                '                    var mobile = (document.getElementById(\'paywall414Mobile\').value || \'\').trim();\n'
                '                    var password = document.getElementById(\'paywall414Password\').value || \'\';\n'
                '                    var errEl = document.getElementById(\'paywall414Error\');\n'
                '                    errEl.style.display = \'none\';\n'
                '                    errEl.textContent = \'\';\n'
                '                    if (!mobile || !password) {\n'
                '                        errEl.textContent = \'کد کاربری و کلمه عبور الزامی است.\';\n'
                '                        errEl.style.display = \'block\';\n'
                '                        return;\n'
                '                    }\n'
                '                    fetch(window.location.origin + \'/api/subscription/login\', {\n'
                '                        method: \'POST\',\n'
                '                        headers: { \'Content-Type\': \'application/json\' },\n'
                '                        credentials: \'include\',\n'
                '                        body: JSON.stringify({ mobile: mobile, password: password, section: \'questions_414\' })\n'
                '                    }).then(function(r) { return r.json(); }).then(function(data) {\n'
                '                        if (data && data.success) {\n'
                '                            window.location.reload();\n'
                '                        } else {\n'
                '                            errEl.textContent = (data && data.error) ? data.error : \'خطا در ورود.\';\n'
                '                            errEl.style.display = \'block\';\n'
                '                        }\n'
                '                    }).catch(function() {\n'
                '                        errEl.textContent = \'خطای اتصال.\';\n'
                '                        errEl.style.display = \'block\';\n'
                '                    });\n'
                '                });\n'
                '            })();\n'
                '            </script>\n'
                '{% endif %}\n'
            )
        sections.append('{% endif %}\n')

    OUT_TEMPLATE.write_text("".join(sections), encoding="utf-8")
    print(f"Wrote {OUT_TEMPLATE}")


if __name__ == "__main__":
    main()


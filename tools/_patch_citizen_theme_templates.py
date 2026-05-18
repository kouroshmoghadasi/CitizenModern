"""One-off patcher: wire shared citizenSiteTheme into citizenship templates."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"

HEAD_SNIPPET = (
    "{% set citizen_theme_profile = 'exam' %}\n"
    "{% include '_citizen_site_theme_head.html' %}\n"
)

HEAD_SNIPPET_414 = (
    "{% set citizen_theme_profile = 'exam' %}\n"
    "{% set citizen_theme_page_key = 'citizenship414_theme' %}\n"
    "{% include '_citizen_site_theme_head.html' %}\n"
)

BOOT_571 = (
    "    <script>try{var t=localStorage.getItem('citizenship571_theme');"
    "if(t==='dark')document.body.classList.add('theme-dark');}catch(e){}</script>"
)

BOOT_414 = (
    "    <script>try{var t=localStorage.getItem('citizenship414_theme');"
    "if(t==='dark')document.body.classList.add('theme-dark');}catch(e){}</script>"
)

BODY_SYNC = "    {% include '_citizen_site_theme_body_sync.html' %}"

OLD_APPLY = """            function applyTheme(val) {
                if (val === 'dark') { document.body.classList.add('theme-dark'); if (themeLight) themeLight.setAttribute('aria-pressed', 'false'); if (themeDark) themeDark.setAttribute('aria-pressed', 'true'); }
                else { document.body.classList.remove('theme-dark'); if (themeLight) themeLight.setAttribute('aria-pressed', 'true'); if (themeDark) themeDark.setAttribute('aria-pressed', 'false'); }
            }"""

NEW_APPLY = """            function applyTheme(val) {
                if (val === 'dark') { document.body.classList.add('theme-dark'); if (themeLight) themeLight.setAttribute('aria-pressed', 'false'); if (themeDark) themeDark.setAttribute('aria-pressed', 'true'); }
                else { document.body.classList.remove('theme-dark'); if (themeLight) themeLight.setAttribute('aria-pressed', 'true'); if (themeDark) themeDark.setAttribute('aria-pressed', 'false'); }
                document.documentElement.setAttribute('data-theme', val === 'dark' ? 'dark' : 'light');
            }"""

OLD_SAVED = "            var savedTheme = localStorage.getItem(themeKey) || 'light';"

NEW_SAVED = """            var savedTheme = (function () {
                try {
                    var g = localStorage.getItem('citizenSiteTheme');
                    if (g === 'dark' || g === 'light') return g === 'dark' ? 'dark' : 'light';
                    g = localStorage.getItem('modernLandingTheme');
                    if (g === 'dark' || g === 'light') return g === 'dark' ? 'dark' : 'light';
                    var p = localStorage.getItem(themeKey);
                    return (p === 'dark') ? 'dark' : 'light';
                } catch (e) {
                    return 'light';
                }
            })();"""

OLD_CLICK_LIGHT = (
    "            if (themeLight) themeLight.addEventListener('click', function() { "
    "localStorage.setItem(themeKey, 'light'); applyTheme('light'); });"
)

NEW_CLICK_LIGHT = (
    "            if (themeLight) themeLight.addEventListener('click', function() { "
    "try { localStorage.setItem('citizenSiteTheme', 'light'); "
    "localStorage.setItem('modernLandingTheme', 'light'); "
    "localStorage.setItem(themeKey, 'light'); } catch(e){} applyTheme('light'); });"
)

OLD_CLICK_DARK = (
    "            if (themeDark) themeDark.addEventListener('click', function() { "
    "localStorage.setItem(themeKey, 'dark'); applyTheme('dark'); });"
)

NEW_CLICK_DARK = (
    "            if (themeDark) themeDark.addEventListener('click', function() { "
    "try { localStorage.setItem('citizenSiteTheme', 'dark'); "
    "localStorage.setItem('modernLandingTheme', 'dark'); "
    "localStorage.setItem(themeKey, 'dark'); } catch(e){} applyTheme('dark'); });"
)

EXAM_FILES = [
    "citizenship_exams.html",
    "citizenship_introduction.html",
    "exam1.html",
    "exam2.html",
    "exam3.html",
    "citizenship_571.html",
    "citizenship_canadas_history.html",
    "citizenship_rights_responsibilities.html",
    "citizenship_canadian_symbols.html",
    "citizenship_canadas_economy.html",
    "citizenship_exam_report.html",
    "canadian_history_timeline.html",
    "citizenship_how_canadians_govern_themselves.html",
    "citizenship_federal_elections.html",
    "citizenship_canadas_regions.html",
    "citizenship_who_we_are.html",
    "citizenship_modern_canada.html",
    "federal_questions_226.html",
    "citizenship_justice_system.html",
]


def patch_head(content: str, snippet: str) -> str:
    marker = "{% include '_citizen_site_theme_head.html' %}"
    if marker in content:
        return content
    needle = "</head>"
    if needle not in content:
        raise ValueError("no </head>")
    return content.replace(needle, snippet + needle, 1)


def patch_boot(content: str, boot_old: str) -> str:
    if BODY_SYNC in content and boot_old not in content:
        return content
    if boot_old not in content:
        return content
    return content.replace(boot_old, BODY_SYNC, 1)


def patch_footer_blocks(content: str) -> str:
    if OLD_APPLY in content:
        content = content.replace(OLD_APPLY, NEW_APPLY, 1)
    if OLD_SAVED in content:
        content = content.replace(OLD_SAVED, NEW_SAVED, 1)
    if OLD_CLICK_LIGHT in content:
        content = content.replace(OLD_CLICK_LIGHT, NEW_CLICK_LIGHT, 1)
    if OLD_CLICK_DARK in content:
        content = content.replace(OLD_CLICK_DARK, NEW_CLICK_DARK, 1)
    return content


def patch_citizenship_414(content: str) -> str:
    content = patch_head(content, HEAD_SNIPPET_414)
    content = patch_boot(content, BOOT_414)
    old_apply = """            function applyTheme(val) {
                if (val === 'dark') {
                    document.body.classList.add('theme-dark');
                    if (themeLight) themeLight.setAttribute('aria-pressed', 'false');
                    if (themeDark) themeDark.setAttribute('aria-pressed', 'true');
                } else {
                    document.body.classList.remove('theme-dark');
                    if (themeLight) themeLight.setAttribute('aria-pressed', 'true');
                    if (themeDark) themeDark.setAttribute('aria-pressed', 'false');
                }
            }"""
    new_apply = """            function applyTheme(val) {
                if (val === 'dark') {
                    document.body.classList.add('theme-dark');
                    if (themeLight) themeLight.setAttribute('aria-pressed', 'false');
                    if (themeDark) themeDark.setAttribute('aria-pressed', 'true');
                } else {
                    document.body.classList.remove('theme-dark');
                    if (themeLight) themeLight.setAttribute('aria-pressed', 'true');
                    if (themeDark) themeDark.setAttribute('aria-pressed', 'false');
                }
                document.documentElement.setAttribute('data-theme', val === 'dark' ? 'dark' : 'light');
            }"""
    if old_apply in content:
        content = content.replace(old_apply, new_apply, 1)
    ol = (
        "            if (themeLight) themeLight.addEventListener('click', function() { "
        "localStorage.setItem(themeKey, 'light'); applyTheme('light'); });"
    )
    nw = (
        "            if (themeLight) themeLight.addEventListener('click', function() { "
        "try { localStorage.setItem('citizenSiteTheme', 'light'); "
        "localStorage.setItem('modernLandingTheme', 'light'); "
        "localStorage.setItem(themeKey, 'light'); } catch(e){} applyTheme('light'); });"
    )
    if ol in content:
        content = content.replace(ol, nw, 1)
    od = (
        "            if (themeDark) themeDark.addEventListener('click', function() { "
        "localStorage.setItem(themeKey, 'dark'); applyTheme('dark'); });"
    )
    nd = (
        "            if (themeDark) themeDark.addEventListener('click', function() { "
        "try { localStorage.setItem('citizenSiteTheme', 'dark'); "
        "localStorage.setItem('modernLandingTheme', 'dark'); "
        "localStorage.setItem(themeKey, 'dark'); } catch(e){} applyTheme('dark'); });"
    )
    if od in content:
        content = content.replace(od, nd, 1)
    old_saved = "            var savedTheme = localStorage.getItem(themeKey) || 'light';"
    if old_saved in content:
        content = content.replace(old_saved, NEW_SAVED, 1)
    return content


def main():
    for name in EXAM_FILES:
        path = TEMPLATES / name
        text = path.read_text(encoding="utf-8")
        original = text
        if name == "citizenship_414.html":
            text = patch_citizenship_414(text)
        else:
            text = patch_head(text, HEAD_SNIPPET)
            text = patch_boot(text, BOOT_571)
            text = patch_footer_blocks(text)
        if text != original:
            path.write_text(text, encoding="utf-8")
            print("patched", name)
        else:
            print("skip", name)


if __name__ == "__main__":
    main()

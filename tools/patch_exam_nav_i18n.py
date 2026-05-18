#!/usr/bin/env python3
"""Replace Persian exam nav buttons with shared EN/FR partials."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"

NAV_RE = re.compile(
    r'<div id="(q-nav-bar-[^"]+)" class="[^"]+" data-max-question="\{\{ ([^}]+) \}\}">'
    r".*?"
    r'<button type="button" class="q-nav-btn btn-prev" id="([^"]+)"[^>]*>.*?</button>\s*'
    r'<span class="q-nav-current"[^>]*>Question <span id="([^"]+)">1</span> of \{\{ ([^}]+) \}\}</span>\s*'
    r'<button type="button" class="q-nav-btn" id="([^"]+)"[^>]*>.*?</button>\s*'
    r"</motion div>",
    re.DOTALL,
)
NAV_RE = re.compile(
    r'<div id="(q-nav-bar-[^"]+)" class="[^"]+" data-max-question="\{\{ ([^}]+) \}\}">'
    r".*?"
    r'<button type="button" class="q-nav-btn btn-prev" id="([^"]+)"[^>]*>.*?</button>\s*'
    r'<span class="q-nav-current"[^>]*>Question <span id="([^"]+)">1</span> of \{\{ ([^}]+) \}\}</span>\s*'
    r'<button type="button" class="q-nav-btn" id="([^"]+)"[^>]*>.*?</button>\s*'
    r"</div>",
    re.DOTALL,
)

GO_RE = re.compile(
    r'<div class="group go-to-q-wrap">\s*'
    r'<label for="([^"]+)"[^>]*>.*?</label>\s*'
    r'<input type="number" id="\1" min="1" max="\{\{ ([^}]+) \}\}"[^>]*>\s*'
    r'<button type="button" class="go-to-q-btn" id="([^"]+)">.*?</button>\s*'
    r"</div>",
    re.DOTALL,
)


def nav_repl(m: re.Match) -> str:
    nav_id, _data_max, prev_id, num_id, max_vis, next_id = m.groups()
    return (
        f"{{% set q_nav_id = '{nav_id}' %}}\n"
        f"        {{% set q_prev_id = '{prev_id}' %}}\n"
        f"        {{% set q_next_id = '{next_id}' %}}\n"
        f"        {{% set q_num_id = '{num_id}' %}}\n"
        f"        {{% set q_max = {max_vis} %}}\n"
        f"        {{% include '_exam_q_nav_bar.html' %}}"
    )


def go_repl(m: re.Match) -> str:
    inp, go_max, btn = m.groups()
    return (
        f"{{% set go_input_id = '{inp}' %}}\n"
        f"            {{% set go_btn_id = '{btn}' %}}\n"
        f"            {{% set go_max = {go_max} %}}\n"
        f"            {{% include '_exam_go_to_q_group.html' %}}"
    )


def main() -> None:
    count = 0
    for path in sorted(TEMPLATES.glob("*.html")):
        text = path.read_text(encoding="utf-8")
        if "go-to-q-wrap" not in text and "q-nav-btn btn-prev" not in text:
            continue
        text2, n1 = (text, 0)
        if "_exam_q_nav_bar.html" not in text:
            text2, n1 = NAV_RE.subn(nav_repl, text)
        text3, n2 = (text2, 0)
        if "go-to-q-wrap" in text2 and "برو</button>" in text2:
            text3, n2 = GO_RE.subn(go_repl, text2)
        if n1 or n2:
            path.write_text(text3, encoding="utf-8")
            print(f"{path.name}: nav={n1} go={n2}")
            count += 1
    print(f"Patched {count} files")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
Compare 571 JSON correct answers with 571_Questions_English_Persian.html (A: answer text).
Reports questions where the option matching HTML answer != JSON correct index.
No changes applied.
"""
import re
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(SCRIPT_DIR, "571_Questions_English_Persian.html")
JSON_PATH = os.path.join(SCRIPT_DIR, "static", "citizenship_571_questions.json")


def normalize(t):
    if not t:
        return ""
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t).strip().lower()
    t = re.sub(r"[\.\,\;\:\?\!\-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_html_answers(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        text = f.read()
    # Pattern: <div class="num">#N</div> ... <div class="a-en"><b>A:</b> ANSWER</div>
    blocks = re.split(r'<div class="qa">', text)
    result = {}
    for block in blocks:
        m_num = re.search(r'<div class="num">#(\d+)</div>', block)
        m_ans = re.search(r'<div class="a-en"><b>A:</b>\s*([^<]+)', block)
        if m_num and m_ans:
            num = int(m_num.group(1))
            ans = m_ans.group(1).strip()
            ans = re.sub(r"<[^>]+>", " ", ans).strip()
            result[num] = ans
    return result


def find_best_option_index(html_answer, options):
    """Return index of option that best matches html_answer text."""
    if not options:
        return 0
    na = normalize(html_answer)
    if not na:
        return 0
    best = 0
    best_score = 0
    for i, opt in enumerate(options):
        no = normalize(opt)
        if na == no:
            return i
        if na in no or no in na:
            score = len(na) + len(no)
            if score > best_score:
                best_score = score
                best = i
        # word overlap
        wa = set(na.split())
        wo = set(no.split())
        overlap = len(wa & wo) / max(len(wa), 1)
        if overlap > best_score:
            best_score = overlap
            best = i
    if best_score > 0:
        return best
    # try first word or key word match
    for i, opt in enumerate(options):
        if na[:20] in normalize(opt) or normalize(opt)[:20] in na:
            return i
    return 0


def main():
    if not os.path.isfile(HTML_PATH):
        print("HTML not found:", HTML_PATH)
        return
    if not os.path.isfile(JSON_PATH):
        print("JSON not found:", JSON_PATH)
        return

    print("Loading HTML answers...")
    html_answers = extract_html_answers(HTML_PATH)
    print("HTML: found", len(html_answers), "question answers")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        json_questions = json.load(f)
    print("JSON: loaded", len(json_questions), "questions")

    diffs = []
    no_html = []
    for i in range(len(json_questions)):
        num = i + 1
        jq = json_questions[i]
        json_correct = jq.get("correct", 0)
        options = jq.get("options") or []
        html_ans = html_answers.get(num)
        if not html_ans:
            no_html.append(num)
            continue
        expected_idx = find_best_option_index(html_ans, options)
        if expected_idx != json_correct:
            json_ans = options[json_correct][:70] if json_correct < len(options) else "?"
            diffs.append({
                "num": num,
                "json_correct": json_correct,
                "expected_index": expected_idx,
                "html_answer": html_ans[:70],
                "json_answer": json_ans,
                "expected_option": options[expected_idx][:70] if expected_idx < len(options) else "?",
                "q_preview": (jq.get("q") or "")[:65],
            })

    # Report
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append("571 QUESTIONS - Answer check (JSON vs HTML source)")
    lines.append("=" * 70)
    lines.append("Total questions in JSON: " + str(len(json_questions)))
    lines.append("Total with answer in HTML: " + str(len(html_answers)))
    if no_html:
        lines.append("Question numbers missing in HTML (first 20): " + str(no_html[:20]))
    lines.append("")
    lines.append("DISCREPANCIES: questions where JSON 'correct' index != expected from HTML answer")
    lines.append("Total discrepancies: " + str(len(diffs)))
    lines.append("")
    if diffs:
        lines.append("List:")
        lines.append("-" * 70)
        for d in diffs:
            lines.append("Q" + str(d["num"]) + " | JSON correct index: " + str(d["json_correct"]) +
                        " | Expected index (from HTML): " + str(d["expected_index"]))
            lines.append("  Question: " + d["q_preview"] + "...")
            lines.append("  HTML answer text: " + d["html_answer"])
            lines.append("  Current JSON answer: " + d["json_answer"])
            lines.append("  Expected option text: " + d["expected_option"])
            lines.append("")
        lines.append("Question numbers to review/fix: " + str([d['num'] for d in diffs]))

    report = "\n".join(lines)
    print(report)
    report_path = os.path.join(SCRIPT_DIR, "571_answer_diff_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print("\nReport written to:", report_path)


if __name__ == "__main__":
    main()

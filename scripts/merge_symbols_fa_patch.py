"""Build static/canadian_symbols_options_fa_patch.json from canadian_symbols_questions.json + symbols_fa_lines.txt."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
jq = json.loads((ROOT / "static" / "canadian_symbols_questions.json").read_text(encoding="utf-8"))
keys = []
for q in jq:
    for o in q.get("options") or []:
        s = (o or "").strip()
        if s and s not in keys:
            keys.append(s)
lines = (ROOT / "static" / "symbols_fa_lines.txt").read_text(encoding="utf-8").splitlines()
if len(lines) != len(keys):
    raise SystemExit(f"symbols: want {len(keys)} fa lines, got {len(lines)}")
patch = {k: lines[i].strip() for i, k in enumerate(keys)}
out = ROOT / "static" / "canadian_symbols_options_fa_patch.json"
out.write_text(json.dumps(patch, ensure_ascii=False, indent=2), encoding="utf-8")
print("Wrote", out, len(patch))

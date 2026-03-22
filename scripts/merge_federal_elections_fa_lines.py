"""Merge static/fe_fa_lines_part1.txt + part2 into federal_elections_options_fa_patch.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
keys = json.loads((ROOT / "static" / "_fe_opts_order.json").read_text(encoding="utf-8"))
a = (ROOT / "static" / "fe_fa_lines_part1.txt").read_text(encoding="utf-8").splitlines()
b = (ROOT / "static" / "fe_fa_lines_part2.txt").read_text(encoding="utf-8").splitlines()
lines = a + b
if len(lines) != len(keys):
    raise SystemExit(f"Expected {len(keys)} fa lines, got {len(lines)}")
patch = {k: lines[i].strip() for i, k in enumerate(keys)}
out = ROOT / "static" / "federal_elections_options_fa_patch.json"
out.write_text(json.dumps(patch, ensure_ascii=False, indent=2), encoding="utf-8")
print("Wrote", out, len(patch), "entries")

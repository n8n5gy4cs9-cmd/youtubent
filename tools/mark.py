"""Mark tasks done: python tools/mark.py T01 T02  -> updates task.md and PRD.json"""
import json, re, sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
done_ids = set(sys.argv[1:])
lines = (root / "task.md").read_text().splitlines()
out, tasks = [], []
for l in lines:
    m = re.match(r"- \[( |x)\] (T\d+) (.*)", l)
    if m:
        d = m[1] == "x" or m[2] in done_ids
        l = f"- [{'x' if d else ' '}] {m[2]} {m[3]}"
        tasks.append({"id": m[2], "title": m[3], "done": d})
    out.append(l)
(root / "task.md").write_text("\n".join(out) + "\n")
prd = json.loads((root / "PRD.json").read_text())
prd["tasks"] = tasks
(root / "PRD.json").write_text(json.dumps(prd, indent=2) + "\n")
print(f"{sum(t['done'] for t in tasks)}/{len(tasks)} done")

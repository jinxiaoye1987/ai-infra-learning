"""收集 site/new/<m>w1..4.md 中尚未收录的链接，curl 校验后生成 add_refs 的 JSON。用法：python tools/month_refs.py m4 13 cat out.json"""
import re, json, subprocess, sys
m, base, defcat, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
have = set(re.findall(r"'(https?://[^']+)'", open("tools/refs.py").read()))
titles, weeks = {}, {}
for w in range(1, 5):
    for t, u in re.findall(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', open(f"site/new/{m}w{w}.md").read()):
        if u in have: continue
        weeks.setdefault(u, set()).add(base + w - 1); titles.setdefault(u, t)
rows = []
for u, t in titles.items():
    c = subprocess.run(["curl", "-s", "-o", "/dev/null", "-L", "-w", "%{http_code}", u], capture_output=True, text=True).stdout
    if c != "200": print("DROP", c, u); continue
    kind = "论文" if "arxiv.org" in u or "usenix.org" in u else ("仓库" if "github.com" in u else "文档")
    ws = sorted(weeks[u])
    rows.append([defcat, t, u, kind, "进阶", ws, "第 %s 周精读/实验参考" % "、".join(map(str, ws))])
json.dump(rows, open(out, "w"), ensure_ascii=False); print("new", len(rows))

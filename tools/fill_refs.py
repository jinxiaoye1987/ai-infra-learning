"""把 site/new/<slug>.md 中的 @@REFS@@ 替换为 content 里该周原有的“## 参考资料”段（保留资源标签与原条目）。用法：python tools/fill_refs.py slug"""
import sys, glob, re
slug = sys.argv[1]
for f in glob.glob("site/content/*.md"):
    c = open(f).read()
    m = re.search(r"^=== %s \|.*?(?=^=== |\Z)" % re.escape(slug), c, re.S | re.M)
    if m: sec = m.group(0); break
s = sec.index("## 参考资料"); e = sec.find("\n## ", s + 5)
refs = sec[s:e if e > 0 else len(sec)].rstrip() + "\n"
p = "site/new/%s.md" % slug; t = open(p).read()
assert "@@REFS@@" in t; open(p, "w").write(t.replace("@@REFS@@", refs)); print("refs filled", slug)

"""用 site/new/<slug>.md 替换 content/*.md 中同 slug 的页面块。"""
import glob, re, sys, pathlib
root = pathlib.Path(__file__).resolve().parent.parent / "site"
for slug in sys.argv[1:]:
    new = (root / "new" / f"{slug}.md").read_text().rstrip("\n") + "\n\n"
    # @@CODE:w5/tasks.py@@ → labs/w5/tasks.py 的原样内容（保证页面代码 = 实测代码）
    new = re.sub(r"@@CODE:([\w./-]+)@@", lambda m: (root.parent / "labs" / m.group(1)).read_text().rstrip("\n"), new)
    for f in sorted(glob.glob(str(root / "content" / "*.md"))):
        txt = open(f).read()
        parts = re.split(r"(?m)^(?==== )", txt)
        hit = [i for i, p in enumerate(parts) if p.startswith(f"=== {slug} |")]
        if hit:
            parts[hit[0]] = new
            open(f, "w").write("".join(parts).rstrip("\n") + "\n")
            print("spliced", slug, "into", f)
            break
    else:
        print("NOT FOUND", slug)

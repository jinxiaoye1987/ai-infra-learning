"""把新参考资料并入 refs.py 的 D 列表：URL 已存在则合并周次，否则追加。用法：python add_refs.py new_refs.json"""
import ast, json, pathlib, sys
p = pathlib.Path(__file__).with_name("refs.py")
src = p.read_text()
start = src.index("D=[")
end = src.index("\n]\n", start)
body = src[start + 3:end]
rows = [ast.literal_eval(l.strip().rstrip(",")) for l in body.splitlines() if l.strip().startswith("(")]
idx = {r[2]: i for i, r in enumerate(rows)}
for n in json.load(open(sys.argv[1])):
    n = tuple(n)
    if n[2] in idx:
        r = list(rows[idx[n[2]]]); r[5] = sorted(set(r[5]) | set(n[5])); rows[idx[n[2]]] = tuple(r)
    else:
        idx[n[2]] = len(rows); rows.append(n)
head = [l for l in body.splitlines() if l.strip().startswith("#")]
new_body = "\n" + "\n".join(head) + "\n" + "\n".join(repr(r) + "," for r in rows)
p.write_text(src[:start + 3] + new_body + src[end:])
print("rows", len(rows))

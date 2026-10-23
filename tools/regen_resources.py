"""用 refs.py page 的输出替换 90-ref.md 里的 resources 页面块。"""
import re, subprocess, pathlib
here = pathlib.Path(__file__).resolve().parent
f = here.parent / "site/content/90-ref.md"
page = subprocess.run(["python3", str(here / "refs.py"), "page"], capture_output=True, text=True, check=True).stdout
parts = re.split(r"(?m)^(?==== )", f.read_text())
i = next(i for i, p in enumerate(parts) if p.startswith("=== resources |"))
parts[i] = page.rstrip("\n") + "\n\n"
f.write_text("".join(parts))
print("resources regenerated")

"""博客发布前自查：检查草稿是否写明环境/版本、是否区分实测与估算、是否有图、是否有大数据类比、数字是否有单位。
用法：python blog_lint.py draft.md"""
import re, sys
t = open(sys.argv[1], encoding="utf-8").read()
checks = [
    ("写明硬件/环境", r"(GPU|CPU|显卡|A100|H100|L4|4090|核)"),
    ("写明软件版本", r"\b(v?\d+\.\d+(\.\d+)?)\b"),
    ("区分实测与估算", r"(实测|估算|假设)"),
    ("至少一张图", r"(!\[|```mermaid)"),
    ("有大数据类比", r"(Spark|YARN|Hive|Flink|Kafka|HDFS|MapReduce)"),
    ("有取舍/局限讨论", r"(取舍|局限|代价|不足|限制)"),
    ("给出复现方式", r"(```bash|仓库|github\.com)"),
]
ok = 0
for name, pat in checks:
    hit = re.search(pat, t, re.I); ok += bool(hit)
    print(f"[{'✓' if hit else '✗'}] {name}" + (f"（例：{hit.group(0)}）" if hit else ""))
bare = re.findall(r"(?<![\w.])\d{3,}(?![\w.%])(?!\s*(ms|s|GB|MB|tok|token|篇|条|行|个|张|卡|倍|字|次|元))", t)
print(f"疑似缺少单位的数字：{len(bare)} 处")
print(f"通过 {ok}/{len(checks)} 项")

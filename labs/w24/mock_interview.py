"""离线模拟面试：随机抽题，先自己作答（口述或写下），再对照要点自评。
用法：python mock_interview.py --n 3 --seed 1        （--show 直接显示要点，用于复习）"""
import argparse, json, random
p = argparse.ArgumentParser(); p.add_argument("--n", type=int, default=3); p.add_argument("--seed", type=int, default=None)
p.add_argument("--show", action="store_true"); p.add_argument("--topic", default=None); a = p.parse_args()
qs = json.load(open("questions.json", encoding="utf-8"))
if a.topic: qs = [q for q in qs if q["topic"] == a.topic]
random.seed(a.seed); pick = random.sample(qs, min(a.n, len(qs)))
for i, q in enumerate(pick, 1):
    print(f"\n第 {i} 题【{q['topic']}】{q['q']}")
    if not a.show: input("  （作答后按回车查看要点）")
    print("  要点：" + "；".join(q["points"]))
    print(f"  复习：{q['ref']}  自评：命中 __/{len(q['points'])} 个要点")

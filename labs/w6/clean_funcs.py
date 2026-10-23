"""清洗规则：Ray 版与 pandas 版共用。"""
import re

import numpy as np
import pandas as pd

TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"[ \t]+")
STOP = {"the", "be", "to", "of", "and", "that", "have", "with"}   # Gopher 论文的 8 个停用词


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """去 HTML 标签、压缩空白、去掉空行。"""
    def one(t: str) -> str:
        t = TAG.sub(" ", t)
        lines = [WS.sub(" ", l).strip() for l in t.splitlines()]
        return "\n".join(l for l in lines if l)
    df["text"] = df["text"].map(one)
    return df


def quality(df: pd.DataFrame) -> pd.DataFrame:
    """为每行打上 reason（为空表示通过），不在这里删行，方便统计每条规则的命中数。"""
    reasons = []
    for t in df["text"]:
        words = t.split()
        n = len(words)
        lines = t.splitlines() or [""]
        alpha_words = sum(any(c.isalpha() for c in w) for w in words)
        if n < 50:
            r = "too_short"                                   # Gopher：少于 50 词
        elif n > 100_000:
            r = "too_long"
        elif not 3 <= np.mean([len(w) for w in words]) <= 10:
            r = "avg_word_len"                               # 平均词长不在 3–10
        elif alpha_words / n < 0.8:
            r = "non_alpha"                                  # 含字母的词不足 80%
        elif len(STOP & {w.lower() for w in words}) < 2:
            r = "few_stop_words"                             # 英文停用词少于 2 个（兼作粗糙的语言过滤）
        elif 1 - len(set(lines)) / len(lines) > 0.3:
            r = "dup_lines"                                  # 重复行占比 > 30%（Gopher 重复规则的简化版）
        else:
            r = ""
        reasons.append(r)
    df["reason"] = reasons
    return df

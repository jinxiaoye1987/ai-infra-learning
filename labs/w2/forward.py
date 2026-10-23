"""跟踪 GPT-2 一次前向：每一步的张量形状，以及下一个 token 的概率。"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

tok = AutoTokenizer.from_pretrained("openai-community/gpt2")
m = AutoModelForCausalLM.from_pretrained("openai-community/gpt2").eval()
ids = tok("SELECT count(*) FROM", return_tensors="pt").input_ids
print("① token id:", ids.tolist(), "->", [tok.decode([i]) for i in ids[0]])
with torch.no_grad():
    pos = torch.arange(ids.shape[1])
    h = m.transformer.wte(ids) + m.transformer.wpe(pos)          # 词向量 + 位置向量
    print("② embedding 后:", tuple(h.shape))
    for i, blk in enumerate(m.transformer.h):
        out = blk(h)
        h = out[0] if isinstance(out, tuple) else out   # 不同 transformers 版本返回 tuple 或 Tensor
        if i in (0, 11):
            print(f"③ 第 {i:>2} 个 Block 后:", tuple(h.shape))
    h = m.transformer.ln_f(h)
    logits = m.lm_head(h)                                        # 投影回词表
    print("④ logits:", tuple(logits.shape))
    p = logits[0, -1].softmax(-1)
    top = p.topk(5)
    print("⑤ 下一个 token 候选:", [(tok.decode([int(i)]), round(float(v), 3)) for v, i in zip(top.values, top.indices)])
    ref = m(ids).logits
    print("与 model(ids) 直接调用的最大误差:", float((ref - logits).abs().max()))

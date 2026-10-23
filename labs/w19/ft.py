# ft.py —— HF Trainer + PEFT LoRA 微调；可选 --deepspeed 配置；指标写入 MLflow
# 本地 CPU 调通：python ft.py --steps 15        多卡：deepspeed --num_gpus 2 ft.py --deepspeed ds_z2.json
import argparse, time, torch, mlflow
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model
p = argparse.ArgumentParser()
p.add_argument("--model", default="Qwen/Qwen2.5-0.5B"); p.add_argument("--steps", type=int, default=100)
p.add_argument("--deepspeed", default=None); p.add_argument("--data", default="../w7/input/part-0.parquet")
p.add_argument("--run-name", default=None); p.add_argument("--max-len", type=int, default=128)
p.add_argument("--lora-r", type=int, default=16); p.add_argument("--save", default=None)   # 保存 LoRA adapter 的目录
a = p.parse_args()
cuda = torch.cuda.is_available()
tok = AutoTokenizer.from_pretrained(a.model); tok.pad_token = tok.pad_token or tok.eos_token
model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16 if cuda else torch.float32)
model = get_peft_model(model, LoraConfig(r=a.lora_r, lora_alpha=2 * a.lora_r, target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM"))
model.print_trainable_parameters()
ds = load_dataset("parquet", data_files=a.data, split="train").select(range(2000))   # 第 7 周的语料样本
ds = ds.map(lambda b: tok(b["text"], truncation=True, max_length=a.max_len), batched=True, remove_columns=ds.column_names)
mlflow.set_experiment("finetune")
args = TrainingArguments(output_dir="out", per_device_train_batch_size=2 if not cuda else 4, max_steps=a.steps,
                         bf16=cuda, logging_steps=5, report_to=["mlflow"], run_name=a.run_name,
                         save_strategy="no", deepspeed=a.deepspeed)
t = time.perf_counter()
tr = Trainer(model=model, args=args, train_dataset=ds, data_collator=DataCollatorForLanguageModeling(tok, mlm=False)); tr.train()
if a.save: model.save_pretrained(a.save)
dt = time.perf_counter() - t
print(f"总耗时 {dt:.1f}s，每步 {dt/a.steps:.2f}s，峰值显存 GB: " + (f"{torch.cuda.max_memory_allocated()/1e9:.1f}" if cuda else "n/a (CPU)"))

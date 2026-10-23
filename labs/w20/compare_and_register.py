# compare_and_register.py —— 用 API 对比第 19 周的微调 run，把 loss 最低的 LoRA adapter 登记为模型版本并打上别名
import mlflow, mlflow.pyfunc
from mlflow import MlflowClient
cli = MlflowClient()
exp = cli.get_experiment_by_name("finetune")
runs = cli.search_runs([exp.experiment_id], filter_string="attributes.run_name LIKE 'lora-r%'",
                       order_by=["metrics.train_loss ASC"])
print(f"{'run_name':<10} {'lora_r':>6} {'train_loss':>10} {'runtime_s':>9}")
for r in runs:
    print(f"{r.info.run_name:<10} {r.info.run_name.split('-r')[-1]:>6} "
          f"{r.data.metrics['train_loss']:>10.4f} {r.data.metrics['train_runtime']:>9.2f}")
best = runs[0]; rr = best.info.run_name.split('-r')[-1]   # Trainer 不会记录 PEFT 的 r，这里从 run 名解析

class Adapter(mlflow.pyfunc.PythonModel):              # 最小包装：登记 adapter 目录，推理时由服务加载
    def predict(self, context, model_input): return [context.artifacts["adapter"]] * len(model_input)

with mlflow.start_run(run_id=best.info.run_id):
    info = mlflow.pyfunc.log_model(name="lora_adapter", python_model=Adapter(),
                                   artifacts={"adapter": f"../w19/adapter-r{rr}"})
mv = mlflow.register_model(info.model_uri, "qwen2.5-0.5b-lora")
cli.set_registered_model_alias("qwen2.5-0.5b-lora", "champion", mv.version)
m = cli.get_model_version_by_alias("qwen2.5-0.5b-lora", "champion")
print(f"已登记 qwen2.5-0.5b-lora 版本 {m.version}，别名 champion → 来源 run {m.run_id[:8]}（{best.info.run_name}）")

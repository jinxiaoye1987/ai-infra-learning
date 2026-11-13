# 第 19 周实验产物

可复现的步骤和配置仍在本目录：

- `shard_compare.py`：DDP 与 FSDP 的 CPU 对比
- `ft.py`：LoRA 微调，并把指标写入 MLflow
- `ds_z2.json`、`ds_z3.json`：DeepSpeed 配置
- `adapter-r4/adapter_config.json`、`adapter-r16/adapter_config.json`：当时 PEFT 写出的超参

`adapter-r4/README.md` 和 `adapter-r16/README.md` 是 PEFT 生成的未填写模型卡模板。

当前 Git 树不收录 LoRA 权重（`*.safetensors`）、`*.pkl` 和 `mlruns/`。这些是实验产物，不是阅读课程所必需的源文件。需要权重时，按第 19 周正文准备依赖和数据，再运行 `ft.py` 的 `--save` 重新生成。多卡 DeepSpeed 步骤在正文中标为未在本站实测。

配置里的基座名称是 `Qwen/Qwen2.5-0.5B`。使用该模型前阅读其作者发布的模型卡。本目录的文件不构成对该模型的再授权。

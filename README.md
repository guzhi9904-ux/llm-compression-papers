# LLM Compression Papers

这个仓库用来存放已经看过或准备阅读的 LLM compression 论文。代码放在另一个仓库，这里只放论文和清单。

目前共有 77 篇：

- 69 篇来自本地 `LLM Compress` 目录，标记为“已读”。
- 8 篇从 ICLR、ICML、NeurIPS 或 arXiv 页面补充，标记为“待读”。
- 相同 PDF 按 SHA256 去重，只保留一份。

## 分类

```text
papers/
├── PTQ/
│   ├── fp4_and_microscaling/
│   ├── gptq_and_rounding/
│   ├── rotation_and_transform/
│   ├── smoothing/
│   └── other/
├── QAT/
├── Quantized_finetuning/
├── KV_cache/
├── Reasoning_and_serving/
└── Related/
    ├── compression/
    ├── interpretability/
    └── quantization_theory/
```

分类按论文主要内容来定。例如 PV-Tuning 放在 `QAT`，QLoRA 和 QDPO 放在 `Quantized_finetuning`，MicroMix 和 MR-GPTQ 放在 `PTQ/fp4_and_microscaling`。

## 各类论文主要在看什么

### PTQ

PTQ 不重新训练整个模型，重点是怎样用少量 calibration 数据把量化误差压下来。

- [GPTQ](<papers/PTQ/gptq_and_rounding/OPTQ.pdf>) 用近似二阶信息决定 weight 的量化顺序，并把当前列的误差补到后面的列。
- [SmoothQuant](<papers/PTQ/smoothing/SmoothQuant.pdf>) 把 activation 上难量化的 outlier 部分转移到 weight，主要解决 W8A8。
- [QuaRot](papers/PTQ/rotation_and_transform/QuaRot.pdf) 用等价旋转打散 outlier；DuQuant、SpinQuant、OSTQuant 和 FlatQuant 继续沿着 rotation、scaling、permutation 和可学习变换往下做。
- [MR-GPTQ](papers/PTQ/fp4_and_microscaling/MR-GPTQ.pdf) 和 [MicroMix](papers/PTQ/fp4_and_microscaling/MicroMix.pdf) 开始直接围绕 MXFP4、NVFP4 和 Blackwell kernel 设计方法。

### QAT 和 quantized fine-tuning

当 bit 数降到 1-2 bit，或者 PTQ 很难保住任务性能时，就需要少量训练。

- [LLM-QAT](papers/QAT/LLM-QAT.pdf) 用模型自己生成的数据做 distillation，同时量化 weight、activation 和 KV cache。
- [PV-Tuning](papers/QAT/PV-Tuning.pdf) 关注极低 bit 下怎样比普通 STE fine-tuning 做得更稳。
- QLoRA 和 QDPO 更偏向量化模型上的下游训练或偏好对齐，不和纯 PTQ 混在一起。

### KV cache 和推理

- [KVQuant](papers/KV_cache/KVQuant.pdf) 处理长上下文下 KV cache 占用过大的问题。
- [CommVQ](papers/KV_cache/CommVQ.pdf) 用和 RoPE 相容的 codebook 压缩 KV cache，目标是让低 bit 表示更容易接进 attention。
- reasoning 目录关注量化以后推理能力掉在哪里，而不只是看 WikiText2 PPL。

## 研究路线

一条从基础 PTQ 到 FP4 和真实推理的阅读、实验顺序见 [`docs/research_route.md`](docs/research_route.md)。

## 论文清单

- [`manifests/papers.csv`](manifests/papers.csv)：全部论文，包含分类、会议、年份、PDF 路径、来源、SHA256、阅读状态和代码链接。
- [`manifests/conference_2023_2026.csv`](manifests/conference_2023_2026.csv)：只保留 ICLR、ICML、NeurIPS 2023-2026 的论文。

会议和年份只在已经核实的情况下填写，空白不表示没有发表，只表示这次还没有确认。

## 只下载某一类论文

普通 `git clone` 会下载整个仓库。如果只需要 PTQ，可以使用 sparse checkout：

```bash
git clone --filter=blob:none --sparse \
  https://github.com/guzhi9904-ux/llm-compression-papers.git

cd llm-compression-papers
git sparse-checkout set papers/PTQ manifests
```

只需要 QAT：

```bash
git sparse-checkout set papers/QAT manifests
```

需要全部论文时执行：

```bash
git sparse-checkout disable
```

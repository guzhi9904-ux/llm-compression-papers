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

## 论文清单

- [`manifests/papers.csv`](manifests/papers.csv)：全部论文，包含分类、会议、年份、PDF 路径、来源、SHA256、阅读状态和代码链接。
- [`manifests/conference_2023_2026.csv`](manifests/conference_2023_2026.csv)：只保留 ICLR、ICML、NeurIPS 2023-2026 的论文。

会议和年份只在已经核实的情况下填写，空白不表示没有发表，只表示这次还没有确认。

## 这次从会议页面补的论文

| 论文 | 会议 | 分类 |
|---|---|---|
| AQLM | ICML 2024 | PTQ |
| QuIP# | ICML 2024 | PTQ |
| SqueezeLLM | ICML 2024 | PTQ |
| PV-Tuning | NeurIPS 2024 | QAT |
| GuidedQuant | ICML 2025 | PTQ |
| CommVQ | ICML 2025 | KV cache |
| Q-Palette | NeurIPS 2025 | PTQ |
| GPTQ as Babai's Nearest Plane Algorithm | ICLR 2026 | PTQ |

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

## 整理脚本

`tools/inventory_local.py` 扫描本地 PDF 并计算 SHA256，`tools/import_local_papers.py` 负责去重、分类和生成 CSV。脚本不会修改原始 PDF。

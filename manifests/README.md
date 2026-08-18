# 清单说明

`papers.csv` 的字段：

| 字段 | 含义 |
|---|---|
| `title` | 论文标题 |
| `category` | 仓库分类 |
| `venue`、`year` | 已核实的会议和年份 |
| `pdf_path` | 仓库中的 PDF 路径 |
| `local_source` | 原文件在 `LLM Compress` 下的相对路径；网络补充论文为空 |
| `sha256` | 用于检查重复文件 |
| `paper_url` | 会议或论文页面 |
| `code_url` | 论文代码地址 |
| `read_status` | `已读` 或 `待读` |
| `notes_zh` | 简短备注 |

`conference_2023_2026.csv` 从总清单中筛选 ICLR、ICML 和 NeurIPS 2023-2026 论文生成。

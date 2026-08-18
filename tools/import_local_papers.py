"""把本地论文去重后复制到仓库，并生成论文清单。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path


# 同一个 PDF 在多个目录出现时，优先保留文件名和分类更准确的这一份。
PREFERRED_SOURCES = {
    "FP4/MicroMix.pdf",
    "PTQ/HeRo-Q.pdf",
    "QAT/EfficientQAT.pdf",
    "Scaling Laws for Precision.pdf",
    "quant/CBQ.pdf",
    "quant/QuaRot.pdf",
}

# GPTQ.pdf 是匿名评审稿，OPTQ.pdf 是同一工作的正式版本。
SKIPPED_SOURCES = {"quant/GPTQ.pdf"}

TITLE_OVERRIDES = {
    "2752_outlier_suppression_pushing_th.pdf": "Outlier Suppression: Pushing the Limit of Low-bit Transformer Language Models",
    "5654_SliceGPT_Compress_Large_L.pdf": "SliceGPT: Compress Large Language Models by Deleting Rows and Columns",
    "ACBQ.pdf": "ACBQ: Adaptive Cross-Block Quantization of Large Language Models",
    "FP4/LLM-fp4.pdf": "LLM-FP4: 4-Bit Floating-Point Quantized Transformers",
    "FP4/MicroMix.pdf": "MicroMix: Efficient Mixed-Precision Quantization with Microscaling Formats for Large Language Models",
    "FP4/MR-GPTQ.pdf": "Bridging the Gap Between Promise and Performance for Microscaling FP4 Quantization",
    "FP4/MXFP4.pdf": "Microscaling Data Formats for Deep Learning",
    "FP4/TAGQuant.pdf": "TAGQuant: Token-Aware Clustering for Group-Wise Quantization",
    "KV/19321_KV_Cache_Transform_Codin.pdf": "KV Cache Transform Coding for Compact Storage in LLM Inference",
    "KV/20146_Cache_What_Lasts_Token_R.pdf": "Cache What Lasts: Token Retention for Memory-Bounded KV Cache in LLMs",
    "KV/KVQuant.pdf": "KVQuant: Towards 10 Million Context Length LLM Inference with KV Cache Quantization",
    "KV/SnapKV.pdf": "SnapKV: LLM Knows What You Are Looking for before Generation",
    "Optimal Brain Compression.pdf": "Optimal Brain Compression: A Framework for Accurate Post-Training Quantization and Pruning",
    "PTQ/DuQuant.pdf": "DuQuant: Distributing Outliers via Dual Transformation Makes Stronger Quantized LLMs",
    "PTQ/OSTQuant.pdf": "OSTQuant: Refining Large Language Model Quantization with Orthogonal and Scaling Transformations",
    "PTQ/ParetoQ.pdf": "ParetoQ: Improving Scaling Laws in Extremely Low-bit LLM Quantization",
    "PTQ/QDPO.pdf": "Improving Conversational Abilities of Quantized Large Language Models via Direct Preference Alignment",
    "PTQ/QEP.pdf": "Quantization Error Propagation: Revisiting Layer-Wise Post-Training Quantization",
    "PTQ/RPTQ.pdf": "RPTQ: Reorder-based Post-training Quantization for Large Language Models",
    "PTQ/SPQR.pdf": "SpQR: A Sparse-Quantized Representation for Near-Lossless LLM Weight Compression",
    "QLoRA.pdf": "QLoRA: Efficient Finetuning of Quantized LLMs",
    "quant/1923_Outlier_Suppression_Accur.pdf": "Outlier Suppression+: Accurate Quantization of Large Language Models by Equivalent Shifting and Scaling",
    "quant/AFFINEQUANT.pdf": "AffineQuant: Affine Transformation Quantization for Large Language Models",
    "quant/BRECQ.pdf": "BRECQ: Pushing the Limit of Post-Training Quantization by Block Reconstruction",
    "quant/CBQ.pdf": "CBQ: Cross-Block Quantization for Large Language Models",
    "quant/EfficientQAT.pdf": "EfficientQAT: Efficient Quantization-Aware Training for Large Language Models",
    "quant/LLM-QAT.pdf": "LLM-QAT: Data-Free Quantization Aware Training for Large Language Models",
    "quant/LLM.int8().pdf": "LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale",
    "quant/OmniQuant.pdf": "OmniQuant: Omnidirectionally Calibrated Quantization for Large Language Models",
    "quant/OPTQ.pdf": "GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers",
    "quant/QDrop.pdf": "QDrop: Randomly Dropping Quantization for Extremely Low-Bit Post-Training Quantization",
    "quant/QTIP.pdf": "QTIP: Quantization with Trellises and Incoherence Processing",
    "quant/QuaRot.pdf": "QuaRot: Outlier-Free 4-Bit Inference in Rotated LLMs",
    "quant/QuIP.pdf": "QuIP: 2-Bit Quantization of Large Language Models With Guarantees",
    "quant/SliderQuant.pdf": "SliderQuant: Accurate Post-Training Quantization for LLMs",
    "quant/SpinQuant.pdf": "SpinQuant: LLM Quantization with Learned Rotations",
    "resoning/REASONING LANGUAGE MODEL INFERENCE SERVING.pdf": "Reasoning Language Model Inference Serving Unveiled: An Empirical Study",
    "resoning/When_Reasoning_Meets_Com.pdf": "When Reasoning Meets Compression: Understanding the Effects of LLM Compression on Large Reasoning Models",
    "Scaling Laws for Precision.pdf": "Scaling Laws for Precision",
}

STEM_OVERRIDES = {
    "2752_outlier_suppression_pushing_th.pdf": "Outlier Suppression",
    "5654_SliceGPT_Compress_Large_L.pdf": "SliceGPT",
    "KV/19321_KV_Cache_Transform_Codin.pdf": "KV Cache Transform Coding",
    "KV/20146_Cache_What_Lasts_Token_R.pdf": "Cache What Lasts",
    "quant/1923_Outlier_Suppression_Accur.pdf": "Outlier Suppression Plus",
    "quant/9338_CBQ_Cross_Block_Quantizat.pdf": "CBQ",
    "quant/FPTQuant_.pdf": "FPTQuant",
}

VENUE_OVERRIDES = {
    "GPTQ": ("ICLR", "2023"),
    "SmoothQuant": ("ICML", "2023"),
    "QLoRA": ("NeurIPS", "2023"),
    "QuIP": ("NeurIPS", "2023"),
    "OmniQuant": ("ICLR", "2024"),
    "AffineQuant": ("ICLR", "2024"),
    "SliceGPT": ("ICLR", "2024"),
    "SpQR": ("ICLR", "2024"),
    "QuaRot": ("NeurIPS", "2024"),
    "DuQuant": ("NeurIPS", "2024"),
    "QTIP": ("NeurIPS", "2024"),
    "KVQuant": ("NeurIPS", "2024"),
    "SpinQuant": ("ICLR", "2025"),
    "OSTQuant": ("ICLR", "2025"),
    "CBQ": ("ICLR", "2025"),
    "Scaling Laws for Precision": ("ICLR", "2025"),
    "FlatQuant": ("ICML", "2025"),
    "ParetoQ": ("NeurIPS", "2025"),
    "MR-GPTQ": ("ICLR", "2026"),
    "MicroMix": ("ICLR", "2026"),
    "SliderQuant": ("ICLR", "2026"),
    "ParoQuant": ("ICLR", "2026"),
    "MixFP4": ("ICML", "2026"),
}

WEB_PAPERS = (
    {
        "title": "Extreme Compression of Large Language Models via Additive Quantization (AQLM)",
        "category": "PTQ/other",
        "venue": "ICML",
        "year": "2024",
        "pdf_path": "papers/PTQ/other/AQLM.pdf",
        "paper_url": "https://proceedings.mlr.press/v235/egiazarian24a.html",
        "code_url": "https://github.com/Vahe1994/AQLM",
    },
    {
        "title": "QuIP#: Even Better LLM Quantization with Hadamard Incoherence and Lattice Codebooks",
        "category": "PTQ/other",
        "venue": "ICML",
        "year": "2024",
        "pdf_path": "papers/PTQ/other/QuIP-Sharp.pdf",
        "paper_url": "https://proceedings.mlr.press/v235/tseng24a.html",
        "code_url": "https://github.com/Cornell-RelaxML/quip-sharp",
    },
    {
        "title": "SqueezeLLM: Dense-and-Sparse Quantization",
        "category": "PTQ/other",
        "venue": "ICML",
        "year": "2024",
        "pdf_path": "papers/PTQ/other/SqueezeLLM.pdf",
        "paper_url": "https://proceedings.mlr.press/v235/kim24f.html",
        "code_url": "https://github.com/SqueezeAILab/SqueezeLLM",
    },
    {
        "title": "PV-Tuning: Beyond Straight-Through Estimation for Extreme LLM Compression",
        "category": "QAT",
        "venue": "NeurIPS",
        "year": "2024",
        "pdf_path": "papers/QAT/PV-Tuning.pdf",
        "paper_url": "https://proceedings.neurips.cc/paper_files/paper/2024/hash/091166620a04a289c555f411d8899049-Abstract-Conference.html",
        "code_url": "https://github.com/Vahe1994/AQLM",
    },
    {
        "title": "CommVQ: Commutative Vector Quantization for KV Cache Compression",
        "category": "KV_cache",
        "venue": "ICML",
        "year": "2025",
        "pdf_path": "papers/KV_cache/CommVQ.pdf",
        "paper_url": "https://proceedings.mlr.press/v267/li25du.html",
        "code_url": "https://github.com/UMass-Embodied-AGI/CommVQ",
    },
    {
        "title": "GuidedQuant: Large Language Model Quantization via Exploiting End Loss Guidance",
        "category": "PTQ/gptq_and_rounding",
        "venue": "ICML",
        "year": "2025",
        "pdf_path": "papers/PTQ/gptq_and_rounding/GuidedQuant.pdf",
        "paper_url": "https://proceedings.mlr.press/v267/kim25d.html",
        "code_url": "https://github.com/snu-mllab/GuidedQuant",
    },
    {
        "title": "Q-Palette: Fractional-Bit Quantizers Toward Optimal Bit Allocation for Efficient LLM Deployment",
        "category": "PTQ/other",
        "venue": "NeurIPS",
        "year": "2025",
        "pdf_path": "papers/PTQ/other/Q-Palette.pdf",
        "paper_url": "https://proceedings.neurips.cc/paper_files/paper/2025/hash/10df8641edc837ca49360d5fb1d182f0-Abstract-Conference.html",
        "code_url": "https://github.com/snu-mllab/Q-Palette",
    },
    {
        "title": "The Geometry of LLM Quantization: GPTQ as Babai's Nearest Plane Algorithm",
        "category": "PTQ/gptq_and_rounding",
        "venue": "ICLR",
        "year": "2026",
        "pdf_path": "papers/PTQ/gptq_and_rounding/The Geometry of LLM Quantization - GPTQ as Babai's Nearest Plane Algorithm.pdf",
        "paper_url": "https://openreview.net/forum?id=NFB4QGGS65",
        "code_url": "",
    },
)


def short_name(title: str) -> str:
    return title.split(":", 1)[0].strip()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def choose_record(group: list[dict[str, object]]) -> dict[str, object]:
    preferred = [item for item in group if item["relative_path"] in PREFERRED_SOURCES]
    return preferred[0] if preferred else group[0]


def category_for(relative_path: str, title: str) -> str:
    lower = title.lower()
    if relative_path.startswith("KV/"):
        return "KV_cache"
    if any(key in lower for key in ("qlora", "preference alignment")):
        return "Quantized_finetuning"
    if relative_path.startswith(("QAT/", "QAD/")) or any(
        key in lower for key in ("qat", "distillation")
    ):
        return "QAT"
    if relative_path.startswith("resoning/"):
        return "Reasoning_and_serving"
    if any(key in lower for key in ("circuit discovery", "tuned lens")):
        return "Related/interpretability"
    if any(key in lower for key in ("diffusion models", "slicegpt", "pruning")):
        return "Related/compression"
    if "scaling laws for precision" in lower:
        return "Related/quantization_theory"
    if relative_path.startswith("FP4/") or any(
        key in lower for key in ("mxfp", "nvfp4", "microscaling", "fp4")
    ):
        return "PTQ/fp4_and_microscaling"
    if any(
        key in lower
        for key in (
            "quarot",
            "spinquant",
            "duquant",
            "ostquant",
            "flatquant",
            "affinequant",
            "omniquant",
            "paroquant",
            "fptquant",
            "closed-form rotations",
            "outlier separation",
        )
    ):
        return "PTQ/rotation_and_transform"
    if any(key in lower for key in ("smoothquant", "outlier suppression")):
        return "PTQ/smoothing"
    if any(
        key in lower
        for key in (
            "gptq",
            "adaptive rounding",
            "flexround",
            "qdrop",
            "brecq",
            "optimal brain",
            "model-preserving adaptive rounding",
            "final-block quantization",
        )
    ):
        return "PTQ/gptq_and_rounding"
    return "PTQ/other"


def title_for(record: dict[str, object]) -> str:
    relative_path = str(record["relative_path"])
    if relative_path in TITLE_OVERRIDES:
        return TITLE_OVERRIDES[relative_path]
    metadata_title = str(record.get("metadata_title") or "").strip()
    return metadata_title or Path(relative_path).stem.replace("_", " ")


def safe_filename(record: dict[str, object], title: str) -> str:
    relative_path = str(record["relative_path"])
    stem = STEM_OVERRIDES.get(relative_path, Path(relative_path).stem)
    if re.fullmatch(r"[\d_]+", stem):
        stem = short_name(title)
    stem = re.sub(r'[<>:"/\\|?*]+', "_", stem).strip(" .")
    return f"{stem}.pdf"


def venue_for(record: dict[str, object], title: str) -> tuple[str, str]:
    name = short_name(title)
    if name in VENUE_OVERRIDES:
        return VENUE_OVERRIDES[name]
    first_page = " ".join(record.get("first_page_lines") or [])
    match = re.search(r"conference paper at (ICLR) (20\d{2})", first_page, re.I)
    if match:
        return match.group(1).upper(), match.group(2)
    return "", ""


def main() -> None:
    parser = argparse.ArgumentParser(description="整理本地论文")
    parser.add_argument("inventory", type=Path)
    parser.add_argument("repo_root", type=Path)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    records = json.loads(args.inventory.read_text(encoding="utf-8"))
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        if record["relative_path"] not in SKIPPED_SOURCES:
            groups[str(record["sha256"])].append(record)

    rows: list[dict[str, str]] = []
    used_destinations: set[Path] = set()
    for digest, group in sorted(groups.items()):
        record = choose_record(group)
        title = title_for(record)
        category = category_for(str(record["relative_path"]), title)
        destination = Path("papers") / category / safe_filename(record, title)
        if destination in used_destinations:
            destination = destination.with_stem(
                f"{destination.stem}_{digest[:8]}"
            )
        used_destinations.add(destination)
        target = repo_root / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(record["source_path"], target)
        venue, year = venue_for(record, title)
        rows.append(
            {
                "title": title,
                "category": category,
                "venue": venue,
                "year": year,
                "pdf_path": destination.as_posix(),
                "local_source": str(record["relative_path"]),
                "sha256": digest,
                "paper_url": "",
                "code_url": "",
                "read_status": "已读",
                "notes_zh": "本地已有",
            }
        )

    for paper in WEB_PAPERS:
        pdf_path = repo_root / paper["pdf_path"]
        if not pdf_path.exists():
            continue
        rows.append(
            {
                **paper,
                "local_source": "",
                "sha256": file_sha256(pdf_path),
                "read_status": "待读",
                "notes_zh": "从会议或 arXiv 页面补充",
            }
        )

    manifest = repo_root / "manifests" / "papers.csv"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda item: (item["category"], item["title"])))

    conference_manifest = repo_root / "manifests" / "conference_2023_2026.csv"
    conference_rows = [
        row
        for row in rows
        if row["venue"] in {"ICLR", "ICML", "NeurIPS"}
        and row["year"] in {"2023", "2024", "2025", "2026"}
    ]
    with conference_manifest.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(
            sorted(conference_rows, key=lambda item: (item["year"], item["venue"], item["title"]))
        )
    print(
        f"已整理 {len(rows)} 篇论文，其中三大会 2023-2026 共 {len(conference_rows)} 篇"
    )


if __name__ == "__main__":
    main()

# LLM 量化研究路线

这条路线不是严格按年份分的。后面的工作通常是在补前面方法暴露出来的问题：先解决 weight，再处理 activation outlier，然后进入 4 bit 计算和 FP4，最后看低 bit 训练、KV cache 和真实推理。

```text
RTN / GPTQ / SmoothQuant
        ↓
2-3 bit weight-only
        ↓
W4A4 rotation 和等价变换
        ↓
FP4 / microscaling / mixed precision
        ↓
QAT 和少量 fine-tuning
        ↓
KV cache、reasoning、kernel 和端到端速度
```

## 第一阶段：先把 PTQ 基线做清楚

### 研究重点

先弄清楚最基本的量化误差从哪里来：group size、scale、clipping、calibration 数据和 weight 的量化顺序分别影响什么。

### 动机

直接 RTN 很简单，但低 bit 下误差会在层间不断积累。GPTQ 用输入的二阶信息判断哪些方向更敏感；SmoothQuant 则处理 activation outlier，让 W8A8 真正能跑起来。

### 主要方法

- RTN：作为最基本的舍入结果。
- GPTQ：逐列量化，并把误差补到还没有量化的列。
- SmoothQuant：用等价 scaling 把 activation 的量化难度转到 weight。

这一阶段先看 GPTQ 和 SmoothQuant，实验上至少固定模型、calibration 数据、sequence length、group size 和 evaluation 版本。后面的改进都要和这两条基线比较。

## 第二阶段：把 weight 压到 2-3 bit

### 研究重点

4 bit weight-only 已经比较成熟，继续往下压时，单个 weight 独立量化很快碰到上限。这一阶段主要看 weight 应该怎样成组表示，以及怎样利用更好的 codebook。

### 动机

小 batch decoding 往往受显存带宽限制，weight 越小，单卡能放下的模型越大。但 2 bit 只有很少的取值，普通均匀量化很难保住精度。

### 主要方法

- QuIP、QuIP#：先用正交变换减小 weight 和 Hessian 的不均匀，再做低 bit 量化。
- AQLM：一个 weight block 由多个 codebook 的结果相加得到。
- SqueezeLLM：把大部分 weight 做低 bit 量化，把 outlier 和敏感值单独保存。
- QTIP：用 trellis codebook 避免普通 vector quantization 的 codebook 随维度快速变大。
- Q-Palette：准备多种 bit 数和量化器，再按层选择。

这里不要只看模型大小，还要看解码 kernel。表示方法很复杂但没有高效 kernel，最终不一定比普通 4 bit 更快。

## 第三阶段：从 weight-only 走到 W4A4

### 研究重点

W4A4 的主要问题不是 weight，而是 activation 中少量特别大的值。研究重点变成怎样在不改变模型输出的前提下，把这些 outlier 打散或移走。

### 动机

weight 可以离线慢慢量化，activation 每次推理都会变化。activation 一旦保留高精度，4 bit Tensor Core 的收益就很难吃满。

### 主要方法

- OmniQuant：学习 clipping 和等价变换参数。
- AffineQuant、FlatQuant：把 scaling、shifting 或更一般的 affine transform 放进每层。
- QuaRot：用 Hadamard rotation 打散 hidden state、activation 和 KV cache 的 outlier。
- SpinQuant：不再只用随机 rotation，而是直接学习 rotation。
- DuQuant：rotation 之后再做 permutation，处理特别大的 activation outlier。
- OSTQuant：把 orthogonal transform 和 scaling 放在一起优化。

这一阶段适合做统一对照：保持 quantizer、group size 和 calibration 数据不变，只替换 transformation。否则很难判断提升到底来自 rotation，还是来自 scale 和 clipping 的变化。

## 第四阶段：进入 FP4 和 microscaling

### 研究重点

INT4 只关心整数网格，MXFP4 和 NVFP4 还要同时处理 exponent、mantissa、block scale 和 tensor scale。方法必须和具体格式一起设计。

### 动机

Blackwell 开始直接支持 FP4 Tensor Core，但“硬件支持 FP4”不等于模型直接转成 FP4 就会更准。小 block 共用 scale 后，scale 误差、block 内分布和格式选择都会影响结果。

### 主要方法

- 基线：分别实现 MXFP4/NVFP4 的 RTN、GPTQ 和 rotation，不能只写一个笼统的 FP4 baseline。
- MR-GPTQ：把 MSE scale、Hadamard rotation 和 GPTQ error compensation 合在一起，重点改善 MXFP4。
- MicroMix：按 channel 混用 MXFP4、MXFP6 和 MXFP8，并配套 mixed-precision kernel。
- MixFP4：在 NVFP4 block 内选择 E2M1 或 E1M2，尽量不增加额外 metadata。
- DuQuant++、TORQ、Block Rotation：继续研究怎样让 rotation 更适合小 block FP4。

这里最值得拆开的三个问题是：format 本身的误差、rotation 带来的变化、mixed precision 带来的变化。三者混在一个实验里，很难知道方法为什么有效。

## 第五阶段：PTQ 不够时再做 QAT

### 研究重点

当 1-2 bit、W4A4 或 reasoning model 上的 PTQ 明显掉点时，用少量训练把量化误差补回来。

### 动机

PTQ 的优点是便宜，但它不能改模型参数。bit 越低，这个限制越明显。QAT 能让模型适应量化网格，代价是数据、显存和训练时间都会增加。

### 主要方法

- LLM-QAT：用 teacher 生成的数据做 distillation，训练时同时考虑 weight、activation 和 KV cache。
- EfficientQAT：减少 QAT 的训练参数和资源开销。
- PV-Tuning：针对 1-2 bit 表示，改进普通 STE 的更新方式。
- QAD：针对 NVFP4 做 distillation 和精度恢复。

这一阶段要把“训练成本”也记进结果。只比较最终精度，不记录 token 数、GPU 时间和可训练参数量，会高估 QAT 的收益。

## 第六阶段：看真实推理问题

### 研究重点

最后不只看 weight PPL，还要看 KV cache、长上下文、reasoning task、kernel 和端到端速度。

### 动机

prefill、decode 和长上下文的瓶颈不同。一个方法在 WikiText2 上误差很小，不代表它在长上下文或数学推理上也稳定，更不代表真实速度一定更快。

### 主要方法

- KVQuant：按 KV cache 的分布设计低 bit quantizer，并单独处理 outlier。
- CommVQ：用和 RoPE 相容的 vector codebook 压缩 KV cache。
- When Reasoning Meets Compression：检查量化、蒸馏和剪枝具体伤到了哪些 reasoning 模块。
- MicroMix、MR-GPTQ 等 kernel 工作：同时记录 GPU、CUDA、batch size、prefill/decode 长度和实际数据布局。

## 建议的实际推进顺序

1. 在一个小模型上跑通 RTN、GPTQ、SmoothQuant，先把数据和评测入口固定。
2. 统一比较 QuaRot、SpinQuant、DuQuant、OSTQuant、FlatQuant，重点看 W4A4。
3. 在相同模型和 calibration 数据上实现 MXFP4/NVFP4 的 RTN、GPTQ、rotation 三组基线。
4. 再接 MR-GPTQ、MicroMix、MixFP4，分别分析 scale、rotation 和 mixed precision。
5. PTQ 掉点明显的设置再加入 LLM-QAT、PV-Tuning 或 QAD，不需要一开始就上训练。
6. 最后补 KV cache、reasoning benchmark 和真实 kernel 测速。

如果当前研究重点是 FP4，可以直接从第 3 步开始，但前面的 GPTQ、SmoothQuant 和 rotation 基线仍要保留，后面写论文时才能说清楚改进来自哪里。

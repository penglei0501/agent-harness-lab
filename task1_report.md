# 任务1：机器学习框架调研报告

> 执行人：alice（程序员）  
> 日期：2025-05-18

## 一、概述

本报告对 PyTorch 和 TensorFlow 两大主流深度学习框架进行系统性对比分析，并结合本项目实际情况给出推荐方案。

---

## 二、PyTorch

| 项目 | 说明 |
|------|------|
| 开发者 | Meta（Facebook AI Research） |
| 首次发布 | 2016年9月 |
| 当前最新稳定版 | 2.x 系列 |
| 语言 | Python 为主，底层 C++/CUDA |
| 许可证 | BSD |

### 优点
1. **动态计算图（Define-by-Run）**：图在运行时动态构建，调试方便，代码直观，类似 NumPy 风格
2. **Pythonic 设计**：与 Python 生态无缝融合，学习曲线平缓
3. **强大的调试能力**：支持标准 Python 调试器（pdb）、打印中间变量
4. **社区活跃**：学术界首选，论文复现几乎都用 PyTorch
5. **TorchScript / TorchFX**：提供从研究到生产的过渡方案
6. **丰富的生态库**：torchvision（CV）、torchaudio（音频）、torchtext（NLP）、HuggingFace Transformers
7. **分布式训练**：`torch.distributed` 支持 DDP、FSDP 等

### 缺点
1. 生产部署工具链相对 TensorFlow Serving 不够成熟（但 TorchServe 已在改善）
2. 静态量化/优化工具不如 TensorFlow 丰富
3. 企业级大规模分布式训练工具链相对较新

---

## 三、TensorFlow

| 项目 | 说明 |
|------|------|
| 开发者 | Google Brain |
| 首次发布 | 2015年11月 |
| 当前最新版本 | 2.x 系列（含 Keras 作为官方高级 API） |
| 语言 | Python 为主，底层 C++/CUDA |
| 许可证 | Apache 2.0 |

### 优点
1. **静态计算图（Define-and-Run）**：优化能力强，推理性能高
2. **生产部署成熟**：TensorFlow Serving、TensorFlow Lite（移动端）、TensorFlow.js（浏览器端）生态完整
3. **TFX（TensorFlow Extended）**：完整的 ML 生产流水线工具
4. **TPU 原生支持**：Google Cloud TPU 的最佳伙伴
5. **TensorBoard**：可视化工具非常成熟（PyTorch 也兼容）
6. **Keras API**：简洁易用的高级接口
7. **模型量化与优化**：TFLite 提供丰富的量化工具

### 缺点
1. 学习曲线偏陡：Eager Execution（动态图）虽在 TF2 中成为默认，但底层概念仍复杂
2. 调试困难：静态图模式下错误信息不够直观
3. 版本兼容性问题：TF1 → TF2 迁移成本高，部分 API 反复变动
4. 学术圈采用率下降：近年越来越多研究者转向 PyTorch

---

## 四、关键维度对比

| 对比维度 | PyTorch | TensorFlow |
|---------|---------|------------|
| **动态图** | ✅ 原生支持（Eager Mode） | ✅ TF2 默认启用（Eager Execution） |
| **静态图** | ⚠️ TorchScript/FX（可选） | ✅ 原生（Graph Mode） |
| **调试便利性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **学习曲线** | ⭐⭐⭐⭐⭐（平缓） | ⭐⭐⭐（较陡） |
| **研究/学术界** | ⭐⭐⭐⭐⭐（主流） | ⭐⭐⭐ |
| **工业界部署** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **移动端/边缘设备** | ⭐⭐⭐（TorchMobile） | ⭐⭐⭐⭐⭐（TFLite） |
| **分布式训练** | ⭐⭐⭐⭐（DDP成熟） | ⭐⭐⭐⭐⭐（历史悠久） |
| **可视化** | ⭐⭐⭐⭐（TensorBoard兼容） | ⭐⭐⭐⭐⭐（TensorBoard） |
| **社区生态** | 学术界主导，快速成长 | 工业界主导，生态庞大 |

---

## 五、推荐方案

### 推荐：PyTorch

**理由如下：**

1. **本项目定位**：项目主要是模型训练与评估（任务2→任务3），属于典型的 "研究+开发" 场景，PyTorch 更适合
2. **Python 3.12 兼容性**：PyTorch 对新版 Python 支持更好，TensorFlow 2.x 在某些较新 Python 版本上可能存在兼容问题
3. **开发效率优先**：动态图机制使调试和迭代更高效
4. **学习成本低**：团队成员上手快
5. **部署可选 TorchServe**：若有轻量级部署需求，TorchServe 足以满足

### 替代方案说明

如果后续需要大规模生产部署/移动端推理，可考虑：
- **ONNX 中间格式**：将 PyTorch 模型导出为 ONNX，再部署到其他推理引擎
- **TensorFlow Lite**：移动端场景下可选

---

## 六、环境准备建议

```bash
# 安装 PyTorch（根据 CUDA 版本选择）
pip3 install torch torchvision torchaudio

# CPU-only 版本
pip3 install torch --index-url https://download.pytorch.org/whl/cpu

# 相关依赖
pip3 install numpy pandas scikit-learn matplotlib
```

---

## 七、结论

**选择 PyTorch 作为本项目机器学习框架。** 对于任务2（数据处理流水线）和任务3（训练评估模型），PyTorch 提供了足够的灵活性、良好的调试体验和丰富的生态支持。

"""
数据处理流水线 - 数据清洗、特征提取和数据集划分
================================================
基于任务1（Alice 完成）推荐的 PyTorch 框架实现。

模块：
    - cleaner:      数据清洗（缺失值处理、异常值检测、去重）
    - feature_engineer: 特征提取与工程（数值/类别/文本特征处理）
    - splitter:     数据集划分（训练/验证/测试集）
    - pipeline:     完整流水线封装
"""

from .pipeline import DataPipeline, run_pipeline

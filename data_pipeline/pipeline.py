"""
完整数据处理流水线
==================
将数据清洗、特征工程、数据集划分串联为端到端流水线。
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .cleaner import DataCleaner
from .feature_engineer import FeatureEngineer
from .splitter import DatasetSplitter


@dataclass
class PipelineConfig:
    """流水线配置。"""
    # 数据清洗配置
    cleaning_strategy: str = "auto"
    remove_outliers: bool = False
    outlier_method: str = "iqr"
    outlier_factor: float = 1.5

    # 特征工程配置
    standardize_numeric: bool = True
    encode_categorical: bool = True
    categorical_encoding: str = "label"  # "label" 或 "onehot"
    datetime_features: List[str] = field(default_factory=lambda: ["year", "month", "day"])

    # 数据集划分配置
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    random_state: int = 42
    stratify: bool = False

    # 输出配置
    output_dir: str = "./data/processed"


class DataPipeline:
    """完整的数据处理流水线。"""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.cleaner = DataCleaner(strategy=self.config.cleaning_strategy)
        self.feature_engineer = FeatureEngineer()
        self.splitter = DatasetSplitter(
            train_ratio=self.config.train_ratio,
            val_ratio=self.config.val_ratio,
            test_ratio=self.config.test_ratio,
            random_state=self.config.random_state,
        )
        self._fitted = False
        self._pipeline_info: Dict[str, Any] = {}

    def fit(self, df: pd.DataFrame, target_col: Optional[str] = None) -> "DataPipeline":
        """在数据上拟合流水线参数。"""
        self._pipeline_info["input_shape"] = df.shape
        self._pipeline_info["input_columns"] = df.columns.tolist()
        self._pipeline_info["target_col"] = target_col

        # 拟合清洗器
        self.cleaner.fit(df)

        # 拟合特征工程
        self.feature_engineer.fit(df)

        self._fitted = True
        return self

    def transform(
        self,
        df: pd.DataFrame,
        target_col: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        """对数据执行完整的转换流水线。

        返回
        -------
        Tuple[DataFrame, Series or None]
            (特征数据, 标签数据)
        """
        if not self._fitted:
            raise RuntimeError("请先调用 fit() 方法拟合流水线！")

        result = df.copy()

        # Step 1: 数据清洗
        result = self.cleaner.transform(result)

        # Step 2: 删除异常值（可选）
        if self.config.remove_outliers:
            result = self.cleaner.remove_outliers(
                result, method=self.config.outlier_method, factor=self.config.outlier_factor
            )

        # Step 3: 特征工程
        if self.config.standardize_numeric:
            result = self.feature_engineer.standardize(result)
        if self.config.encode_categorical:
            if self.config.categorical_encoding == "label":
                result = self.feature_engineer.label_encode(result)
            elif self.config.categorical_encoding == "onehot":
                result = self.feature_engineer.one_hot_encode(result)

        # Step 4: 分离特征和标签
        if target_col and target_col in result.columns:
            y = result[target_col]
            X = result.drop(columns=[target_col])
        else:
            X = result
            y = None

        self._pipeline_info["output_shape"] = X.shape
        return X, y

    def fit_transform(
        self,
        df: pd.DataFrame,
        target_col: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        """拟合并转换数据。"""
        return self.fit(df, target_col).transform(df, target_col)

    def run(
        self,
        df: pd.DataFrame,
        target_col: Optional[str] = None,
        time_col: Optional[str] = None,
        split_method: str = "random",
    ) -> Dict[str, Any]:
        """运行完整流水线（拟合 + 转换 + 划分）。

        参数
        ----------
        df : pd.DataFrame
            原始输入数据
        target_col : str, optional
            目标列名
        time_col : str, optional
            时间列名（用于时序划分）
        split_method : str
            划分方法: "random" 或 "temporal"

        返回
        -------
        Dict[str, Any]
            包含 "train", "val", "test" 三个 DataFrames 和流水线信息的字典
        """
        print("🚀 开始执行数据处理流水线...")

        # 1. 拟合
        print("📊 步骤 1/4: 拟合流水线参数...")
        self.fit(df, target_col)

        # 2. 清洗
        print("🧹 步骤 2/4: 数据清洗...")
        cleaned = self.cleaner.transform(df)

        if self.config.remove_outliers:
            print(f"   🔍 移除异常值 (方法: {self.config.outlier_method})...")
            cleaned = self.cleaner.remove_outliers(
                cleaned, method=self.config.outlier_method, factor=self.config.outlier_factor
            )

        # 3. 特征工程
        print("⚙️  步骤 3/4: 特征工程...")
        if self.config.standardize_numeric:
            cleaned = self.feature_engineer.standardize(cleaned)
        if self.config.encode_categorical:
            if self.config.categorical_encoding == "label":
                cleaned = self.feature_engineer.label_encode(cleaned)
            elif self.config.categorical_encoding == "onehot":
                cleaned = self.feature_engineer.one_hot_encode(cleaned)

        # 分离特征和标签
        if target_col and target_col in cleaned.columns:
            y = cleaned[target_col]
            X = cleaned.drop(columns=[target_col])
            data_for_split = pd.concat([X, y], axis=1)
        else:
            X = cleaned
            y = None
            data_for_split = X

        # 4. 数据集划分
        print(f"✂️  步骤 4/4: 数据集划分 ({split_method})...")

        if split_method == "temporal" and time_col:
            train, val, test = self.splitter.temporal_split(
                data_for_split, time_col=time_col
            )
        else:
            train, val, test = self.splitter.random_split(
                data_for_split, target_col=target_col,
                stratify=self.config.stratify,
            )

        # 保存结果
        os.makedirs(self.config.output_dir, exist_ok=True)

        result = {
            "train": train,
            "val": val,
            "test": test,
            "info": {
                "input_shape": self._pipeline_info.get("input_shape"),
                "train_size": len(train),
                "val_size": len(val),
                "test_size": len(test),
                "config": asdict(self.config),
            },
        }

        print(f"✅ 流水线执行完成！")
        print(f"   训练集: {len(train)} 样本")
        print(f"   验证集: {len(val)} 样本")
        print(f"   测试集: {len(test)} 样本")

        return result

    def save_datasets(
        self,
        result: Dict[str, Any],
        prefix: str = "dataset",
    ) -> Dict[str, str]:
        """将划分后的数据集保存为 CSV 文件。"""
        output_dir = self.config.output_dir
        os.makedirs(output_dir, exist_ok=True)

        paths = {}
        for split_name in ["train", "val", "test"]:
            path = os.path.join(output_dir, f"{prefix}_{split_name}.csv")
            result[split_name].to_csv(path, index=False)
            paths[split_name] = path

        # 保存配置和信息
        info_path = os.path.join(output_dir, f"{prefix}_info.json")
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(result["info"], f, ensure_ascii=False, indent=2)
        paths["info"] = info_path

        print(f"💾 数据集已保存至: {output_dir}/")
        for name, path in paths.items():
            print(f"   - {name}: {path}")

        return paths

    def summary(self) -> str:
        """返回流水线配置摘要。"""
        return json.dumps(asdict(self.config), ensure_ascii=False, indent=2)


def run_pipeline(
    df: pd.DataFrame,
    target_col: Optional[str] = None,
    config: Optional[PipelineConfig] = None,
    save: bool = True,
) -> Dict[str, Any]:
    """便捷函数：一行代码运行数据处理流水线。

    示例
    -------
    >>> import pandas as pd
    >>> from data_pipeline import run_pipeline
    >>>
    >>> df = pd.read_csv("data.csv")
    >>> result = run_pipeline(df, target_col="label")
    >>> result["train"].head()
    """
    pipeline = DataPipeline(config)
    result = pipeline.run(df, target_col=target_col)

    if save:
        pipeline.save_datasets(result)

    return result

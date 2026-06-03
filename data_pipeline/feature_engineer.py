"""
特征提取与工程模块
==================
功能：
  - 数值特征标准化/归一化
  - 类别特征编码（Label Encoding / One-Hot Encoding）
  - 文本特征提取（TF-IDF / CountVectorizer）
  - 特征组合与交叉
  - 时间特征提取
"""

import re
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd


class FeatureEngineer:
    """特征工程处理器。"""

    def __init__(self):
        self._encoders: Dict[str, Any] = {}
        self._numeric_stats: Dict[str, Dict[str, float]] = {}
        self._fitted = False

    # ──────────────────────────────────────────────
    # 数值特征处理
    # ──────────────────────────────────────────────

    def fit_numeric(self, df: pd.DataFrame, columns: Optional[List[str]] = None) -> "FeatureEngineer":
        """学习数值列的均值和标准差（用于标准化）。"""
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        for col in columns:
            if col in df.columns:
                self._numeric_stats[col] = {
                    "mean": float(df[col].mean()),
                    "std": float(df[col].std()) if df[col].std() > 0 else 1.0,
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                }
        return self

    def standardize(self, df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Z-Score 标准化: (x - mean) / std"""
        result = df.copy()
        if columns is None:
            columns = list(self._numeric_stats.keys())

        for col in columns:
            if col in result.columns and col in self._numeric_stats:
                stats = self._numeric_stats[col]
                result[col] = (result[col].astype(float) - stats["mean"]) / stats["std"]
        return result

    def normalize(self, df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Min-Max 归一化: (x - min) / (max - min)"""
        result = df.copy()
        if columns is None:
            columns = list(self._numeric_stats.keys())

        for col in columns:
            if col in result.columns and col in self._numeric_stats:
                stats = self._numeric_stats[col]
                range_val = stats["max"] - stats["min"]
                if range_val > 0:
                    result[col] = (result[col].astype(float) - stats["min"]) / range_val
                else:
                    result[col] = 0.0
        return result

    # ──────────────────────────────────────────────
    # 类别特征处理
    # ──────────────────────────────────────────────

    def fit_categorical(self, df: pd.DataFrame, columns: Optional[List[str]] = None) -> "FeatureEngineer":
        """学习类别编码映射。"""
        if columns is None:
            columns = df.select_dtypes(include=["object", "category", "str"]).columns.tolist()

        for col in columns:
            if col in df.columns:
                unique_vals = df[col].dropna().unique().tolist()
                self._encoders[f"label_{col}"] = {
                    val: idx for idx, val in enumerate(sorted(unique_vals))
                }
                self._encoders[f"onehot_{col}"] = sorted(unique_vals)
        return self

    def label_encode(self, df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """标签编码：将类别映射为整数。"""
        result = df.copy()
        if columns is None:
            columns = [k.replace("label_", "") for k in self._encoders.keys() if k.startswith("label_")]

        for col in columns:
            encoder_key = f"label_{col}"
            if col in result.columns and encoder_key in self._encoders:
                result[col] = result[col].map(self._encoders[encoder_key]).fillna(-1).astype(int)
        return result

    def one_hot_encode(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        drop_first: bool = False,
        prefix: Optional[str] = None
    ) -> pd.DataFrame:
        """One-Hot 编码。"""
        result = df.copy()
        if columns is None:
            columns = [k.replace("onehot_", "") for k in self._encoders.keys() if k.startswith("onehot_")]

        for col in columns:
            if col in result.columns:
                dummies = pd.get_dummies(
                    result[col],
                    prefix=prefix or col,
                    drop_first=drop_first,
                    dummy_na=False,
                )
                result = pd.concat([result, dummies], axis=1)
                # 可选择删除原列
                # result = result.drop(columns=[col])

        return result

    # ──────────────────────────────────────────────
    # 时间特征提取
    # ──────────────────────────────────────────────

    @staticmethod
    def extract_datetime_features(
        df: pd.DataFrame,
        column: str,
        features: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """从日期列提取时间特征。

        features 可选值:
            year, month, day, dayofweek, quarter, hour, minute, second, is_weekend
        """
        result = df.copy()
        if column not in result.columns:
            return result

        dt_series = pd.to_datetime(result[column], errors="coerce")

        feature_map = {
            "year": dt_series.dt.year,
            "month": dt_series.dt.month,
            "day": dt_series.dt.day,
            "dayofweek": dt_series.dt.dayofweek,
            "quarter": dt_series.dt.quarter,
            "hour": dt_series.dt.hour,
            "minute": dt_series.dt.minute,
            "second": dt_series.dt.second,
            "is_weekend": (dt_series.dt.dayofweek >= 5).astype(int),
        }

        if features is None:
            features = ["year", "month", "day", "dayofweek"]

        for feat in features:
            if feat in feature_map:
                result[f"{column}_{feat}"] = feature_map[feat]

        return result

    # ──────────────────────────────────────────────
    # 特征交叉
    # ──────────────────────────────────────────────

    @staticmethod
    def create_interaction(
        df: pd.DataFrame,
        col1: str,
        col2: str,
        operation: str = "multiply",
        new_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """创建两个特征的交叉特征。

        operation 可选: multiply, add, subtract, divide
        """
        result = df.copy()
        if col1 not in result.columns or col2 not in result.columns:
            return result

        name = new_name or f"{col1}_{operation}_{col2}"

        ops = {
            "multiply": lambda a, b: a * b,
            "add": lambda a, b: a + b,
            "subtract": lambda a, b: a - b,
            "divide": lambda a, b: a / (b + 1e-8),
        }

        if operation in ops:
            result[name] = ops[operation](result[col1].astype(float), result[col2].astype(float))

        return result

    @staticmethod
    def bin_numeric(
        df: pd.DataFrame,
        column: str,
        bins: Union[int, List[float]],
        labels: Optional[List[str]] = None,
        new_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """将数值特征分箱为类别特征。"""
        result = df.copy()
        if column not in result.columns:
            return result

        name = new_name or f"{column}_binned"
        result[name] = pd.cut(result[column], bins=bins, labels=labels)
        return result

    # ──────────────────────────────────────────────
    # 主流程
    # ──────────────────────────────────────────────

    def fit(self, df: pd.DataFrame) -> "FeatureEngineer":
        """学习所有特征参数。"""
        self.fit_numeric(df)
        self.fit_categorical(df)
        self._fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """对数据应用特征工程（需先 fit）。"""
        if not self._fitted:
            raise RuntimeError("请先调用 fit() 方法拟合数据！")
        result = df.copy()
        result = self.standardize(result)
        return result

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """学习并转换。"""
        self.fit(df)
        return self.transform(df)

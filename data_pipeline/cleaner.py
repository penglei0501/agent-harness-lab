"""
数据清洗模块
============
功能：
  - 缺失值检测与处理（删除/填充/插值）
  - 异常值检测与处理（IQR / Z-Score）
  - 重复数据删除
  - 数据类型标准化
"""

from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np
import pandas as pd


class DataCleaner:
    """数据清洗器，提供多种清洗策略。"""

    def __init__(self, strategy: str = "auto"):
        """
        参数
        ----------
        strategy : str
            缺失值处理策略: "drop" (删除含缺失值的行),
            "fill_mean" (用均值填充),
            "fill_median" (用中位数填充),
            "fill_mode" (用众数填充),
            "fill_value" (用指定值填充),
            "interpolate" (线性插值),
            "auto" (自动选择)
        """
        self.strategy = strategy
        self._fitted = False
        self._fill_values: Dict[str, Any] = {}

    def _auto_select_strategy(self, df: pd.DataFrame) -> None:
        """自动为每列选择填充策略。"""
        for col in df.columns:
            if df[col].dtype in (np.int64, np.float64):
                if df[col].skew() > 1.0:
                    # 偏态分布用中位数
                    self._fill_values[col] = df[col].median()
                else:
                    self._fill_values[col] = df[col].mean()
            elif df[col].dtype == object:
                # 类别型用众数
                mode_vals = df[col].mode()
                self._fill_values[col] = mode_vals[0] if not mode_vals.empty else "UNKNOWN"
            else:
                self._fill_values[col] = None

    def fit(self, df: pd.DataFrame) -> "DataCleaner":
        """学习数据的填充参数。"""
        if self.strategy == "auto":
            self._auto_select_strategy(df)
        elif self.strategy == "fill_mean":
            self._fill_values = {col: df[col].mean() for col in df.select_dtypes(include=[np.number]).columns}
        elif self.strategy == "fill_median":
            self._fill_values = {col: df[col].median() for col in df.select_dtypes(include=[np.number]).columns}
        elif self.strategy == "fill_mode":
            for col in df.columns:
                mode_vals = df[col].mode()
                self._fill_values[col] = mode_vals[0] if not mode_vals.empty else None
        self._fitted = True
        return self

    def handle_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理缺失值。"""
        result = df.copy()

        if self.strategy == "drop":
            return result.dropna().reset_index(drop=True)

        if self.strategy == "interpolate":
            numeric_cols = result.select_dtypes(include=[np.number]).columns
            result[numeric_cols] = result[numeric_cols].interpolate(method="linear")
            # 剩余的NaN用前向填充
            return result.ffill().bfill().reset_index(drop=True)

        if self.strategy == "fill_value":
            # 用户需在 transform 时传入 fill_values
            return result

        # 使用已学习的填充值
        if not self._fitted:
            self.fit(result)

        for col, val in self._fill_values.items():
            if col in result.columns and val is not None:
                result[col] = result[col].fillna(val)

        return result.reset_index(drop=True)

    @staticmethod
    def remove_duplicates(df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """删除重复行。"""
        return df.drop_duplicates(subset=subset).reset_index(drop=True)

    @staticmethod
    def detect_outliers_iqr(df: pd.DataFrame, column: str, factor: float = 1.5) -> pd.Series:
        """使用 IQR 方法检测异常值。

        返回布尔 Series，True 表示异常值。
        """
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - factor * IQR
        upper = Q3 + factor * IQR
        return (df[column] < lower) | (df[column] > upper)

    @staticmethod
    def detect_outliers_zscore(df: pd.DataFrame, column: str, threshold: float = 3.0) -> pd.Series:
        """使用 Z-Score 方法检测异常值。

        返回布尔 Series，True 表示异常值。
        """
        mean = df[column].mean()
        std = df[column].std()
        if std == 0:
            return pd.Series([False] * len(df), index=df.index)
        z_scores = (df[column] - mean) / std
        return z_scores.abs() > threshold

    def remove_outliers(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: str = "iqr",
        **kwargs
    ) -> pd.DataFrame:
        """检测并移除异常值。"""
        result = df.copy()
        if columns is None:
            columns = result.select_dtypes(include=[np.number]).columns.tolist()

        outlier_mask = pd.Series([False] * len(result), index=result.index)
        for col in columns:
            if method == "iqr":
                outlier_mask |= self.detect_outliers_iqr(result, col, **kwargs)
            elif method == "zscore":
                outlier_mask |= self.detect_outliers_zscore(result, col, **kwargs)

        return result[~outlier_mask].reset_index(drop=True)

    @staticmethod
    def standardize_types(df: pd.DataFrame, type_map: Dict[str, str]) -> pd.DataFrame:
        """标准化列的数据类型。"""
        result = df.copy()
        for col, dtype in type_map.items():
            if col in result.columns:
                try:
                    result[col] = result[col].astype(dtype)
                except (ValueError, TypeError) as e:
                    print(f"⚠️ 列 '{col}' 转换至 {dtype} 失败: {e}")
        return result

    def transform(self, df: pd.DataFrame, fill_values: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """对数据进行清洗转换。"""
        result = df.copy()

        # 1. 处理缺失值
        if fill_values and self.strategy == "fill_value":
            for col, val in fill_values.items():
                if col in result.columns:
                    result[col] = result[col].fillna(val)
        else:
            result = self.handle_missing(result)

        return result

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """学习参数并转换数据。"""
        return self.fit(df).transform(df)


def create_cleaner(strategy: str = "auto") -> DataCleaner:
    """便捷工厂函数。"""
    return DataCleaner(strategy=strategy)

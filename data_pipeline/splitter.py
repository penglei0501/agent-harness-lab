"""
数据集划分模块
==============
功能：
  - 训练/验证/测试集划分（随机 / 分层 / 时序）
  - PyTorch Dataset 封装
  - 数据加载器 (DataLoader) 创建
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


class DatasetSplitter:
    """数据集划分器，支持多种划分策略。"""

    def __init__(
        self,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        random_state: int = 42,
        shuffle: bool = True,
    ):
        """
        参数
        ----------
        train_ratio : float
            训练集比例
        val_ratio : float
            验证集比例
        test_ratio : float
            测试集比例
        random_state : int
            随机种子
        shuffle : bool
            是否在划分前打乱数据
        """
        total = train_ratio + val_ratio + test_ratio
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"比例之和必须为 1.0，当前为 {total}")

        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.random_state = random_state
        self.shuffle = shuffle

        self._split_indices: Dict[str, np.ndarray] = {}
        self._fitted = False

    def random_split(
        self,
        df: pd.DataFrame,
        target_col: Optional[str] = None,
        stratify: bool = False,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """随机划分数据集。

        参数
        ----------
        df : pd.DataFrame
            输入数据
        target_col : str, optional
            目标列名（用于分层采样）
        stratify : bool
            是否使用分层采样（需提供 target_col）

        返回
        -------
        Tuple[DataFrame, DataFrame, DataFrame]
            (训练集, 验证集, 测试集)
        """
        X = df.copy()
        y = X[target_col] if target_col and stratify else None

        # 先分出测试集
        train_val, test = train_test_split(
            X,
            test_size=self.test_ratio,
            random_state=self.random_state,
            shuffle=self.shuffle,
            stratify=y,
        )

        # 再从剩余中分出训练集和验证集
        val_ratio_adjusted = self.val_ratio / (self.train_ratio + self.val_ratio)

        y_train_val = (
            train_val[target_col]
            if target_col and stratify and y is not None
            else None
        )

        train, val = train_test_split(
            train_val,
            test_size=val_ratio_adjusted,
            random_state=self.random_state,
            shuffle=self.shuffle,
            stratify=y_train_val,
        )

        self._split_indices = {
            "train": train.index.to_numpy(),
            "val": val.index.to_numpy(),
            "test": test.index.to_numpy(),
        }
        self._fitted = True

        return train.reset_index(drop=True), val.reset_index(drop=True), test.reset_index(drop=True)

    def temporal_split(
        self,
        df: pd.DataFrame,
        time_col: str,
        ascending: bool = True,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """按时间顺序划分（适用于时序数据）。

        参数
        ----------
        df : pd.DataFrame
            输入数据
        time_col : str
            时间列名
        ascending : bool
            是否按时间升序排列

        返回
        -------
        Tuple[DataFrame, DataFrame, DataFrame]
            (训练集, 验证集, 测试集) — 按时间顺序划分
        """
        result = df.copy()
        if ascending:
            result = result.sort_values(by=time_col).reset_index(drop=True)
        else:
            result = result.sort_values(by=time_col, ascending=False).reset_index(drop=True)

        total = len(result)
        train_end = int(total * self.train_ratio)
        val_end = train_end + int(total * self.val_ratio)

        train = result.iloc[:train_end].reset_index(drop=True)
        val = result.iloc[train_end:val_end].reset_index(drop=True)
        test = result.iloc[val_end:].reset_index(drop=True)

        return train, val, test

    def get_split_info(self) -> Dict[str, Any]:
        """获取划分信息。"""
        if not self._fitted:
            return {"status": "not fitted"}
        return {
            "status": "fitted",
            "train_size": len(self._split_indices.get("train", [])),
            "val_size": len(self._split_indices.get("val", [])),
            "test_size": len(self._split_indices.get("test", [])),
            "ratios": {
                "train": self.train_ratio,
                "val": self.val_ratio,
                "test": self.test_ratio,
            },
        }


class PyTorchDataset:
    """将 DataFrame 封装为 PyTorch Dataset（可选依赖 PyTorch）。"""

    def __init__(
        self,
        features: pd.DataFrame,
        labels: Optional[pd.Series] = None,
        task: str = "regression",
    ):
        """
        参数
        ----------
        features : pd.DataFrame
            特征数据
        labels : pd.Series, optional
            标签数据
        task : str
            "regression" 或 "classification"
        """
        self.features = features
        self.labels = labels
        self.task = task

    def __len__(self) -> int:
        return len(self.features)

    def _get_numeric_values(self, idx: int) -> np.ndarray:
        """获取数值型特征值，非数值列会被跳过。"""
        row = self.features.iloc[idx]
        numeric_values = []
        for val in row:
            if isinstance(val, (int, float, np.integer, np.floating)):
                numeric_values.append(float(val))
            elif isinstance(val, np.bool_):
                numeric_values.append(float(val))
            else:
                # 尝试转换为 float
                try:
                    numeric_values.append(float(val))
                except (ValueError, TypeError):
                    numeric_values.append(0.0)
        return np.array(numeric_values, dtype=np.float32)

    def __getitem__(self, idx: int) -> Tuple[Any, Any]:
        try:
            import torch
        except ImportError:
            raise ImportError("使用 PyTorchDataset 需要安装 PyTorch: pip install torch")

        x = torch.tensor(self._get_numeric_values(idx), dtype=torch.float32)
        if self.labels is not None:
            y_val = self.labels.iloc[idx]
            if self.task == "classification":
                y = torch.tensor(y_val, dtype=torch.long)
            else:
                y = torch.tensor(y_val, dtype=torch.float32)
            return x, y
        return x

    def to_dataloader(self, batch_size: int = 32, shuffle: bool = True):
        """创建 PyTorch DataLoader。"""
        try:
            from torch.utils.data import DataLoader
        except ImportError:
            raise ImportError("需要安装 PyTorch: pip install torch")

        return DataLoader(
            self,
            batch_size=batch_size,
            shuffle=shuffle,
        )

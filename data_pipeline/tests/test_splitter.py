"""测试数据集划分模块。"""

import numpy as np
import pandas as pd
import pytest

from data_pipeline.splitter import DatasetSplitter, PyTorchDataset


@pytest.fixture
def sample_df():
    """创建示例 DataFrame。"""
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        "feature1": np.random.randn(n),
        "feature2": np.random.randn(n),
        "label": np.random.randint(0, 2, n),
        "date": pd.date_range("2023-01-01", periods=n, freq="D"),
    })


class TestDatasetSplitter:
    def test_random_split_default_ratios(self, sample_df):
        splitter = DatasetSplitter()
        train, val, test = splitter.random_split(sample_df)
        total = len(sample_df)
        # All data preserved
        assert len(train) + len(val) + len(test) == total
        # Approximate ratios (due to integer rounding)
        assert abs(len(train) / total - 0.7) < 0.02
        assert abs(len(val) / total - 0.15) < 0.02
        assert abs(len(test) / total - 0.15) < 0.02

    def test_random_split_custom_ratios(self, sample_df):
        splitter = DatasetSplitter(train_ratio=0.8, val_ratio=0.1, test_ratio=0.1)
        train, val, test = splitter.random_split(sample_df)
        assert len(train) == 80
        assert len(val) == 10
        assert len(test) == 10

    def test_random_split_invalid_ratios(self):
        with pytest.raises(ValueError):
            DatasetSplitter(train_ratio=0.5, val_ratio=0.3, test_ratio=0.3)

    def test_stratified_split(self, sample_df):
        splitter = DatasetSplitter(train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)
        train, val, test = splitter.random_split(
            sample_df, target_col="label", stratify=True
        )
        # Check label distribution is preserved
        for subset in [train, val, test]:
            label_ratio = subset["label"].mean()
            assert abs(label_ratio - sample_df["label"].mean()) < 0.2

    def test_temporal_split(self, sample_df):
        splitter = DatasetSplitter(train_ratio=0.6, val_ratio=0.2, test_ratio=0.2)
        train, val, test = splitter.temporal_split(sample_df, time_col="date")
        # Check temporal order is preserved
        assert train["date"].max() <= val["date"].min()
        assert val["date"].max() <= test["date"].min()

    def test_get_split_info(self, sample_df):
        splitter = DatasetSplitter()
        info_before = splitter.get_split_info()
        assert info_before["status"] == "not fitted"

        splitter.random_split(sample_df)
        info_after = splitter.get_split_info()
        assert info_after["status"] == "fitted"
        assert info_after["train_size"] > 0
        assert info_after["val_size"] > 0
        assert info_after["test_size"] > 0


class TestPyTorchDataset:
    def test_dataset_length(self):
        X = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        y = pd.Series([0, 1, 0])
        dataset = PyTorchDataset(X, y)
        assert len(dataset) == 3

    def test_dataset_getitem(self):
        X = pd.DataFrame({"A": [1.0, 2.0], "B": [3.0, 4.0]})
        y = pd.Series([0, 1])
        dataset = PyTorchDataset(X, y, task="classification")
        x, label = dataset[0]
        import torch
        assert isinstance(x, torch.Tensor)
        assert isinstance(label, torch.Tensor)
        assert x.shape == (2,)

    def test_to_dataloader(self):
        X = pd.DataFrame({"A": range(10), "B": range(10, 20)})
        y = pd.Series([0] * 10)
        dataset = PyTorchDataset(X, y)
        dataloader = dataset.to_dataloader(batch_size=4, shuffle=False)
        batches = list(dataloader)
        assert len(batches) == 3  # 10 items, batch_size=4 → 3 batches
        # Last batch has 2 items
        assert batches[-1][0].shape[0] == 2

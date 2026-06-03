"""测试完整流水线。"""

import numpy as np
import pandas as pd
import pytest

from data_pipeline import DataPipeline, run_pipeline
from data_pipeline.pipeline import PipelineConfig


@pytest.fixture
def sample_df():
    """创建示例 DataFrame。"""
    np.random.seed(42)
    n = 200
    return pd.DataFrame({
        "age": np.random.randint(18, 65, n).astype(float),
        "income": np.random.normal(50000, 15000, n),
        "education": np.random.choice(["高中", "本科", "硕士"], n),
        "label": np.random.randint(0, 2, n),
    })


class TestDataPipeline:
    def test_fit_transform(self, sample_df):
        pipeline = DataPipeline()
        X, y = pipeline.fit_transform(sample_df, target_col="label")
        assert X is not None
        assert y is not None
        assert "label" not in X.columns

    def test_run_pipeline(self, sample_df):
        pipeline = DataPipeline()
        result = pipeline.run(sample_df, target_col="label")
        assert "train" in result
        assert "val" in result
        assert "test" in result
        assert result["train"].shape[0] > 0
        assert result["val"].shape[0] > 0
        assert result["test"].shape[0] > 0
        assert "info" in result

    def test_run_pipeline_without_target(self, sample_df):
        df_no_target = sample_df.drop(columns=["label"])
        pipeline = DataPipeline()
        result = pipeline.run(df_no_target)
        assert "train" in result
        # Total rows preserved
        total = sum(len(v) for k, v in result.items() if k != "info")
        assert total == len(sample_df)

    def test_custom_config(self, sample_df):
        config = PipelineConfig(
            cleaning_strategy="drop",
            standardize_numeric=True,
            encode_categorical=True,
            categorical_encoding="onehot",
            train_ratio=0.8,
            val_ratio=0.1,
            test_ratio=0.1,
        )
        pipeline = DataPipeline(config)
        result = pipeline.run(sample_df, target_col="label")
        assert abs(len(result["train"]) / 200 - 0.8) < 0.1

    def test_run_pipeline_convenience(self, sample_df):
        result = run_pipeline(sample_df, target_col="label", save=False)
        assert "train" in result
        assert "val" in result
        assert "test" in result

    def test_summary(self, sample_df):
        pipeline = DataPipeline()
        summary = pipeline.summary()
        assert "train_ratio" in summary
        assert "val_ratio" in summary

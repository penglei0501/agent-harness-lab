"""测试特征工程模块。"""

import numpy as np
import pandas as pd
import pytest

from data_pipeline.feature_engineer import FeatureEngineer


@pytest.fixture
def sample_df():
    """创建示例 DataFrame。"""
    np.random.seed(42)
    return pd.DataFrame({
        "age": [25, 30, 35, 40, 45],
        "income": [30000, 50000, 70000, 90000, 110000],
        "education": ["高中", "本科", "硕士", "博士", "本科"],
        "city": ["北京", "上海", "广州", "深圳", "北京"],
    })


class TestFeatureEngineer:
    def test_fit_numeric_and_standardize(self, sample_df):
        fe = FeatureEngineer()
        fe.fit_numeric(sample_df, columns=["age", "income"])
        result = fe.standardize(sample_df)
        # After standardization, mean ≈ 0, std ≈ 1
        assert abs(result["age"].mean()) < 1e-10
        assert abs(result["income"].mean()) < 1e-10
        assert abs(result["age"].std() - 1.0) < 1e-10

    def test_normalize(self, sample_df):
        fe = FeatureEngineer()
        fe.fit_numeric(sample_df, columns=["age"])
        result = fe.normalize(sample_df)
        assert result["age"].min() == 0.0
        assert result["age"].max() == 1.0

    def test_fit_categorical_and_label_encode(self, sample_df):
        fe = FeatureEngineer()
        fe.fit_categorical(sample_df, columns=["education", "city"])
        result = fe.label_encode(sample_df)
        assert result["education"].dtype == int
        assert set(result["education"].unique()) == {0, 1, 2, 3}
        assert set(result["city"].unique()) == {0, 1, 2, 3}

    def test_one_hot_encode(self, sample_df):
        fe = FeatureEngineer()
        fe.fit_categorical(sample_df, columns=["city"])
        result = fe.one_hot_encode(sample_df, columns=["city"])
        # One-hot adds 4 new columns (北京, 上海, 广州, 深圳)
        city_cols = [c for c in result.columns if c.startswith("city_")]
        assert len(city_cols) == 4

    def test_one_hot_encode_drop_first(self, sample_df):
        fe = FeatureEngineer()
        fe.fit_categorical(sample_df, columns=["city"])
        result = fe.one_hot_encode(sample_df, columns=["city"], drop_first=True)
        city_cols = [c for c in result.columns if c.startswith("city_")]
        assert len(city_cols) == 3  # dropped first category

    def test_extract_datetime_features(self):
        df = pd.DataFrame({
            "date": pd.date_range("2023-01-01", periods=3, freq="D")
        })
        result = FeatureEngineer.extract_datetime_features(
            df, "date", features=["year", "month", "day", "dayofweek"]
        )
        assert "date_year" in result.columns
        assert "date_month" in result.columns
        assert "date_day" in result.columns
        assert "date_dayofweek" in result.columns
        assert result["date_year"].iloc[0] == 2023
        assert result["date_month"].iloc[0] == 1
        assert result["date_day"].iloc[0] == 1

    def test_create_interaction_multiply(self, sample_df):
        result = FeatureEngineer.create_interaction(
            sample_df, "age", "income", operation="multiply"
        )
        interaction_col = "age_multiply_income"
        assert interaction_col in result.columns
        assert result[interaction_col].iloc[0] == 25 * 30000

    def test_create_interaction_add(self, sample_df):
        result = FeatureEngineer.create_interaction(
            sample_df, "age", "income", operation="add"
        )
        assert "age_add_income" in result.columns

    def test_bin_numeric(self, sample_df):
        result = FeatureEngineer.bin_numeric(
            sample_df, "age", bins=[0, 30, 40, 100], labels=["年轻", "中年", "年长"]
        )
        assert "age_binned" in result.columns
        assert result["age_binned"].iloc[0] == "年轻"

    def test_fit_transform_pipeline(self, sample_df):
        fe = FeatureEngineer()
        result = fe.fit_transform(sample_df)
        # Numeric columns should be standardized
        assert abs(result["age"].mean()) < 1e-10

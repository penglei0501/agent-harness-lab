"""测试数据清洗模块。"""

import numpy as np
import pandas as pd
import pytest

from data_pipeline.cleaner import DataCleaner


@pytest.fixture
def sample_df():
    """创建示例 DataFrame。"""
    np.random.seed(42)
    return pd.DataFrame({
        "A": [1.0, 2.0, np.nan, 4.0, 5.0],
        "B": [10, 20, 30, np.nan, 50],
        "C": ["x", "y", "z", "x", np.nan],
        "D": [100, 200, 300, 400, 500],
    })


class TestDataCleaner:
    def test_handle_missing_drop(self, sample_df):
        cleaner = DataCleaner(strategy="drop")
        result = cleaner.handle_missing(sample_df)
        # 3 rows with complete data out of 5
        assert len(result) == 2  # rows 0 and 3 (index 0 and 3 have no NaN...actually row 0 has no NaN)
        # Let me recalculate: row 0: A=1.0, B=10, C=x, D=100 → valid
        # row 1: A=2.0, B=20, C=y, D=200 → valid
        # row 2: A=NaN → invalid
        # row 3: B=NaN → invalid
        # row 4: C=NaN → invalid
        # So 2 rows remain
        assert len(result) == 2

    def test_handle_missing_fill_mean(self, sample_df):
        cleaner = DataCleaner(strategy="fill_mean")
        result = cleaner.handle_missing(sample_df)
        assert len(result) == 5  # no rows dropped
        # A mean = (1+2+4+5)/4 = 3.0
        assert result.loc[2, "A"] == 3.0
        # B mean = (10+20+30+50)/4 = 27.5
        assert result.loc[3, "B"] == 27.5

    def test_handle_missing_auto(self, sample_df):
        cleaner = DataCleaner(strategy="auto")
        result = cleaner.handle_missing(sample_df)
        assert len(result) == 5

    def test_remove_duplicates(self, sample_df):
        df_dup = pd.concat([sample_df, sample_df.iloc[[0]]], ignore_index=True)
        assert len(df_dup) == 6
        result = DataCleaner.remove_duplicates(df_dup)
        assert len(result) == 5

    def test_detect_outliers_iqr(self, sample_df):
        df = pd.DataFrame({"values": [1, 2, 3, 4, 100]})
        outliers = DataCleaner.detect_outliers_iqr(df, "values")
        assert outliers.iloc[4] == True  # 100 is outlier
        assert outliers.iloc[:4].sum() == 0  # others not

    def test_detect_outliers_zscore(self):
        df = pd.DataFrame({"values": [10, 10, 10, 10, 100]})
        outliers = DataCleaner.detect_outliers_zscore(df, "values", threshold=1.5)
        assert outliers.iloc[4] == True  # 100 is outlier (mean=28, std≈36, z≈2.0)

    def test_remove_outliers(self, sample_df):
        df = pd.DataFrame({"A": [1, 2, 3, 4, 100], "B": [10, 20, 30, 40, 50]})
        cleaner = DataCleaner()
        result = cleaner.remove_outliers(df, columns=["A"])
        assert len(result) == 4  # row with 100 removed

    def test_fit_transform_pipeline(self, sample_df):
        cleaner = DataCleaner(strategy="fill_mean")
        result = cleaner.fit_transform(sample_df)
        assert len(result) == 5
        # 数值列应该已填充，字符串列不受 fill_mean 影响
        assert result[["A", "B", "D"]].isnull().sum().sum() == 0  # 数值列无 NaN

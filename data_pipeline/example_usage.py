"""
数据处理流水线 - 使用示例
=========================
运行方式: python -m data_pipeline.example_usage

本示例演示如何使用 data_pipeline 模块处理一份示例数据集。
"""

import numpy as np
import pandas as pd

from data_pipeline import DataPipeline, run_pipeline
from data_pipeline.cleaner import DataCleaner
from data_pipeline.feature_engineer import FeatureEngineer
from data_pipeline.pipeline import PipelineConfig
from data_pipeline.splitter import DatasetSplitter


def create_sample_dataset(n_samples: int = 1000) -> pd.DataFrame:
    """生成示例数据集用于演示。"""
    np.random.seed(42)

    data = {
        "age": np.random.randint(18, 80, n_samples).astype(float),
        "income": np.random.normal(50000, 15000, n_samples),
        "education": np.random.choice(
            ["高中", "本科", "硕士", "博士"], n_samples, p=[0.3, 0.4, 0.2, 0.1]
        ),
        "city": np.random.choice(
            ["北京", "上海", "广州", "深圳", "其他"], n_samples, p=[0.2, 0.2, 0.15, 0.15, 0.3]
        ),
        "signup_date": pd.date_range("2020-01-01", periods=n_samples, freq="D"),
        "score": np.random.uniform(0, 100, n_samples),
    }

    df = pd.DataFrame(data)

    # 人为引入一些缺失值
    missing_idx = np.random.choice(n_samples, int(n_samples * 0.05), replace=False)
    df.loc[missing_idx, "income"] = np.nan
    df.loc[np.random.choice(n_samples, int(n_samples * 0.03), replace=False), "education"] = np.nan

    # 添加目标列（二分类标签）
    df["label"] = (
        (df["age"] > 35) & (df["income"] > 45000) & (df["score"] > 50)
    ).astype(int)

    return df


def example_basic_usage():
    """示例 1：基本用法 - 使用 run_pipeline 一行搞定。"""
    print("=" * 60)
    print("示例 1：基本用法 - run_pipeline")
    print("=" * 60)

    df = create_sample_dataset(500)
    print(f"原始数据: {df.shape}")
    print(f"列: {df.columns.tolist()}")
    print(f"缺失值: \n{df.isnull().sum()}")

    config = PipelineConfig(
        cleaning_strategy="auto",
        standardize_numeric=True,
        encode_categorical=True,
        categorical_encoding="label",
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        random_state=42,
    )

    result = run_pipeline(df, target_col="label", config=config, save=False)

    print("\n划分结果:")
    for split_name in ["train", "val", "test"]:
        print(f"  {split_name}: {result[split_name].shape}")

    print("\n训练集前3行:")
    print(result["train"].head(3))


def example_step_by_step():
    """示例 2：分步使用 - 更细粒度的控制。"""
    print("\n" + "=" * 60)
    print("示例 2：分步使用 - 细粒度控制")
    print("=" * 60)

    df = create_sample_dataset(200)

    # Step 1: 数据清洗
    print("\n1️⃣  数据清洗...")
    cleaner = DataCleaner(strategy="auto")
    cleaned = cleaner.fit_transform(df)
    print(f"   清洗后: {cleaned.shape} (移除了 {len(df) - len(cleaned)} 行缺失数据)")

    # 检测异常值
    outliers = cleaner.detect_outliers_iqr(cleaned, "income")
    print(f"   收入异常值: {outliers.sum()} 行")
    cleaned = cleaner.remove_outliers(cleaned, columns=["income"])
    print(f"   移除异常值后: {cleaned.shape}")

    # Step 2: 特征工程
    print("\n2️⃣  特征工程...")
    fe = FeatureEngineer()
    fe.fit(cleaned)

    # 标准化数值特征
    engineered = fe.standardize(cleaned)
    print(f"   数值特征标准化完成")

    # 标签编码类别特征
    engineered = fe.label_encode(cleaned)
    print(f"   类别特征标签编码完成")

    # 提取时间特征
    engineered = FeatureEngineer.extract_datetime_features(
        engineered, "signup_date", features=["year", "month", "day", "dayofweek"]
    )
    print(f"   时间特征提取完成")
    print(f"   当前特征列: {engineered.columns.tolist()}")

    # Step 3: 数据集划分
    print("\n3️⃣  数据集划分...")
    splitter = DatasetSplitter(train_ratio=0.8, val_ratio=0.1, test_ratio=0.1)

    # 分离特征和标签
    X = engineered.drop(columns=["label"])
    y = engineered["label"]
    data_with_label = pd.concat([X, y], axis=1)

    train, val, test = splitter.random_split(data_with_label, target_col="label", stratify=True)
    print(f"   训练集: {len(train)} (分层采样)")
    print(f"   验证集: {len(val)}")
    print(f"   测试集: {len(test)}")

    # 检查标签分布
    print(f"\n训练集标签分布:\n{train['label'].value_counts()}")


def example_pytorch_integration():
    """示例 3：PyTorch 集成 - 创建 DataLoader。"""
    print("\n" + "=" * 60)
    print("示例 3：PyTorch DataLoader 集成")
    print("=" * 60)

    try:
        import torch
    except ImportError:
        print("⚠️  未安装 PyTorch，跳过此示例。")
        print("   安装: pip install torch")
        return

    df = create_sample_dataset(100)

    pipeline = DataPipeline(
        PipelineConfig(
            cleaning_strategy="auto",
            encode_categorical=True,
            categorical_encoding="label",
        )
    )

    result = pipeline.run(df, target_col="label")

    from data_pipeline.splitter import PyTorchDataset

    # 为每个划分创建 Dataset 和 DataLoader
    for split_name in ["train", "val", "test"]:
        data = result[split_name]
        # 丢弃非数值列（如日期）
        numeric_data = data.select_dtypes(include=[np.number])
        y = numeric_data["label"] if "label" in numeric_data.columns else None
        X = numeric_data.drop(columns=["label"]) if "label" in numeric_data.columns else numeric_data

        dataset = PyTorchDataset(X, y, task="classification")
        dataloader = dataset.to_dataloader(batch_size=16, shuffle=(split_name == "train"))

        print(f"\n{split_name.upper()} DataLoader:")
        for batch_idx, (x_batch, y_batch) in enumerate(dataloader):
            print(f"  批次 {batch_idx + 1}: X shape={x_batch.shape}, y shape={y_batch.shape}")
            if batch_idx >= 1:  # 只显示前两个批次
                break

        print(f"  共 {len(dataloader)} 个批次 (batch_size=16)")


if __name__ == "__main__":
    print("🚀 数据处理流水线 - 使用示例\n")

    example_basic_usage()
    example_step_by_step()
    example_pytorch_integration()

    print("\n" + "=" * 60)
    print("✅ 所有示例运行完成！")
    print("=" * 60)

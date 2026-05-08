import pandas as pd
import numpy as np
import os


class DataProcessor:
    """
    M1: 数据处理模块
    负责数据加载、质量检测、清洗以及特征衍生。
    """

    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        self.quality_report = {}

    def load_data(self):
        """加载Parquet数据"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"未找到文件: {self.file_path}")
        print(f"正在加载数据: {self.file_path}...")
        self.df = pd.read_parquet(self.file_path)
        print(f"数据加载完成，共 {len(self.df)} 条记录。")

    def generate_quality_report(self):
        """生成数据质量报告（缺失率、异常值统计）"""
        report = {}
        # 1. 缺失率
        missing_rates = self.df.isnull().mean() * 100
        report['missing_rates'] = missing_rates[missing_rates > 0].to_dict()

        # 2. 异常值统计 (针对关键数值字段)
        numerical_cols = ['passenger_count', 'trip_distance', 'fare_amount', 'total_amount']
        stats = self.df[numerical_cols].describe(percentiles=[0.01, 0.99]).T
        report['outlier_stats'] = stats.to_dict('index')

        self.quality_report = report
        print("数据质量报告已生成。")
        return report

    def clean_data(self):
        """
        清洗数据逻辑及理由：
        1. 去除坐标/区域ID缺失值：确保地理分析准确性。
        2. 过滤费用异常：fare_amount 应 > 0，total_amount 应 > 0（排除撤销单或测试单）。
        3. 过滤距离异常：trip_distance 应 > 0 且在合理范围内（如 < 100英里）。
        4. 乘客人数过滤：passenger_count 应 > 0 且 <= 6（法定最大人数）。
        5. 时间过滤：仅保留 2023-01 内的数据，排除系统误差导致的跨年数据。
        """
        initial_count = len(self.df)

        # 策略 1: 时间清洗 (确保在2023年1月内)
        self.df = self.df[
            (self.df['tpep_pickup_datetime'] >= '2023-01-01') &
            (self.df['tpep_pickup_datetime'] < '2023-02-01')
            ]

        # 策略 2: 过滤金额和距离 (排除负数或极端的异常值)
        self.df = self.df[(self.df['fare_amount'] > 0) & (self.df['fare_amount'] < 500)]
        self.df = self.df[(self.df['trip_distance'] > 0) & (self.df['trip_distance'] < 100)]

        # 策略 3: 过滤乘客数 (排除0人或超载情况)
        self.df = self.df[(self.df['passenger_count'] > 0) & (self.df['passenger_count'] <= 6)]

        # 策略 4: 处理缺失值 (对关键字段进行dropna)
        self.df.dropna(subset=['PULocationID', 'DOLocationID', 'payment_type'], inplace=True)

        final_count = len(self.df)
        print(
            f"清洗完成。过滤掉 {initial_count - final_count} 条记录 ({((initial_count - final_count) / initial_count) * 100:.2f}%)。")

    def engineer_features(self):
        """
        提取时间特征与设计衍生特征
        """
        # --- 基础时间特征提取 ---
        self.df['pickup_hour'] = self.df['tpep_pickup_datetime'].dt.hour
        self.df['day_of_week'] = self.df['tpep_pickup_datetime'].dt.dayofweek  # 0=Monday
        self.df['is_weekend'] = self.df['day_of_week'].isin([5, 6]).astype(int)

        # 高峰时段定义 (工作日 08:00-10:00, 17:00-20:00)
        self.df['is_peak_hour'] = ((self.df['day_of_week'] < 5) &
                                   ((self.df['pickup_hour'].between(8, 10)) |
                                    (self.df['pickup_hour'].between(17, 20)))).astype(int)

        # --- 衍生特征 1: 平均车速 (miles per hour) ---
        # 理由：反映交通拥堵状况。
        duration_hours = (self.df['tpep_dropoff_datetime'] - self.df['tpep_pickup_datetime']).dt.total_seconds() / 3600
        # 避免除以0或极短时间导致的速度异常
        self.df['avg_speed'] = self.df['trip_distance'] / duration_hours.replace(0, np.nan)
        self.df.loc[(self.df['avg_speed'] > 80) | (self.df['avg_speed'] < 1), 'avg_speed'] = np.nan  # 过滤非人类车速

        # --- 衍生特征 2: 小费比例 (tip_fraction) ---
        # 理由：反映乘客满意度或该区域乘客的支付习惯。
        self.df['tip_fraction'] = self.df['tip_amount'] / self.df['fare_amount']

        print("特征工程完成。新增特征：pickup_hour, is_peak_hour, avg_speed, tip_fraction 等。")

    def get_processed_data(self):
        """返回处理后的DataFrame"""
        return self.df


# --- 模块运行示例 (仅用于演示，后续会被集成) ---
if __name__ == "__main__":
    # 假设文件在当前目录下
    FILE_NAME = 'yellow_tripdata_2023-01.parquet'

    processor = DataProcessor(FILE_NAME)
    try:
        processor.load_data()
        report = processor.generate_quality_report()
        # print("质量报告片段:", list(report['outlier_stats'].items())[:2])

        processor.clean_data()
        processor.engineer_features()

        final_df = processor.get_processed_data()
        print(f"处理后数据列名: {final_df.columns.tolist()}")
    except Exception as e:
        print(f"运行出错: {e}")
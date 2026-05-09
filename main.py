import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns


class DataProcessor:
    """
    M1: 数据处理模块
    功能：加载、质量分析、分步清洗、特征衍生。
    """

    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        self.total_initial_rows = 0

    def load_and_report(self):
        """
        加载数据并输出初始数据质量报告
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"未找到文件: {self.file_path}")

        self.df = pd.read_parquet(self.file_path)
        self.total_initial_rows = len(self.df)

        print("=" * 50)
        print(f"项目启动：2023年1月黄色出租车数据处理")
        print(f"原始总数据量: {self.total_initial_rows} 条")

        # 1. 缺失值统计
        missing_counts = self.df.isnull().sum()
        total_missing = missing_counts.sum()
        print(f"\n[缺失值报告]")
        for col, count in missing_counts[missing_counts > 0].items():
            percentage = (count / self.total_initial_rows) * 100
            print(f"- 字段 {col}: 缺失 {count} 条, 占比 {percentage:.4f}%")

        # 2. 异常值初步统计 (基于业务常识的极值定义)
        # 定义：行程距离<=0 或 >100; 费用<=0 或 >1000; 乘客数<=0 或 >6
        outliers_mask = (
                (self.df['trip_distance'] <= 0) | (self.df['trip_distance'] > 100) |
                (self.df['fare_amount'] <= 0) | (self.df['fare_amount'] > 1000) |
                (self.df['passenger_count'] <= 0) | (self.df['passenger_count'] > 6)
        )
        outlier_count = outliers_mask.sum()
        print(f"\n[异常值报告]")
        print(f"- 业务逻辑异常数据 (距离/金额/人数): {outlier_count} 条")
        print(f"- 异常数据占比: {(outlier_count / self.total_initial_rows) * 100:.4f}%")
        print("=" * 50)

    def clean_data_stepwise(self):
        """
        分步清洗数据：每步操作均遵循“策略说明 -> 编程实现 -> 注释解释”
        """
        print("\n开始分步清洗数据...")

        # --- 第一步策略：时间范围清洗 ---
        # 理由：Parquet文件中常含有记录设备故障产生的非2023-01月份的脏数据，需剔除。
        self.df = self.df[
            (self.df['tpep_pickup_datetime'] >= '2023-01-01') &
            (self.df['tpep_pickup_datetime'] < '2023-02-01')
            ]
        # 注释：以上代码过滤掉不属于2023年1月的订单，确保分析对象的时效准确。

        # --- 第二步策略：核心业务字段异常值清洗 ---
        # 理由：行程距离为0、费用为负或乘客数为0的数据在统计学上属于无效行程。
        self.df = self.df[
            (self.df['trip_distance'] > 0) &
            (self.df['fare_amount'] > 0) &
            (self.df['passenger_count'] > 0)
            ]
        # 注释：过滤掉无效的零/负值数据，防止均值分析被极端值拉低。

        # --- 第三步策略：地理位置ID清洗 ---
        # 理由：PULocationID和DOLocationID是后续空间分析的核心，若为Unknown(264/265)则无法分析。
        self.df = self.df[
            (~self.df['PULocationID'].isin([264, 265])) &
            (~self.df['DOLocationID'].isin([264, 265]))
            ]
        # 注释：剔除起始点未知的记录，为后续的M2/M3地理维度建模打下基础。

        # --- 第四步策略：处理缺失值 ---
        # 理由：对于乘客数或付款方式极少量的缺失，采用直接剔除法以维持数据纯净度。
        self.df.dropna(subset=['passenger_count', 'payment_type'], inplace=True)
        # 注释：移除包含空值的行，保证后续矩阵运算不产生空值报错。

        final_rows = len(self.df)
        print(
            f"清洗完成！保留有效数据: {final_rows} 条，总过滤占比: {((self.total_initial_rows - final_rows) / self.total_initial_rows) * 100:.2f}%")

    def engineer_features(self):
        """
        特征提取：基础特征 + 2个衍生特征
        """
        print("\n开始特征提取与衍生...")

        # 1. 基础特征
        self.df['pickup_hour'] = self.df['tpep_pickup_datetime'].dt.hour
        self.df['day_of_week'] = self.df['tpep_pickup_datetime'].dt.dayofweek  # 0=周一

        # 是否高峰 (工作日 8-10点, 17-20点)
        self.df['is_peak'] = ((self.df['day_of_week'] < 5) &
                              (self.df['pickup_hour'].isin([8, 9, 10, 17, 18, 19, 20]))).astype(int)

        # 2. 衍生特征提取输出说明：
        # 特征一：avg_speed (平均行驶速度，单位：英里/小时)
        # 判断指标：trip_distance / 行程时长(小时)。用于衡量路网拥堵程度。
        duration_h = (self.df['tpep_dropoff_datetime'] - self.df['tpep_pickup_datetime']).dt.total_seconds() / 3600
        self.df['avg_speed'] = self.df['trip_distance'] / duration_h
        # 限制合理车速 (1-80 mph)
        self.df = self.df[(self.df['avg_speed'] > 0) & (self.df['avg_speed'] < 80)]

        # 特征二：efficiency_score (订单创收效率)
        # 判断指标：fare_amount / (行程时长+1s)。用于衡量每单位时间产生的经济效益。
        self.df['efficiency_score'] = self.df['fare_amount'] / (duration_h * 60 + 0.01)  # 分钟收益

        print("-" * 30)
        print("【衍生特征提取报告】")
        print("1. 特征名: avg_speed | 指标: 距离/时间 | 意义: 识别交通拥堵与路况")
        print("2. 特征名: efficiency_score | 指标: 车费/时长 | 意义: 评估不同时段/地段的运营价值")
        print("-" * 30)

    def get_data(self):
        return self.df


import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib.font_manager as fm


class DataAnalyzer:
    """
    M2: 分析可视化模块
    功能：实现出行规律、区域热度、影响因素及行程经济效益洞察。
    """

    def __init__(self, df):
        self.df = df.copy()
        self.output_dir = 'outputs'
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self._setup_chinese_font()

    def _setup_chinese_font(self):
        """配置中文字体以支持中文显示"""
        fonts = ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'Heiti SC', 'STHeiti', 'Arial Unicode MS']
        for f in fonts:
            if any(f in font.name for font in fm.fontManager.ttflist):
                plt.rcParams['font.sans-serif'] = [f]
                break
        plt.rcParams['axes.unicode_minus'] = False
        sns.set_theme(style="whitegrid", font=plt.rcParams['font.sans-serif'][0])

    def _ensure_dimensions(self):
        """内部特征补全：确保绘图所需的衍生维度存在"""
        if 'day_of_week' not in self.df.columns:
            self.df['day_of_week'] = self.df['tpep_pickup_datetime'].dt.dayofweek
        if 'is_weekend' not in self.df.columns:
            self.df['is_weekend'] = self.df['day_of_week'].isin([5, 6]).astype(int)

    def analyze_time_patterns(self):
        """1. 出行需求时间规律"""
        print("执行分析 1: 出行需求时间规律...")
        self._ensure_dimensions()
        time_stats = self.df.groupby(['pickup_hour', 'is_weekend']).size().reset_index(name='count')
        time_stats['日期类型'] = time_stats['is_weekend'].map({0: '工作日', 1: '周末'})

        plt.figure(figsize=(12, 6))
        sns.lineplot(data=time_stats, x='pickup_hour', y='count', hue='日期类型', marker='o')
        plt.title('2023年1月纽约出租车：分时段订单趋势', fontsize=14)
        plt.xlabel('小时 (0-23)')
        plt.ylabel('订单总量')
        plt.savefig(f'{self.output_dir}/m2_1_time_patterns.png', dpi=300, bbox_inches='tight')
        plt.close()

    def analyze_location_hotspots(self):
        """2. 区域热度分析"""
        print("执行分析 2: 区域热度分析...")
        top_10_zones = self.df['PULocationID'].value_counts().head(10).index
        hot_df = self.df[self.df['PULocationID'].isin(top_10_zones)]
        pivot_table = hot_df.pivot_table(index='PULocationID', columns='pickup_hour', values='VendorID',
                                         aggfunc='count', fill_value=0)

        plt.figure(figsize=(14, 7))
        sns.heatmap(pivot_table, cmap='YlGnBu', cbar_kws={'label': '订单热度'})
        plt.title('Top 10 上客核心区域的小时流量分布', fontsize=14)
        plt.xlabel('时段')
        plt.ylabel('区域代码 (PULocationID)')
        plt.savefig(f'{self.output_dir}/m2_2_location_hotspots.png', dpi=300, bbox_inches='tight')
        plt.close()

    def analyze_fare_factors(self):
        """3. 车费影响因素分析"""
        print("执行分析 3: 车费影响因素分析...")
        sample_df = self.df.sample(n=min(20000, len(self.df)), random_state=42)
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=sample_df, x='trip_distance', y='fare_amount', alpha=0.2, color='teal')
        plt.title('行程距离与车费金额关联性分析', fontsize=14)
        plt.xlabel('行程距离 (英里)')
        plt.ylabel('基础车费 (美元)')
        plt.xlim(0, self.df['trip_distance'].quantile(0.99))
        plt.ylim(0, self.df['fare_amount'].quantile(0.99))
        plt.savefig(f'{self.output_dir}/m2_3_fare_factors.png', dpi=300, bbox_inches='tight')
        plt.close()

    def analyze_insight_value(self):
        """
        4. 自选价值分析（新）：不同距离区间的订单效率分析
        分析目的：识别哪些长度的订单能产生最高的“每分钟收益”，为司机接单策略提供参考。
        """
        print("执行分析 4: 智能化运营 - 行程距离对每分钟收益效率的影响...")

        # 将距离划分为不同区间 (Binning)
        bins = [0, 2, 5, 10, 20, 100]
        labels = ['超短途(0-2)', '短途(2-5)', '中途(5-10)', '远途(10-20)', '超远途(20+)']
        temp_df = self.df.copy()
        temp_df['距离区间'] = pd.cut(temp_df['trip_distance'], bins=bins, labels=labels)

        plt.figure(figsize=(10, 6))
        # 绘制不同距离区间的平均效率得分 (efficiency_score 由 M1 定义)
        sns.barplot(data=temp_df, x='距离区间', y='efficiency_score', palette='viridis', hue='距离区间', legend=False)

        plt.title('订单运营效率随行程距离的变化趋势', fontsize=14)
        plt.ylabel('每分钟收益 (美元/分钟)')
        plt.xlabel('行程距离区间 (英里)')

        # 排除效率得分的极端异常值对均值显示的影响
        plt.ylim(0, temp_df['efficiency_score'].quantile(0.95))

        plt.savefig(f'{self.output_dir}/m2_4_efficiency_insight.png', dpi=300, bbox_inches='tight')
        plt.close()


import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


# ==========================================
# M3: 预测模型模块 (双图独立输出版)
# ==========================================
class DemandPredictor:
    """
    M3: 预测模型模块
    功能：构建神经网络预测出行需求，与随机森林对比。
    变更：将 Loss 曲线与预测对比图拆分为两个独立的图片文件输出。
    """

    def __init__(self, df):
        self.df = df.copy()
        self.output_dir = 'outputs'
        self.model_nn = None
        self.history = None
        self.scaler = StandardScaler()

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _prepare_demand_data(self):
        """聚合数据：按区域和小时统计需求"""
        print("\n[M3] 正在构建区域时段需求量特征...")
        self.df['pickup_date'] = self.df['tpep_pickup_datetime'].dt.date
        self.df['pickup_hour'] = self.df['tpep_pickup_datetime'].dt.hour

        agg_data = self.df.groupby(['PULocationID', 'pickup_date', 'pickup_hour']).size().reset_index(name='demand')
        agg_data['pickup_date'] = pd.to_datetime(agg_data['pickup_date'])
        agg_data['day_of_week'] = agg_data['pickup_date'].dt.dayofweek

        X = agg_data[['PULocationID', 'pickup_hour', 'day_of_week']]
        y = agg_data['demand']
        return train_test_split(X, y, test_size=0.2, random_state=42)

    def run_comparison_experiment(self):
        """执行对比实验"""
        X_train, X_test, y_train, y_test = self._prepare_demand_data()

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # 1. 神经网络 (TensorFlow/Keras)
        import tensorflow as tf
        from tensorflow.keras import layers, models, Input

        print(f"[M3] 开始训练神经网络模型 (TF {tf.__version__})...")
        model = models.Sequential([
            Input(shape=(X_train_scaled.shape[1],)),
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(64, activation='relu'),
            layers.Dense(32, activation='relu'),
            layers.Dense(1)
        ])

        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        self.history = model.fit(
            X_train_scaled, y_train,
            epochs=30, batch_size=256, validation_split=0.1, verbose=0
        )
        self.model_nn = model

        # 2. 随机森林
        print("[M3] 开始训练随机森林对比模型...")
        rf = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)

        # 3. 评估指标
        y_pred_nn = self.model_nn.predict(X_test_scaled).flatten()
        y_pred_rf = rf.predict(X_test)

        results = {
            '神经网络': {
                'MAE': mean_absolute_error(y_test, y_pred_nn),
                'RMSE': np.sqrt(mean_squared_error(y_test, y_pred_nn))
            },
            '随机森林': {
                'MAE': mean_absolute_error(y_test, y_pred_rf),
                'RMSE': np.sqrt(mean_squared_error(y_test, y_pred_rf))
            }
        }

        self._report_and_save_plots(y_test, y_pred_nn, y_pred_rf, results)

    def _report_and_save_plots(self, y_test, y_nn, y_rf, results):
        """独立保存两张中文图表"""
        # 打印文字报告
        print("\n" + "=" * 50)
        print(f"{'模型':<14} | {'MAE (平均误差)':<12} | {'RMSE (根均误差)':<12}")
        print("-" * 50)
        for name, m in results.items():
            print(f"{name:<12} | {m['MAE']:<14.4f} | {m['RMSE']:<14.4f}")
        print("=" * 50)

        # 设置中文字体（确保与M2逻辑一致）
        plt.rcParams['axes.unicode_minus'] = False

        # --- 图表 1: 训练 Loss 曲线 ---
        plt.figure(figsize=(10, 6))
        plt.plot(self.history.history['loss'], label='训练集损失', color='blue')
        plt.plot(self.history.history['val_loss'], label='验证集损失', color='orange')
        plt.title('神经网络训练损失收敛趋势 (MSE)', fontsize=14)
        plt.xlabel('训练轮次 (Epoch)')
        plt.ylabel('损失值')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(f'{self.output_dir}/m3_loss_curve.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"[M3] 损失曲线图已保存至: {self.output_dir}/m3_loss_curve.png")

        # --- 图表 2: 预测拟合对比 ---
        plt.figure(figsize=(12, 6))
        sample_idx = 100
        plt.plot(y_test.values[:sample_idx], label='真实需求量', color='black', alpha=0.4, linewidth=2)
        plt.plot(y_nn[:sample_idx], label='神经网络预测', linestyle='--', color='red', alpha=0.8)
        plt.plot(y_rf[:sample_idx], label='随机森林预测', linestyle=':', color='green', alpha=0.8)
        plt.title('出行需求预测拟合对比 (局部采样)', fontsize=14)
        plt.xlabel('测试样本索引')
        plt.ylabel('订单需求数')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(f'{self.output_dir}/m3_prediction_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"[M3] 预测对比图已保存至: {self.output_dir}/m3_prediction_comparison.png")


# 优劣分析文档总结 (将作为文档输出)
"""
[M3 任务总结：算法对比分析]
1. 神经网络: 在处理复杂的时空特征（如多维度ID与时间的交互）时具有更强的非线性拟合能力。
2. 随机森林: 具有极强的鲁棒性，在小规模聚合数据上表现出色，且不容易受到数据噪声干扰。
3. 业务应用: 建议在流量极大的核心区域（如曼哈顿中心）使用神经网络模型，在订单稀疏区域使用随机森林。
"""

# ==========================================
# 保持原有 M1, M2 的 Main 逻辑调用不改动
# ==========================================
if __name__ == "__main__":
    # --- M1 & M2 (保持原样调用) ---
    processor = DataProcessor('yellow_tripdata_2023-01.parquet')
    processor.load_and_report()
    processor.clean_data_stepwise()
    processor.engineer_features()
    clean_df = processor.get_data()

    if clean_df is not None:
        analyzer = DataAnalyzer(clean_df)
        analyzer.analyze_time_patterns()
        analyzer.analyze_location_hotspots()
        analyzer.analyze_fare_factors()
        analyzer.analyze_insight_value()

        # --- M3 任务启动 ---
        predictor = DemandPredictor(clean_df)
        predictor.run_comparison_experiment()
# 导入库
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm



"""
-----------------------
M1: 数据处理
-----------------------
"""

# 对数据进行提取封装

class DataProcessor:

# 读取文件数据并储存
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        self.total_initial_rows = 0
    def load_and_report(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"未找到文件: {self.file_path}")
        self.df = pd.read_parquet(self.file_path)
        self.total_initial_rows = len(self.df)

        print(f"黄色出租车出行数据问答系统\n（回答主要基于2023年1月的相关数据生成）")
        print("-" * 50)
        print(f"数据预处理：\n一、异常数据统计")
        print(f"1.原始总数据量共{self.total_initial_rows} 条")

        # 1. 缺失值统计
        missing_counts = self.df.isnull().sum()         #记录缺失数据的个数
        total_missing = missing_counts.sum()
        print(f"2.原始数据缺失情况：")
        i = 0
        for col, count in missing_counts[missing_counts > 0].items():
            percentage = (count / self.total_initial_rows) * 100
            i += 1
            print(f"({i}) {col}项共有{count}条数据缺失,在总数据中占比为{percentage:.4f}%；")

        # 2. 数据值异常初步统计
        # 筛选数据规则：满足以下任一条件的数据记为异常值
        # （1） 行程距离<=0或>=200;
        # （2） 费用<=0或>=1000;
        # （3） 乘客数<=0或>=6。
        # 每种情况数据条数分别统计和总计
        dist_mask = (self.df['trip_distance'] <= 0) | (self.df['trip_distance'] >= 200)
        fare_mask = (self.df['fare_amount'] <= 0) | (self.df['fare_amount'] >= 1000)
        pass_mask = (self.df['passenger_count'] <= 0) | (self.df['passenger_count'] >= 6)
        outliers_mask = dist_mask | fare_mask | pass_mask
        outlier_count = outliers_mask.sum()

        print(f"3.原始数据异常情况：")
        print(
            f"（1）行程距离异常:共{dist_mask.sum()}条，占比：{(dist_mask.sum() / self.total_initial_rows) * 100:.4f}%")
        print(
            f"（2）行程金额异常：共{fare_mask.sum()}条，占比：{(fare_mask.sum() / self.total_initial_rows) * 100:.4f}%")
        print(
            f"（3）乘客人数异常：共{pass_mask.sum()}条，占比：{(pass_mask.sum() / self.total_initial_rows) * 100:.4f}%")
        print(f"异常数据共{outlier_count} 条")
        print(f"总异常数据占比：{(outlier_count / self.total_initial_rows) * 100:.4f}%")

# 数据清洗
    def clean_data_stepwise(self):
        # --- 第一步：处理缺失值 ---
        # 将有缺失值的数据直接剔除，以维持数据纯净度
        self.df.dropna(subset=['passenger_count', 'payment_type'], inplace=True)
        # 移除包含空值的行，保证后续运算不产生空值报错

        # --- 第二步：时间范围异常数据清洗 ---
        # 若文件中含有记录设备故障产生的非2023-01月份的数据，则需要剔除
        self.df = self.df[
            (self.df['tpep_pickup_datetime'] >= '2023-01-01') &
            (self.df['tpep_pickup_datetime'] < '2023-02-01')
            ]
        # 以上代码过滤掉不属于2023年1月的订单，确保分析对象的时效准确。

        # --- 第三步：不合常理数据异常值清洗 ---
        # 数据在上面被标记为异常的数据值不符合实际运行实际/与通常情况偏差较大，极端数据容易影响整体统计学结果，应当剔除
        self.df = self.df[
            (self.df['trip_distance'] > 0) & (self.df['trip_distance'] < 200)&
            (self.df['fare_amount'] > 0) & (self.df['fare_amount'] < 1000)&
            (self.df['passenger_count'] > 0) & (self.df['passenger_count'] < 6)
            ]
        # 以上代码过滤掉异常值数据，防止均值分析被极端值影响

        # --- 第四步：地理位置未知数据清洗 ---
        # PULocationID和DOLocationID是后续空间分析的核心，若为Unknown(264/265)则无法分析
        self.df = self.df[
            (~self.df['PULocationID'].isin([264, 265])) &
            (~self.df['DOLocationID'].isin([264, 265]))
            ]
        # 剔除行程起始点未知的记录，保证后续对路况的分析正确

        final_rows = len(self.df)   #记录剩下的数据
        print(
            f"数据清洗后保留有效数据共{final_rows}条，总过滤占比:{((self.total_initial_rows - final_rows) / self.total_initial_rows) * 100:.2f}%")
# 特征提取
#此处两个衍生特征为
# 1.avg_speed(平均行驶速度，单位：英里/小时)
# 2.efficiency_score(订单创收效率)
    def engineer_features(self):
        # 1.基础特征提取
        self.df['pickup_hour'] = self.df['tpep_pickup_datetime'].dt.hour    #小时
        self.df['day_of_week'] = self.df['tpep_pickup_datetime'].dt.dayofweek  # 星期几（0=周一）
        # 是否高峰(为方便判断，仅根据日常经验将工作日8-10点和17-20点之间记为高峰时段)
        self.df['is_peak'] = ((self.df['day_of_week'] < 5) &
                              (self.df['pickup_hour'].isin([8, 9, 10, 17, 18, 19, 20]))).astype(int)

        # 2. 衍生特征提取：
        # （1）avg_speed=trip_distance/duration_h(行程时长)
        # 平均行驶速度（单位：英里/小时)用于衡量路网拥堵程度，识别交通拥堵与路况
        duration_h = (self.df['tpep_dropoff_datetime'] - self.df['tpep_pickup_datetime']).dt.total_seconds() / 3600
        self.df['avg_speed'] = self.df['trip_distance'] / duration_h
        # 限制合理车速 (1-80mph)
        self.df = self.df[(self.df['avg_speed'] > 0) & (self.df['avg_speed'] < 80)]

        # （2）efficiency_score(订单创收效率)=fare_amount/duration_h(行程时长+1s)
        # 用于衡量每单位时间产生的经济效益，评估不同时段/地段的运营价值
        self.df['efficiency_score'] = self.df['fare_amount'] / (duration_h * 60 + 0.01)  # 分钟收益
        print("-" * 50)

    def get_data(self):
        return self.df


"""
-----------------------
M2:分析可视化
-----------------------
"""
class DataAnalyzer:
    # 新建output目录
    def __init__(self, df):
        self.df = df.copy()
        self.output_dir = 'outputs'
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self._setup_chinese_font()

    def _setup_chinese_font(self):
        # 配置中文字体以支持中文显示
        #（注：此段是在中文无法正常显示情况下，寻求AI帮助，AI提供的解决方案，能够兼容更多种图标中文显示异常的问题）
        fonts = ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'Heiti SC', 'STHeiti', 'Arial Unicode MS']
        for f in fonts:
            if any(f in font.name for font in fm.fontManager.ttflist):
                plt.rcParams['font.sans-serif'] = [f]
                break
        plt.rcParams['axes.unicode_minus'] = False
        sns.set_theme(style="whitegrid", font=plt.rcParams['font.sans-serif'][0])

    #进行内部特征的补全，以确保绘图所需的横纵坐标内容存在
    def _ensure_dimensions(self):
        if 'day_of_week' not in self.df.columns:
            self.df['day_of_week'] = self.df['tpep_pickup_datetime'].dt.dayofweek
        if 'is_weekend' not in self.df.columns:
            self.df['is_weekend'] = self.df['day_of_week'].isin([5, 6]).astype(int)

    # 1.出行需求时间规律
    def analyze_time_patterns(self):
        self._ensure_dimensions()
        time_stats = self.df.groupby(['pickup_hour', 'is_weekend']).size().reset_index(name='count')
        time_stats['日期类型'] = time_stats['is_weekend'].map({0: '工作日', 1: '周末'})
        plt.figure(figsize=(12, 6))
        sns.lineplot(data=time_stats, x='pickup_hour', y='count', hue='日期类型', marker='o')
        plt.title('2023年1月纽约黄色出租车：分时段订单量趋势', fontsize=14)
        plt.xlabel('小时 (0-23)')
        plt.ylabel('订单总量')
        plt.savefig(f'{self.output_dir}/分小时平均订单量折线图.png', dpi=300, bbox_inches='tight')
        plt.close()

    # 2.区域热度分析
    def analyze_location_hotspots(self):
        top_10_zones = self.df['PULocationID'].value_counts().head(10).index
        hot_df = self.df[self.df['PULocationID'].isin(top_10_zones)]
        pivot_table = hot_df.pivot_table(index='PULocationID', columns='pickup_hour', values='VendorID',
                                         aggfunc='count', fill_value=0)
        plt.figure(figsize=(14, 7))
        sns.heatmap(pivot_table, cmap='YlGnBu', cbar_kws={'label': '订单热度'})
        plt.title('Top10上客核心区域的小时流量分布', fontsize=14)
        plt.xlabel('时段')
        plt.ylabel('区域代码 (PULocationID)')
        plt.savefig(f'{self.output_dir}/上下客量最高的 TOP 10 区域及高峰时段分布热力图.png', dpi=300, bbox_inches='tight')
        plt.close()

    # 3.车费影响因素分析
    def analyze_fare_factors(self):
        sample_df = self.df
        # (1)行程距离-车费
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=sample_df, x='trip_distance', y='fare_amount', alpha=0.2, color='teal')
        plt.title('行程距离与车费金额关联性分析', fontsize=14)
        plt.xlabel('行程距离 (英里)')
        plt.ylabel('基础车费 (美元)')
        plt.xlim(0, self.df['trip_distance'].quantile(0.99))
        plt.ylim(0, self.df['fare_amount'].quantile(0.99))
        plt.savefig(f'{self.output_dir}/行程距离-车费散点图.png', dpi=300, bbox_inches='tight')
        plt.close()

        # (2)出行时段-车费
        plt.figure(figsize=(14, 8))
        # 1.数据预处理：克隆一份数据并计算阶梯
        plot_df = self.df.copy()
        # 将车费按10美元阶梯向下取整（如 15.5 -> 10, 25.0 -> 20）
        plot_df['fare_step'] = (np.floor(plot_df['fare_amount'] / 10) * 10).astype(int)
        # 2.限制纵坐标范围：只看 0-150 美元的主流区间，避免极端值压缩图表
        max_display_fare = 150
        plot_df = plot_df[plot_df['fare_step'] <= max_display_fare]
        # 3.使用 stripplot 绘制。其逻辑与乘客人数图一致：
        # x轴为小时，y轴为阶梯化的车费
        sns.stripplot(
            data=plot_df,
            x='pickup_hour',
            y='fare_step',
            hue='fare_step',  # 根据费用阶梯着色
            palette='magma',  # 使用渐变色色板
            alpha=0.15,  # 降低透明度，重叠处颜色更深，反映数据密度
            jitter=0.4,  # 开启横向随机抖动，避免点连成直线
            size=1.5,  # 缩小点的大小
            legend=False  # 阶梯较多，关闭图例使画面清爽
        )
        plt.title('2023年1月纽约出租车：分时段车费分布规律 (10美元阶梯分类)', fontsize=14)
        plt.xlabel('出发时段 (24小时制)', fontsize=12)
        plt.ylabel('基础车费阶梯 (美元)', fontsize=12)
        # 设置纵坐标刻度：每10美元显示一个标签
        plt.yticks(range(0, max_display_fare + 10, 10))
        # 添加水平网格线，方便对照阶梯
        plt.grid(True, axis='y', linestyle=':', alpha=0.6)
        plt.savefig(f'{self.output_dir}/时段-车费阶梯抖动散点图.png', dpi=300, bbox_inches='tight')
        plt.close()

        # (3)乘客人数-车费
        plt.figure(figsize=(10, 6))
        # 乘客人数是离散值，使用stripplot(抖动散点图)观察分布更清晰
        sns.stripplot(data=sample_df, x='passenger_count', y='fare_amount', alpha=0.2, palette='Set2',
                          hue='passenger_count', legend=False,size=0.1)
        plt.title('乘客人数与车费金额关联性分析', fontsize=14)
        plt.xlabel('乘客人数 (人)')
        plt.ylabel('基础车费 (美元)')
        plt.ylim(0, self.df['fare_amount'].quantile(0.99))
        plt.savefig(f'{self.output_dir}/乘客数-车费散点图.png', dpi=300, bbox_inches='tight')
        plt.close()

    # 4.自选分析：不同供应商的行程距离-车费趋势对比
    # 分析目的：观察不同服务商在计费规律上是否存在显著差异
    def analyze_insight_value(self):
        # 为保证折线图平滑且具有代表性，先对距离进行四舍五入取整
        temp_df = self.df.copy()
        temp_df['dist_rounded'] = temp_df['trip_distance'].round(0)
        # 过滤掉极端长途数据，只保留95%的距离范围以便观察主流趋势
        max_dist = temp_df['trip_distance'].quantile(0.95)
        plot_df = temp_df[temp_df['dist_rounded'] <= max_dist]
        plt.figure(figsize=(12, 7))
        # 使用lineplot自动计算均值和置信区间（阴影部分）
        sns.lineplot(data=plot_df, x='dist_rounded', y='fare_amount', hue='VendorID',
                         marker='o', palette='Set1', linewidth=2)
        plt.title('不同供应商(VendorID)行程距离与平均车费变化趋势', fontsize=14)
        plt.ylabel('平均基础车费 (美元)')
        plt.xlabel('行程距离 (整数英里)')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend(title='供应商ID')
        plt.savefig(f'{self.output_dir}/不同供应商的行程距离-车费折线图.png', dpi=300, bbox_inches='tight')
        plt.close()


# 新导入库
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import re




"""
-----------------------
M3:预测模型
-----------------------
"""

class DemandPredictor:
    def __init__(self, df):
        self.df = df.copy()
        self.output_dir = 'outputs'
        self.model_nn = None
        self.history = None
        self.scaler = StandardScaler()      # 因为神经网络对数值大小敏感，所以通过Scaler把不同量级的数据缩放到统一量纲
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

#聚合数据，按区域和小时统计需求
    def _prepare_demand_data(self):
        # 提取日期和小时，按这两个指标分析预测某时段的出行需求量
        self.df['pickup_date'] = self.df['tpep_pickup_datetime'].dt.date
        self.df['pickup_hour'] = self.df['tpep_pickup_datetime'].dt.hour

        # 把离散的订单记录转换成与时间、空间关联的订单数目统计数据，便于后续学习分析预测
        agg_data = self.df.groupby(['PULocationID', 'pickup_date', 'pickup_hour']).size().reset_index(name='demand')
        agg_data['pickup_date'] = pd.to_datetime(agg_data['pickup_date'])
        agg_data['day_of_week'] = agg_data['pickup_date'].dt.dayofweek

        # X是输入层内容：时间和空间；
        # Y是输出层内容：需求量
        X = agg_data[['PULocationID', 'pickup_hour', 'day_of_week']]
        y = agg_data['demand']

        # 划分训练/测试集（8:2）
        return train_test_split(X, y, test_size=0.2, random_state=42)
# 构建两个不同的预测模型对某区域某时段的出行需求量进行预测
    def run_comparison_experiment(self):
        # 训练集数据预处理
        X_train, X_test, y_train, y_test = self._prepare_demand_data()
        # 把数据标准化，避免梯度爆炸
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # 1.神经网络(TensorFlow)
        import tensorflow as tf
        from tensorflow.keras import layers, models, Input

        print(f"开始训练神经网络模型(TF{tf.__version__})")
        # 构建1层输入层，3层隐藏层，1层输出层的神经网络模型
        model = models.Sequential([
            Input(shape=(X_train_scaled.shape[1],)),
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(64, activation='relu'),
            layers.Dense(32, activation='relu'),
            layers.Dense(1)  #最后输出预测数值
        ])

        # 将神经网络模型训练30轮
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        self.history = model.fit(
            X_train_scaled, y_train,
            epochs=50, batch_size=256, validation_split=0.1, verbose=0
        )
        self.model_nn = model

        # 2.随机森林
        print("开始训练随机森林对比模型")
        rf = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        self.model_rf = rf

        # 3.对两个模型预测结果进行误差分析
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

# 打印两个预测模型的误差分析数据
    def _report_and_save_plots(self, y_test, y_nn, y_rf, results):
        print("\n" + "=" * 50)
        print(f"{'模型':<13} | {'MAE (平均误差)':<12} | {'RMSE (根均误差)':<12}")
        print("-" * 50)
        for name, m in results.items():
            print(f"{name:<12} | {m['MAE']:<14.4f} | {m['RMSE']:<14.4f}")
        print("=" * 50)

        plt.rcParams['axes.unicode_minus'] = False

        # 图表 1:神经网络loss曲线
        plt.figure(figsize=(10, 6))
        plt.plot(self.history.history['loss'], label='训练集损失', color='blue')
        plt.plot(self.history.history['val_loss'], label='验证集损失', color='orange')
        plt.title('神经网络训练损失收敛趋势 (MSE)', fontsize=14)
        plt.xlabel('训练轮次 (Epoch)')
        plt.ylabel('损失值')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(f'{self.output_dir}/神经网络loss曲线.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 图表 2:两个预测模型误差数据可视化对比
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
        plt.savefig(f'{self.output_dir}/预测模型误差对比.png', dpi=300, bbox_inches='tight')
        plt.close()


# 导入新库
import re
import dashscope
from http import HTTPStatus



"""
-----------------------
M4: 问答接口
-----------------------
"""


class QAInterface:
    def __init__(self, df, predictor, processor):
        self.df = df
        self.predictor = predictor
        self.processor = processor
        self.output_dir = 'outputs'
        self.api_key = "sk-c43d8bebc0264d8d97f8564f440cde59"
        dashscope.api_key = self.api_key

    def _call_llm_fallback(self, query, context_data=None):
        system_prompt = (
            "你是一个2023年1月纽约出租车数据分析专家。请根据以下已知数据回答用户问题。"
            f"已知统计信息：原始数据{self.processor.total_initial_rows}条。 "
            "回答要求：简洁专业，若涉及距离，请注意1公里约等于0.62英里。"
        )
        try:
            response = dashscope.Generation.call(
                model=dashscope.Generation.Models.qwen_turbo,
                prompt=f"{system_prompt}\n用户问题：'{query}'\n上下文数据：{context_data if context_data else '无'}"
            )
            if response.status_code == HTTPStatus.OK:
                return f"\n【AI深度解析】\n{response.output.text}"
            return "\n（提示：云端大脑响应异常，请尝试查询具体统计项。）"
        except Exception as e:
            return f"\n（接口异常：{str(e)}）"

    def analyze_query(self, user_input):
        print("\n" + "=" * 50)

        # 预处理：识别单位转换
        unit_info = ""
        if "公里" in user_input:
            unit_info = "（检测到公里单位，已按1公里=0.62英里折算）"

        # 类型0：元数据/异常查询
        if re.search(r"(异常|缺失|过滤|剩下|多少条|数据量)", user_input):
            total_rows = self.processor.total_initial_rows
            current_rows = len(self.df)
            filtered_rows = total_rows - current_rows

            print("【统计结论】：")
            print(f"- 原始总数据量：{total_rows} 条")
            print(f"- 剔除异常/缺失记录：{filtered_rows} 条")
            print(f"- 当前可用纯净数据：{current_rows} 条")
            print(f"\n【关联图表】：请查看控制台初始运行时的“异常数据统计”文字报告。")
            print(self._call_llm_fallback(user_input, context_data=f"原始{total_rows},剩余{current_rows}"))

        # 类型1：时段查询
        elif re.search(r"(几点|小时|时段|什么时候)", user_input):
            target_hour = input("请输入0-23的小时(默认14时):").strip() or "14"
            if target_hour.isdigit() and 0 <= int(target_hour) <= 23:
                h = int(target_hour)
                count = len(self.df[self.df['pickup_hour'] == h])
                print(f"【统计结论】：{h}:00 时段共有订单 {count} 条。")
                print(f"【关联图表】：{self.output_dir}/分小时平均订单量折线图.png")
            else:
                print("输入无效。")

        # 类型2：区域排名
        elif re.search(r"(区域|哪儿|哪里|排名|最火|核心)", user_input):
            top_zones = self.df['PULocationID'].value_counts().head(5)
            print(f"【统计结论】：1月份最繁忙的Top 5区域ID及订单数：\n{top_zones.to_string()}")
            print(f"\n【关联图表】：{self.output_dir}/上下客量最高的TOP 10区域及高峰时段分布热力图.png")

        # 类型3：需求预测
        elif re.search(r"(预测|未来|趋势|模型)", user_input):
            params = input("请输入'区域ID, 小时, 星期'(如 138, 18, 4): ").replace('，', ',').split(',')
            if len(params) == 3:
                try:
                    loc_id, hour, dow = [int(p.strip()) for p in params]
                    input_data = pd.DataFrame([[loc_id, hour, dow]],
                                              columns=['PULocationID', 'pickup_hour', 'day_of_week'])
                    input_scaled = self.predictor.scaler.transform(input_data)
                    pred_nn = self.predictor.model_nn.predict(input_scaled, verbose=0)[0][0]
                    print(f"【预测结论】：该场景下预计订单需求量为 {max(0, pred_nn):.2f} 单。")
                    print(f"【关联图表】：{self.output_dir}/预测模型误差对比.png")
                except:
                    print("输入格式有误。")

        # 类型4：费用预估
        elif re.search(r"(钱|费|价格|多少金额|买单)", user_input):
            print(f"【系统信息】：{unit_info}")
            params = input("格式'人数, 距离': ").replace('，', ',').split(',')
            if len(params) == 2:
                try:
                    p_count, dist_input = int(params[0]), float(params[1])
                    if "公里" in user_input: dist_input *= 0.62137

                    similar = self.df[(self.df['passenger_count'] == p_count) &
                                      (self.df['trip_distance'].between(dist_input * 0.8, dist_input * 1.2))]

                    if not similar.empty:
                        avg_f = similar['fare_amount'].mean()
                        print(f"【统计结论】：{p_count}人行驶约{dist_input:.2f}英里的平均车费为 ${avg_f:.2f}")
                    else:
                        print("【统计结论】：样本库中暂无极其相近的订单，正在请求AI估算...")

                    print(f"【关联图表】：")
                    print(f"- 距离因素：{self.output_dir}/行程距离-车费散点图.png")
                    print(f"- 时段因素：{self.output_dir}/时段-车费阶梯抖动散点图.png")

                    if similar.empty: print(self._call_llm_fallback(f"{p_count}人走{dist_input}英里"))
                except:
                    print("输入数值无效。")

        # 类型5：运营效率
        elif re.search(r"(划算|效率|收益|赚钱)", user_input):
            avg_eff = self.df['efficiency_score'].mean()
            max_eff_hour = self.df.groupby('pickup_hour')['efficiency_score'].mean().idxmax()
            print(f"【分析结论】：本月平均分钟收益为${avg_eff:.2f}/min。")
            print(f"【最佳建议】：从效率看，{max_eff_hour}:00是运营最理想的时段。")
            print(f"【关联图表】：{self.output_dir}/不同供应商的行程距离-车费折线图.png (观察成本/收益趋势)")

        else:
            print("链接大模型深度思考中")
            print(self._call_llm_fallback(user_input))

    def run_loop(self):
        print("\n" + "*" * 50)
        print("纽约出租车数据智能问答系统")
        print("*" * 50)
        while True:
            user_input = input("\n请输入您的问题(退出请输入'退出','quit'或'exit')：").strip()
            if user_input.lower() in ['退出', 'quit', 'exit']: break
            if not user_input: continue
            self.analyze_query(user_input)




"""
-----------------------
调用各部分功能
-----------------------
"""

if __name__ == "__main__":
    # 调用M1
    processor = DataProcessor('yellow_tripdata_2023-01.parquet')
    processor.load_and_report()
    processor.clean_data_stepwise()
    processor.engineer_features()
    clean_df = processor.get_data()
    if clean_df is not None:
        # 调用M2
        analyzer = DataAnalyzer(clean_df)
        analyzer.analyze_time_patterns()
        analyzer.analyze_location_hotspots()
        analyzer.analyze_fare_factors()
        analyzer.analyze_insight_value()
        # 调用M3
        predictor = DemandPredictor(clean_df)
        predictor.run_comparison_experiment()
        # 调用M4
        qa_system = QAInterface(clean_df, predictor, processor)
        qa_system.run_loop()
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time

class MAStopLossBacktest:
    """
    均线金叉死叉策略+止损的量化回测类
    生成股价数据、计算均线、生成交易信号，计算收益以及夏普比率，可视化
    """
    def __init__(self, start_date='2025-01-01', end_date='2025-12-31', 
                 init_price=100.0,              stop_loss_threshold=-0.05, 
                 risk_free_rate=0.03,           ma5_window=5, 
                 ma20_window=20,                random_seed=101):
        """
        初始化回测参数
         start_date: 回测开始日期
         end_date: 回测结束日期
         init_price: 初始股价
         stop_loss_threshold: 止损阈值 默认-5%
         risk_free_rate: 无风险收益率 默认3%
         ma5_window: 5日均线窗口
         ma20_window: 20日均线窗口
         random_seed: 随机种子
        """
        # 类的基础参数
        self.start_date = start_date
        self.end_date = end_date
        self.init_price = init_price
        self.stop_loss_threshold = stop_loss_threshold
        self.risk_free_rate = risk_free_rate
        self.ma5_window = ma5_window
        self.ma20_window = ma20_window
        self.random_seed = random_seed
        
        # 初始化类中实例属性
        self.stock_df = None                          # 核心数据框
        self.day_count = None                         # 交易日数量
        self.annual_strategy_return = None            # 年化策略收益
        self.annual_volatility = None                 # 年化波动率
        self.sharpe_ratio = None                      # 夏普比率
        self.total_benchmark_return = None            # 基准收益
        self.total_strategy_return = None             # 策略最终收益
        self.run_time = None                          # 程序运行时间

    def generate_stock_data(self)->None:
        np.random.seed(self.random_seed)
        # 生成交易日  freq='B'即跳过周末
        date_list = pd.date_range(start=self.start_date, end=self.end_date, freq='B')
        self.day_count = len(date_list)
        
        # 生成涨跌幅和股价
        daily_change = np.random.uniform(-0.02, 0.02, self.day_count)      #每日涨幅
        price_np = np.ones(self.day_count) * self.init_price             
        price_np[1:] = self.init_price * np.cumprod(1 + daily_change[1:])  #每日股价
        price_list = price_np.tolist()                          # numpy 数组转成 Python 列表
        
        # 构建数据框  后续计算使用数据都基于此数据框
        self.stock_df = pd.DataFrame({
            '交易日期': date_list,
            '股票收盘价': price_list
        }).set_index('交易日期')


     #计算均线和均线差值
    def calculate_ma(self)->None: 
        roll5 = self.stock_df['股票收盘价'].rolling(window=self.ma5_window)   #滚轮对象 截取五个数据
        roll20 = self.stock_df['股票收盘价'].rolling(window=self.ma20_window)
        self.stock_df['5日均线价格'] = roll5.mean()
        self.stock_df['20日均线价格'] = roll20.mean()
        self.stock_df['均线差值'] = self.stock_df['5日均线价格'] - self.stock_df['20日均线价格']


   # 生成交易信号（金叉买入、死叉卖出）以及止损逻辑
    def generate_trade_signal(self)->None:
       
        # 初始化交易信号
        self.stock_df['交易信号'] = np.nan
        
        # 金叉买入（1）：前一天，5 日均线在 20 日均线之下，且今天5 日均线已经上穿到 20 日均线之上。
        #反之死叉卖出（0）
        buy_condition = (self.stock_df['均线差值'].shift(1) < 0) & (self.stock_df['均线差值'] >= 0)
        sell_condition = (self.stock_df['均线差值'].shift(1) > 0) & (self.stock_df['均线差值'] <= 0)
        self.stock_df.loc[buy_condition, '交易信号'] = 1
        self.stock_df.loc[sell_condition, '交易信号'] = 0
        
        # 如果当天没有新的买入信号，就沿用上一次买入时的价格，直到下一次买入。
        self.stock_df['买入价格'] = np.nan
        buy_dates = self.stock_df[self.stock_df['交易信号'] == 1].index
        self.stock_df.loc[buy_dates, '买入价格'] = self.stock_df.loc[buy_dates, '股票收盘价']
        self.stock_df['买入价格'] = self.stock_df['买入价格'].fillna(method='ffill')
        
        # 计算浮亏比例并触发止损
        self.stock_df['浮亏比例'] = (self.stock_df['股票收盘价'] - self.stock_df['买入价格']) / self.stock_df['买入价格']
        stop_loss_condition = self.stock_df['浮亏比例'] <= self.stop_loss_threshold
        self.stock_df.loc[stop_loss_condition, '交易信号'] = 0   # 触发止损，交易信号设为0（卖出）
        
        # 确定最终持仓状态
        self.stock_df['最终持仓状态'] = self.stock_df['交易信号'].fillna(method='ffill').fillna(0)

    def calculate_performance(self)->None:
        # 计算日收益率
        self.stock_df['股票日收益率'] = (self.stock_df['股票收盘价'] / self.stock_df['股票收盘价'].shift(1)) - 1
        self.stock_df['策略日收益'] = self.stock_df['股票日收益率'] * self.stock_df['最终持仓状态']
        
        # 年化策略收益
        total_strategy_return = (1 + self.stock_df['策略日收益']).prod()     #累成收益率
        self.annual_strategy_return = total_strategy_return ** (252 / self.day_count) - 1
        
        # 年化波动率
        daily_volatility = self.stock_df['策略日收益'].std()   #。std（）计算标准差
        self.annual_volatility = daily_volatility * np.sqrt(252)
        
        # 夏普比率
        if self.annual_volatility != 0:
            self.sharpe_ratio = (self.annual_strategy_return - self.risk_free_rate) / self.annual_volatility
        else:
            self.sharpe_ratio = 0
        
        # 基准收益（买入持有）和策略最终收益
        self.total_benchmark_return = (1 + self.stock_df['股票日收益率']).prod() - 1
        self.total_strategy_return = (1 + self.stock_df['策略日收益']).prod() - 1


    #打印结果
    def print_results(self):
        print("="*50)
        print("          量化回测结果（均线策略+止损+夏普比率）")
        print("="*50)
        print(f"买入持有策略最终收益：{self.total_benchmark_return:.2%}")
        print(f"带止损的均线策略最终收益：{self.total_strategy_return:.2%}")
        print(f"策略年化收益：{self.annual_strategy_return:.2%}")
        print(f"策略年化波动率：{self.annual_volatility:.2%}")
        print(f"策略夏普比率：{self.sharpe_ratio:.2f}")
        print(f"\n程序运行总耗时：{self.run_time:.2f} 秒")


        #结果绘图
    def plot_results(self):
    
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 绘图
        plt.figure(figsize=(10, 6))
        plt.plot(self.stock_df['股票收盘价'], label='股票收盘价', color='blue')
        plt.plot(self.stock_df['5日均线价格'], label='5日均线', color='red')
        plt.plot(self.stock_df['20日均线价格'], label='20日均线', color='green')
        
        # 标记买入/卖出点
        plt.scatter(self.stock_df[self.stock_df['交易信号']==1].index, 
                    self.stock_df[self.stock_df['交易信号']==1]['股票收盘价'], 
                    marker='^', color='green', s=80, label='买入')
        plt.scatter(self.stock_df[self.stock_df['交易信号']==0].index, 
                    self.stock_df[self.stock_df['交易信号']==0]['股票收盘价'], 
                    marker='v', color='red', s=80, label='卖出')
        
        # 图表设置
        plt.title('股票价格与交易信号（带止损）', fontsize=12)
        plt.xlabel('交易日期')
        plt.ylabel('价格（元）')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()

    def run(self)->None:              #一次完整运行 更加便利 切可以防止调用类中函数顺序错误
        start_time = time.time()
        
        # 按顺序执行步骤
        self.generate_stock_data()
        self.calculate_ma()
        self.generate_trade_signal()
        self.calculate_performance()
        
        # 计算运行时间
        end_time = time.time()
        self.run_time = end_time - start_time
        
        self.print_results()
        self.plot_results()


    
def main(): 
    test = MAStopLossBacktest() 
    test.run()
    
if __name__ == "__main__":
    main()
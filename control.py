
import pandas as pd  
import numpy as np   
import matplotlib.pyplot as plt  
import time  

# 记录开始时间
start_time = time.time()

# 保证中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


# 生成1年交易日  获取交易日数量
date_list = pd.date_range(start='2025-01-01', end='2025-12-31', freq='B')
day_count = len(date_list)

''' #原生成股价部分
np.random.seed(101)  # 固定随机种子，结果可复现
price_list = [100.0]  # 初始股价100元（基础列表）
for i in range(1, day_count):
    # 每日涨跌幅度：-2% 到 +2% 随机（基础随机数函数）
    daily_change = np.random.uniform(-0.02, 0.02)
    # 今日股价 = 昨日股价 * (1 + 涨跌幅度)（基础算术）
    next_price = price_list[-1] * (1 + daily_change)
    price_list.append(next_price)
'''
# 优化：不使用for循环 今日价=昨日价*(1+涨跌幅)
np.random.seed(101)
daily_change = np.random.uniform(-0.02, 0.02, day_count)  # 一次性生成所有涨跌幅
price_np = np.ones(day_count) * 100.0  # 初始股价100，生成等长数组
price_np[1:] = 100.0 * np.cumprod(1 + daily_change[1:])
price_list = price_np.tolist()                 # 转回列表，兼容后续代码
''
stock_df = pd.DataFrame({
    '交易日期': date_list,
    '股票收盘价': price_list
})

# 设置日期为索引（基础语句）
stock_df = stock_df.set_index('交易日期')

'''
# 步骤1：计算5日均线
stock_df['5日均线价格'] = stock_df['股票收盘价'].rolling(window=5).mean()
# 步骤2：计算20日均线
stock_df['20日均线价格'] = stock_df['股票收盘价'].rolling(window=20).mean()
'''
# 优化：复用滚动对象  避免多次遍历数据
roll5 = stock_df['股票收盘价'].rolling(window=5)        # 一次性创建5日滚动对象
roll20 = stock_df['股票收盘价'].rolling(window=20)     # 一次性创建20日滚动对象
stock_df['5日均线价格'] = roll5.mean()
stock_df['20日均线价格'] = roll20.mean()
''
# 计算均线差值
stock_df['均线差值'] = stock_df['5日均线价格'] - stock_df['20日均线价格']

#交易信号 初值为0
stock_df['交易信号'] = np.nan

# 金叉买入：前一日均线差<0，当日≥0
buy_condition = (stock_df['均线差值'].shift(1) < 0) & (stock_df['均线差值'] >= 0)
stock_df.loc[buy_condition, '交易信号'] = 1  # 1买入

# 死叉卖出：前一日均线差>0，当日≤0
sell_condition = (stock_df['均线差值'].shift(1) > 0) & (stock_df['均线差值'] <= 0)
stock_df.loc[sell_condition, '交易信号'] = 0  # 0卖出


# 创建买入价列，初始为空
stock_df['买入价格'] = np.nan

# 买入信号出现时，记录当日收盘价为买入价
buy_dates = stock_df[stock_df['交易信号'] == 1].index
stock_df.loc[buy_dates, '买入价格'] = stock_df.loc[buy_dates, '股票收盘价']

# 如果今天没有新的买入信号，就沿用上一次买入时的价格，直到下一次买入
stock_df['买入价格'] = stock_df['买入价格'].fillna(method='ffill')

# 浮亏比例 = (当前收盘价 - 买入价) / 买入价
stock_df['浮亏比例'] = (stock_df['股票收盘价'] - stock_df['买入价格']) / stock_df['买入价格']


# 止损阈值：5%（下跌5%就止损）  止损条件：浮亏比例 ≤ -0.05
# 强制卖出：触发止损时，交易信号变为0
stop_loss_threshold = -0.05
stop_loss_condition = stock_df['浮亏比例'] <= stop_loss_threshold
stock_df.loc[stop_loss_condition, '交易信号'] = 0


#确定最终持仓状态（基础填充）
stock_df['最终持仓状态'] = stock_df['交易信号'].fillna(method='ffill').fillna(0)


# 关于夏普比率的数学内容
# 夏普比率 = (年化策略收益 - 无风险收益率) / 年化策略波动率
# 1. 日收益率 = (当日收盘价 / 昨日收盘价) - 1
# 2. 策略日收益 = 日收益率 × 持仓状态（只有持仓时才有收益）
# 3. 年化策略收益 = (1+策略日收益)累乘 ^ (252/总交易日数) - 1
# 4. 年化波动率 = 策略日收益的标准差 × √252（252是年交易日数）
# 5. 无风险收益率：取年化3%

# 日收益率 = (当日价 / 昨日价)-1
stock_df['股票日收益率'] = (stock_df['股票收盘价'] / stock_df['股票收盘价'].shift(1)) - 1

# 策略日收益=日收益 × 持仓状态 （0  or  1)
stock_df['策略日收益'] = stock_df['股票日收益率'] * stock_df['最终持仓状态']


# 计算年化策略收益
# 1.策略总收益 = (1+策略日收益)的累乘
# 2.转为年化收益= (1 + 日收益) 累乘 ^(252/N)-1
total_strategy_return = (1 + stock_df['策略日收益']).prod()
annual_strategy_return = total_strategy_return ** (252 / day_count) - 1

# 计算年化波动率
# 1.计算策略日收益的标准差）
# 2.年化波动率 = 日波动率 × √252（平方根运算）
daily_volatility = stock_df['策略日收益'].std()
annual_volatility = daily_volatility * np.sqrt(252)

# 计算夏普比率（核心数学公式）
risk_free_rate = 0.03   # 无风险收益率（年化3%）
# 避免除以0（基础条件判断）
if annual_volatility != 0:
    sharpe_ratio = (annual_strategy_return - risk_free_rate) / annual_volatility
else:
    sharpe_ratio = 0


# 计算基准收益（买入持有）
total_benchmark_return = (1 + stock_df['股票日收益率']).prod() - 1
# 计算策略最终收益
total_strategy_return_final = (1 + stock_df['策略日收益']).prod() - 1

# 基础输出（易读格式）
print("="*50)
print("          量化回测结果（均线策略+止损+夏普比率）")
print("="*50)
print(f"买入持有策略最终收益：{total_benchmark_return:.2%}")
print(f"带止损的均线策略最终收益：{total_strategy_return_final:.2%}")
print(f"策略年化收益：{annual_strategy_return:.2%}")
print(f"策略年化波动率：{annual_volatility:.2%}")
print(f"策略夏普比率：{sharpe_ratio:.2f}")  


# 创建指定大小画布
plt.figure(figsize=(10, 6))
# 画股价和均线（plot语句）
plt.plot(stock_df['股票收盘价'], label='股票收盘价', color='blue')
plt.plot(stock_df['5日均线价格'], label='5日均线', color='red')
plt.plot(stock_df['20日均线价格'], label='20日均线', color='green')
# 标记买入/卖出点（scatter语句）
plt.scatter(stock_df[stock_df['交易信号']==1].index, 
            stock_df[stock_df['交易信号']==1]['股票收盘价'], 
            marker='^', color='green', s=80, label='买入')
plt.scatter(stock_df[stock_df['交易信号']==0].index, 
            stock_df[stock_df['交易信号']==0]['股票收盘价'], 
            marker='v', color='red', s=80, label='卖出')
# 基础设置
plt.title('股票价格与交易信号（带止损）', fontsize=12)
plt.xlabel('交易日期')
plt.ylabel('价格（元）')
plt.legend()
plt.grid(True, alpha=0.3)


plt.draw()    #绘图加载 停止计时后再显示 不然交互时间也会算成程序运行时间

#输出程序运行时间
end_time = time.time()
total_run_time = end_time - start_time
print(f"\n程序运行总耗时：{total_run_time:.2f} 秒")

plt.show()           
#if __name__ == "__main__":
 #   main()
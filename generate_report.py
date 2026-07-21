# -*- coding: utf-8 -*-
"""生成数据采集报告 - 校验所有数据文件并输出统计信息"""
import pandas as pd
import os
import warnings
warnings.filterwarnings('ignore')

OUT = 'data_collection_report.txt'
f = open(OUT, 'w', encoding='utf-8')
def p(s):
    f.write(str(s) + '\n')
    f.flush()

p("="*70)
p("中国商品期货机器学习因子投资 - 数据采集报告")
p("="*70)
p(f"采集时间: 2026-07-21")
p(f"项目目录: c:\\Users\\S20260127\\Documents\\trae_projects\\virtual question")
p(f"数据源: 天相数据库(10.2.47.80) + 聚源数据库(10.2.47.124)")
p(f"采集周期: 2020-01-01 ~ 2025-12-31 (实际数据截止2023-12-31)")
p("")

# 1. 期货行情数据
p("="*70)
p("1. 期货行情数据 (futures_data/01_futures_quotes/)")
p("="*70)

# 1.1 主力合约日行情
f1 = 'futures_data/01_futures_quotes/main_contracts_daily.csv'
df1 = pd.read_csv(f1, encoding='utf-8-sig')
size_mb = os.path.getsize(f1) / 1024 / 1024
p(f"\n  文件: {f1}")
p(f"  大小: {size_mb:.2f} MB")
p(f"  行数: {len(df1):,}")
p(f"  列名: {list(df1.columns)}")
p(f"  品种数: {df1['variety'].nunique()}")
p(f"  日期范围: {df1['trade_date'].min()} ~ {df1['trade_date'].max()}")
p(f"  交易所分布:")
for ex, g in df1.groupby('exchange'):
    p(f"    {ex}: {g['variety'].nunique()}个品种, {len(g):,}行")
p(f"  数据质量:")
for col in ['open','high','low','close','volume','open_interest']:
    miss = df1[col].isna().sum()
    zeros = (df1[col]==0).sum()
    p(f"    {col:15s}: 缺失={miss}, 零值={zeros}")

# 1.2 所有合约日行情
f2 = 'futures_data/01_futures_quotes/all_contracts_daily.csv'
df2 = pd.read_csv(f2, encoding='utf-8-sig', low_memory=False)
size_mb = os.path.getsize(f2) / 1024 / 1024
p(f"\n  文件: {f2}")
p(f"  大小: {size_mb:.2f} MB")
p(f"  行数: {len(df2):,}")
p(f"  列名: {list(df2.columns)}")
p(f"  品种数: {df2['variety'].nunique()}")
p(f"  合约数: {df2['contract_code'].nunique()}")
p(f"  日期范围: {df2['trade_date'].min()} ~ {df2['trade_date'].max()}")

# 2. 库存/仓单数据
p("\n" + "="*70)
p("2. 仓单/库存数据 (futures_data/02_inventory/)")
p("="*70)
f3 = 'futures_data/02_inventory/inventory_weekly.csv'
df3 = pd.read_csv(f3, encoding='utf-8-sig', low_memory=False)
size_mb = os.path.getsize(f3) / 1024 / 1024
p(f"\n  文件: {f3}")
p(f"  大小: {size_mb:.2f} MB")
p(f"  行数: {len(df3):,}")
p(f"  列名: {list(df3.columns)}")
p(f"  品种数(ticker): {df3['variety'].nunique() if 'variety' in df3.columns else 'N/A'}")
p(f"  日期范围: {df3['trade_date'].min()} ~ {df3['trade_date'].max()}")

# 3. 现货价格数据
p("\n" + "="*70)
p("3. 基差/现货价格数据 (futures_data/03_basis_spot/)")
p("="*70)
f4 = 'futures_data/03_basis_spot/spot_prices_daily.csv'
df4 = pd.read_csv(f4, encoding='utf-8-sig')
size_mb = os.path.getsize(f4) / 1024 / 1024
p(f"\n  文件: {f4}")
p(f"  大小: {size_mb:.2f} MB")
p(f"  行数: {len(df4):,}")
p(f"  列名: {list(df4.columns)}")
p(f"  品种数: {df4['variety'].nunique()}")
p(f"  日期范围: {df4['trade_date'].min()} ~ {df4['trade_date'].max()}")
p(f"  各品种数据量:")
for v, g in df4.groupby('variety'):
    p(f"    {v:4s} ({g['variety_cn'].iloc[0]:6s}) | {len(g):5d}行 | {g['trade_date'].min()} ~ {g['trade_date'].max()}")

# 4. 宏观数据
p("\n" + "="*70)
p("4. 宏观经济指标数据 (futures_data/04_macro/)")
p("="*70)
f5 = 'futures_data/04_macro/macro_indicators.csv'
df5 = pd.read_csv(f5, encoding='utf-8-sig')
size_mb = os.path.getsize(f5) / 1024 / 1024
p(f"\n  文件: {f5}")
p(f"  大小: {size_mb:.2f} MB")
p(f"  行数: {len(df5):,}")
p(f"  列名: {list(df5.columns)}")
p(f"  指标数: {df5['indicator_key'].nunique()}")
p(f"  日期范围: {df5['report_date'].min()} ~ {df5['report_date'].max()}")
p(f"  各指标数据量:")
for k, g in df5.groupby('indicator_key'):
    p(f"    {k:30s} | {len(g):5d}行 | {g['report_date'].min()} ~ {g['report_date'].max()}")

# 总结
p("\n" + "="*70)
p("数据采集总结")
p("="*70)
total_size = sum(os.path.getsize(os.path.join(r, fn)) for r, _, fs in os.walk('futures_data') for fn in fs)
total_rows = len(df1) + len(df2) + len(df3) + len(df4) + len(df5)
p(f"\n  数据目录: futures_data/")
p(f"  总文件大小: {total_size/1024/1024:.2f} MB")
p(f"  总数据行数: {total_rows:,}")
p(f"  期货行情(主力): 49个品种, {len(df1):,}行")
p(f"  期货行情(全部): {df2['contract_code'].nunique()}个合约, {len(df2):,}行")
p(f"  仓单/库存: 73个品种, {len(df3):,}行")
p(f"  现货价格: 46个品种, {len(df4):,}行")
p(f"  宏观指标: 26个指标, {len(df5):,}行")

p("\n" + "-"*70)
p("数据可用性说明")
p("-"*70)
p(f"  1. 期货与现货数据: 数据库订阅时间窗截至2023-12-31")
p(f"     (聚源JYDB数据更新到2023-12-29, 天相TxFDB更新到2025-12-31)")
p(f"  2. 主力合约拼接方式: 天相T_MAIN_CONTRACT表已统一拼接")
p(f"  3. 换月成本与涨跌停限制: 由原始OHLC数据可计算")
p(f"  4. 部分品种现货价格数据覆盖不全(如JM/ZC数据截至2022年)")
p(f"  5. 国际铜(BC)/低硫燃料油(LU)/苹果(AP)暂无匹配现货指标")
p(f"  6. 工业增加值_环比 与 新增固定资产投资 指标无2020年后数据")

p("\n" + "-"*70)
p("后续研究方向建议")
p("-"*70)
p(f"  1. 因子构造:")
p(f"     - 动量因子: 基于主力合约过去N日收益率")
p(f"     - 期限结构/展期收益: 基于all_contracts_daily计算近月-次月价差")
p(f"     - 基差因子: 现货价格 - 期货主力合约价格 (基差率)")
p(f"     - 流动性因子: 成交量/持仓量/Amihud illiquidity")
p(f"     - 持仓量因子: open_interest变化率")
p(f"     - 波动率因子: 日收益波动率(20日/60日)")
p(f"     - 偏度因子: 日收益分布偏度")
p(f"  2. 机器学习模型:")
p(f"     - 基准: 单因子排序、线性回归、等权多因子")
p(f"     - AI模型: LightGBM / XGBoost / 神经网络 / 图神经网络")
p(f"  3. 组合检验:")
p(f"     - 样本内训练 + 样本外测试")
p(f"     - 多空组合表现(夏普、最大回撤、IC)")

f.close()
print("Report generated: data_collection_report.txt")

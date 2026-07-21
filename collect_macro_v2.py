# -*- coding: utf-8 -*-
"""
采集关键宏观经济指标数据(V2 - 修正指标代码)
"""
import pyodbc
import pandas as pd
import os
import warnings
warnings.filterwarnings('ignore')

OUT = 'collect_macro_v2_log.txt'
f = open(OUT, 'w', encoding='utf-8')
def p(s):
    f.write(str(s) + '\n')
    f.flush()

CONN_JY = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=10.2.47.124;"
    "DATABASE=JYDB;"
    "UID=jydb_reader;PWD=Syzx805805#;"
)

OUT_DIR = 'futures_data/04_macro'
os.makedirs(OUT_DIR, exist_ok=True)

# 手工精选的关键宏观指标(已校验)
MACRO_INDICATORS = {
    # === 宏观经济(GDP/CPI/PPI/PMI) ===
    'GDP_现价_累计_季': {'code': 110000001, 'name': 'GDP(现价):累计值:季', 'freq': '季'},
    'CPI_同比_月': {'code': 110002855, 'name': 'CPI(上年同月=100):当期值:月', 'freq': '月'},
    'PPI_同比_月': {'code': 110002644, 'name': 'PPI(上年同月=100):当期值:月', 'freq': '月'},
    'PPIRM_同比_月': {'code': 110002632, 'name': '工业生产者购进价格指数PPIRM(上年同月=100):当期值:月', 'freq': '月'},
    'PMI_制造业_季调_月': {'code': 110166523, 'name': '制造业PMI:季调:月', 'freq': '月'},
    'PMI_新订单_月': {'code': 110166521, 'name': '制造业PMI:新订单:季调:月', 'freq': '月'},
    'PMI_生产_月': {'code': 110166522, 'name': '制造业PMI:生产:季调:月', 'freq': '月'},
    'PMI_产成品库存_月': {'code': 110166518, 'name': '制造业PMI:产成品库存:季调:月', 'freq': '月'},
    'PMI_原材料库存_月': {'code': 110166514, 'name': '制造业PMI:原材料库存:季调:月', 'freq': '月'},

    # === 货币供应 ===
    'M2_余额_月': {'code': 110111410, 'name': '货币和准货币(M2):月', 'freq': '月'},
    'M2_同比_月': {'code': 110111411, 'name': '货币和准货币(M2):同比:月', 'freq': '月'},
    'M1_M2_剪刀差_月': {'code': 110111412, 'name': 'M1-M2剪刀差:当期值:月', 'freq': '月'},

    # === 汇率 ===
    'USD_CNY_中间价_日': {'code': 110096210, 'name': '中间价-即期(前一日):美元兑人民币:日', 'freq': '日'},
    'USD_CNY_期末_月': {'code': 110111395, 'name': '美元期末汇率:月', 'freq': '月'},
    'EUR_CNY_期末_月': {'code': 110112339, 'name': '欧元期末汇率:月', 'freq': '月'},
    'JPY_CNY_期末_月': {'code': 110112340, 'name': '日元期末汇率:月', 'freq': '月'},

    # === 利率 ===
    '银行间同业拆借利率_月': {'code': 110111393, 'name': '银行间同业拆借加权平均利率:当期值:月', 'freq': '月'},
    '银行间隔夜拆借利率_月': {'code': 110112359, 'name': '银行间隔夜同业拆借加权平均利率:当期值:月', 'freq': '月'},
    '银行间7天拆借利率_月': {'code': 110112358, 'name': '银行间7天内同业拆借加权平均利率:当期值:月', 'freq': '月'},

    # === 进出口 ===
    '出口额_美元_月': {'code': 110127295, 'name': '出口额(以美元计):当期值:月', 'freq': '月'},
    '进口额_美元_月': {'code': 110005221, 'name': '进口额(以美元计):当期值:月', 'freq': '月'},
    '进出口差额_美元_月': {'code': 110007401, 'name': '进出口差额(以美元计):当期值:月', 'freq': '月'},

    # === 投资/消费/工业 ===
    '社会消费品零售_当期值_月': {'code': 110003911, 'name': '社会消费品零售总额:当期值:月', 'freq': '月'},
    '社会消费品零售_当期同比_月': {'code': 110003918, 'name': '社会消费品零售总额:当期同比:月', 'freq': '月'},
    '工业增加值_当期同比_月': {'code': 110000261, 'name': '规模以上工业增加值:当期同比:月', 'freq': '月'},
    '工业增加值_累计同比_月': {'code': 110000262, 'name': '规模以上工业增加值:累计同比:月', 'freq': '月'},
    '工业增加值_环比_月': {'code': 110002866, 'name': '规模以上工业增加值:环比:月', 'freq': '月'},
    '新增固定资产投资_累计同比_月': {'code': 110110437, 'name': '新增固定资产投资完成额:累计同比:月', 'freq': '月'},
}

try:
    conn = pyodbc.connect(CONN_JY, timeout=120)
    p("已连接聚源JYDB")

    p(f"\n准备采集{len(MACRO_INDICATORS)}个宏观指标")

    # Step 1: 校验指标名称
    p("\nStep 1: 校验指标名称")
    valid_indicators = {}
    invalid_indicators = []
    for key, info in MACRO_INDICATORS.items():
        code = info['code']
        try:
            df_chk = pd.read_sql(f"""
                SELECT TOP 1 IndicatorCode, IndicatorName
                FROM C_ED_IndicatorMain
                WHERE IndicatorCode = {code}
            """, conn)
            if len(df_chk) > 0:
                actual_name = df_chk['IndicatorName'].iloc[0]
                # 检查名称是否与预期匹配
                expected = info['name']
                match = (actual_name == expected)
                valid_indicators[key] = {
                    'code': code,
                    'name': actual_name,
                    'expected_name': expected,
                    'freq': info['freq'],
                    'match': match,
                }
                status = 'OK' if match else 'WARN(名称不符)'
                p(f"  [{status:14s}] {key:30s} | {code:12d} | {actual_name}")
            else:
                invalid_indicators.append((key, code, 'IndicatorMain中不存在'))
                p(f"  [失败] {key:30s} | {code} | IndicatorMain中不存在")
        except Exception as e:
            invalid_indicators.append((key, code, str(e)))
            p(f"  [失败] {key:30s} | {code} | {e}")

    p(f"\n有效指标: {len(valid_indicators)}, 无效指标: {len(invalid_indicators)}")

    # Step 2: 采集每个指标数据
    p(f"\nStep 2: 采集2020-2025时序数据")
    all_data = []
    success_cnt = 0
    fail_list = []
    for key, info in valid_indicators.items():
        code = info['code']
        name = info['name']
        freq = info['freq']
        try:
            df_t = pd.read_sql(f"""
                SELECT IndicatorCode, EndDate, DataValue
                FROM C_ED_MacroIndicatorData
                WHERE IndicatorCode = {code}
                AND EndDate >= '2020-01-01' AND EndDate <= '2025-12-31'
                ORDER BY EndDate
            """, conn)
            if len(df_t) > 0:
                df_t['indicator_key'] = key
                df_t['indicator_name'] = name
                df_t['freq'] = freq
                df_t['DataValue'] = pd.to_numeric(df_t['DataValue'], errors='coerce')
                all_data.append(df_t)
                success_cnt += 1
                p(f"  [{success_cnt}/{len(valid_indicators)}] {key:30s} | {len(df_t):5d}行 | {df_t['EndDate'].min().date()} ~ {df_t['EndDate'].max().date()} | {name}")
            else:
                fail_list.append((key, code, '无数据'))
                p(f"  [失败] {key:30s} | IndicatorCode={code} | 无数据")
        except Exception as e:
            fail_list.append((key, code, str(e)))
            p(f"  [失败] {key:30s} | IndicatorCode={code} | {e}")

    if all_data:
        df_all = pd.concat(all_data, ignore_index=True)
        # 修正: 同时重命名 IndicatorCode 和其他列
        df_all = df_all.rename(columns={
            'EndDate': 'report_date',
            'DataValue': 'value',
            'IndicatorCode': 'indicator_code',
        })
        # 调整列顺序
        df_all = df_all[['indicator_key','indicator_name','freq','report_date','value','indicator_code']]
        df_all = df_all.sort_values(['indicator_key','report_date']).reset_index(drop=True)

        out_file = f'{OUT_DIR}/macro_indicators.csv'
        df_all.to_csv(out_file, index=False, encoding='utf-8-sig')
        size_mb = os.path.getsize(out_file) / 1024 / 1024
        p(f"\n已保存: {out_file}")
        p(f"文件大小: {size_mb:.2f} MB")
        p(f"总行数: {len(df_all):,}")
        p(f"指标数: {df_all['indicator_key'].nunique()}")
        p(f"日期范围: {df_all['report_date'].min().date()} ~ {df_all['report_date'].max().date()}")

        # 数据质量检查
        p("\n数据质量检查:")
        for k, g in df_all.groupby('indicator_key'):
            miss = g['value'].isna().sum()
            p(f"  {k:30s} | {len(g):5d}行 | 缺失={miss:3d} | {g['report_date'].min().date()} ~ {g['report_date'].max().date()}")

    if fail_list:
        p(f"\n失败指标({len(fail_list)}个):")
        for key, code, msg in fail_list:
            p(f"  {key} | {code} | {msg}")

    conn.close()
    p("\n=== 完成 ===")
except Exception as e:
    p(f"ERROR: {e}")
    import traceback
    p(traceback.format_exc())

f.close()

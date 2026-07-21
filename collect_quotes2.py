# -*- coding: utf-8 -*-
"""
采集主力期货行情数据 - 天相T_MAIN_CONTRACT (简化版)
"""
import pyodbc
import pandas as pd
import os
import time
import sys
import traceback

def log(msg, f):
    print(msg, flush=True)
    f.write(str(msg) + '\n')
    f.flush()

log_file = open('collect_quotes_log2.txt', 'w', encoding='utf-8')
try:
    DRIVER = '{ODBC Driver 17 for SQL Server}'
    conn = pyodbc.connect(f"DRIVER={DRIVER};SERVER=10.2.47.80;UID=txdbkq;PWD=Syzxtx2304kq!$", timeout=30)
    log("数据库连接成功", log_file)

    OUTPUT_DIR = 'futures_data/01_futures_quotes'
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 主流活跃品种
    VARIETIES = [
        'CU','AL','ZN','PB','NI','SN','AU','AG','RB','HC','RU','FU','BU','SP','SS',  # SHFE
        'SC','LU','NR','BC',  # INE
        'A','M','Y','P','C','CS','I','J','JM','L','V','PP','EB','EG','PG',  # DCE
        'SR','CF','TA','OI','FG','MA','SF','SM','AP','UR','SA','ZC','RM','PK','PF',  # CZCE
    ]
    VARIETY_NAMES = {
        'CU':'铜','AL':'铝','ZN':'锌','PB':'铅','NI':'镍','SN':'锡',
        'AU':'黄金','AG':'白银','RB':'螺纹钢','HC':'热轧卷板','RU':'天然橡胶',
        'FU':'燃料油','BU':'石油沥青','SP':'纸浆','SS':'不锈钢',
        'SC':'原油','LU':'低硫燃料油','NR':'20号胶','BC':'国际铜',
        'A':'豆一','M':'豆粕','Y':'豆油','P':'棕榈油','C':'玉米','CS':'玉米淀粉',
        'I':'铁矿石','J':'焦炭','JM':'焦煤','L':'聚乙烯','V':'聚氯乙烯',
        'PP':'聚丙烯','EB':'苯乙烯','EG':'乙二醇','PG':'液化石油气',
        'SR':'白糖','CF':'棉花','TA':'PTA','OI':'菜籽油','FG':'玻璃',
        'MA':'甲醇','SF':'硅铁','SM':'锰硅','AP':'苹果','UR':'尿素',
        'SA':'纯碱','ZC':'动力煤','RM':'菜粕','PK':'花生','PF':'短纤',
    }

    variety_in = ",".join([f"'{v}'" for v in VARIETIES])
    log(f"目标品种: {len(VARIETIES)}个", log_file)

    # 先验证品种可用性
    df_check = pd.read_sql(f"""
        SELECT DISTINCT f_varity_code
        FROM txnfdb.dbo.T_MAIN_CONTRACT
        WHERE F_TRADE_DATE >= 20200101
        AND f_varity_code IN ({variety_in})
    """, conn)
    available = set(df_check['f_varity_code'].tolist())
    log(f"数据库中可用品种: {len(available)}个", log_file)
    log(f"可用: {sorted(available)}", log_file)
    missing = set(VARIETIES) - available
    if missing:
        log(f"缺失: {sorted(missing)}", log_file)

    # 采集数据
    log("\n开始采集主力合约数据...", log_file)
    query = f"""
        SELECT 
            f_varity_code as variety,
            f_exch_name as exchange,
            F_TRADE_DATE as trade_date,
            f_futures_code as contract_code,
            f_preClose as pre_close,
            f_open as [open],
            f_high as [high],
            f_low as [low],
            f_close as [close],
            f_volume as volume,
            f_amount as amount,
            f_openinterest as open_interest
        FROM txnfdb.dbo.T_MAIN_CONTRACT
        WHERE F_TRADE_DATE >= 20200101
        AND F_TRADE_DATE <= 20251231
        AND f_varity_code IN ({variety_in})
        ORDER BY f_varity_code, F_TRADE_DATE
    """
    
    t0 = time.time()
    df = pd.read_sql(query, conn)
    t1 = time.time()
    log(f"采集完成! 耗时: {t1-t0:.1f}秒, 行数: {len(df)}", log_file)
    
    # 添加中文名称
    df['variety_name'] = df['variety'].map(VARIETY_NAMES)
    
    # 统计
    log(f"品种数: {df['variety'].nunique()}", log_file)
    log(f"日期范围: {df['trade_date'].min()} ~ {df['trade_date'].max()}", log_file)
    log(f"\n各品种数据量:", log_file)
    for v, g in df.groupby('variety'):
        name = VARIETY_NAMES.get(v, v)
        log(f"  {v:4s}({name:6s}) | {len(g):5d}行 | {g['trade_date'].min()} ~ {g['trade_date'].max()} | 交易所={g['exchange'].iloc[0]}", log_file)

    log(f"\n交易所分布:", log_file)
    for exch, g in df.groupby('exchange'):
        log(f"  {exch}: {len(g)}行, {g['variety'].nunique()}个品种", log_file)

    # 保存
    output_path = os.path.join(OUTPUT_DIR, 'main_contracts_daily.csv')
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    log(f"\n已保存: {output_path}", log_file)
    log(f"文件大小: {os.path.getsize(output_path)/1024/1024:.2f} MB", log_file)

    # 质量检查
    log(f"\n数据质量检查:", log_file)
    for col in ['open','high','low','close','volume','open_interest']:
        n_null = df[col].isna().sum()
        n_zero = (df[col] == 0).sum()
        log(f"  {col:15s}: 缺失={n_null}, 零值={n_zero}", log_file)

    conn.close()
    log("\n=== 完成 ===", log_file)

except Exception as e:
    log(f"\n错误: {e}", log_file)
    log(traceback.format_exc(), log_file)
finally:
    log_file.close()

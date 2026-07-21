# -*- coding: utf-8 -*-
"""
采集库存/仓单数据 - 天相T_INVENTORY_WEEK_SH
"""
import pyodbc
import pandas as pd
import os
import time
import traceback

def log(msg, f):
    print(msg, flush=True)
    f.write(str(msg) + '\n')
    f.flush()

log_file = open('collect_inventory_log.txt', 'w', encoding='utf-8')
try:
    DRIVER = '{ODBC Driver 17 for SQL Server}'
    conn = pyodbc.connect(f"DRIVER={DRIVER};SERVER=10.2.47.80;UID=txdbkq;PWD=Syzxtx2304kq!$", timeout=30)
    log("数据库连接成功", log_file)

    OUTPUT_DIR = 'futures_data/02_inventory'
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step 1: 查看库存表品种和数据范围
    log("\nStep 1: 查看库存表概况", log_file)
    df_overview = pd.read_sql("""
        SELECT F_TICKER_CODE, F_PRODUCT, 
               COUNT(*) as cnt,
               MIN(F_TRADE_DATE) as min_date, 
               MAX(F_TRADE_DATE) as max_date
        FROM txnfdb.dbo.T_INVENTORY_WEEK_SH
        WHERE F_TRADE_DATE >= 20200101
        GROUP BY F_TICKER_CODE, F_PRODUCT
        ORDER BY cnt DESC
    """, conn)
    log(f"品种数: {len(df_overview)}", log_file)
    for _, r in df_overview.iterrows():
        log(f"  {r['F_TICKER_CODE']:6s} | {r['F_PRODUCT']:10s} | {r['cnt']:5d}行 | {r['min_date']} ~ {r['max_date']}", log_file)

    # Step 2: 采集库存数据
    log(f"\nStep 2: 采集库存数据 (2020-2025)", log_file)
    query = """
        SELECT 
            F_CCID,
            F_TICKER_CODE as variety,
            F_PRODUCT as product,
            F_TRADE_DATE as trade_date,
            F1 as region,
            F2 as warehouse,
            F3 as current_inventory,
            F4 as prev_inventory,
            F5 as inventory_change,
            F6 as another_inv1,
            F7 as another_inv2,
            F8 as change_amount,
            F9 as total_current,
            F10 as total_prev,
            F11 as total_change,
            F12 as unit
        FROM txnfdb.dbo.T_INVENTORY_WEEK_SH
        WHERE F_TRADE_DATE >= 20200101
        AND F_TRADE_DATE <= 20251231
        ORDER BY F_TICKER_CODE, F_TRADE_DATE, F2
    """
    
    t0 = time.time()
    df = pd.read_sql(query, conn)
    t1 = time.time()
    log(f"采集完成! 耗时: {t1-t0:.1f}秒, 行数: {len(df)}", log_file)
    
    log(f"品种数: {df['variety'].nunique()}", log_file)
    log(f"日期范围: {df['trade_date'].min()} ~ {df['trade_date'].max()}", log_file)
    log(f"仓库数: {df['warehouse'].nunique()}", log_file)
    
    # 按品种统计
    log(f"\n各品种库存数据量:", log_file)
    for v, g in df.groupby('variety'):
        product = g['product'].iloc[0]
        log(f"  {v:6s}({product:8s}) | {len(g):5d}行 | {g['trade_date'].min()} ~ {g['trade_date'].max()} | 仓库={g['warehouse'].nunique()}个", log_file)
    
    # 保存
    output_path = os.path.join(OUTPUT_DIR, 'inventory_weekly.csv')
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    log(f"\n已保存: {output_path}", log_file)
    log(f"文件大小: {os.path.getsize(output_path)/1024/1024:.2f} MB", log_file)
    
    # 质量检查
    log(f"\n数据质量检查:", log_file)
    for col in ['current_inventory', 'prev_inventory', 'total_current']:
        n_null = df[col].isna().sum()
        log(f"  {col:20s}: 缺失={n_null} ({n_null/len(df)*100:.1f}%)", log_file)
    
    conn.close()
    log("\n=== 完成 ===", log_file)

except Exception as e:
    log(f"\n错误: {e}", log_file)
    log(traceback.format_exc(), log_file)
finally:
    log_file.close()

# -*- coding: utf-8 -*-
"""
采集所有合约行情数据 - 天相T_FUTURES_TRADE (优化版)
使用子查询替代JOIN，分批查询
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

log_file = open('collect_all_contracts_log2.txt', 'w', encoding='utf-8')
try:
    DRIVER = '{ODBC Driver 17 for SQL Server}'
    conn = pyodbc.connect(f"DRIVER={DRIVER};SERVER=10.2.47.80;UID=txdbkq;PWD=Syzxtx2304kq!$", timeout=60)
    log("数据库连接成功", log_file)

    OUTPUT_DIR = 'futures_data/01_futures_quotes'
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 主流品种CCID列表 (从上一次运行获取)
    CCID_MAP = {
        8012234:('JM','大连'), 8210858:('PK','郑州'), 8011307:('SR','郑州'),
        8011277:('FG','郑州'), 8124900:('AP','郑州'), 8011264:('AL','上海'),
        8193739:('LU','上海'), 8171341:('UR','郑州'), 8011278:('FU','上海'),
        8011301:('RM','郑州'), 8026670:('CS','大连'), 8011293:('P','大连'),
        8202027:('PF','郑州'), 8011282:('J','大连'), 8011292:('OI','郑州'),
        8185714:('PG','大连'), 8029975:('NI','上海'), 8018656:('HC','上海'),
        8158020:('EG','大连'), 8011265:('AU','上海'), 8157199:('SP','上海'),
        8011260:('AG','上海'), 8011316:('ZN','上海'), 8011309:('V','大连'),
        8178405:('SA','郑州'), 8029985:('SN','上海'), 8015188:('BU','上海'),
        8011304:('RU','上海'), 8011308:('TA','郑州'), 8022774:('SF','郑州'),
        8171444:('NR','上海'), 8011272:('C','大连'), 8011275:('CU','上海'),
        8011259:('A','大连'), 8032647:('ZC','郑州'), 8175556:('EB','大连'),
        8174681:('SS','上海'), 8011315:('Y','大连'), 8020830:('MA','郑州'),
        8011290:('M','大连'), 8130217:('SC','上海'), 8011274:('CF','郑州'),
        8015485:('I','大连'), 8011294:('PB','上海'), 8205072:('BC','上海'),
        8011283:('L','大连'), 8018055:('PP','大连'), 8011299:('RB','上海'),
        8022775:('SM','郑州'),
    }
    ccid_list = list(CCID_MAP.keys())
    ccid_in = ",".join([str(c) for c in ccid_list])
    log(f"品种数: {len(ccid_list)}", log_file)

    # 方法: 先获取合约ID列表,再查行情
    log("\nStep 1: 获取合约ID列表", log_file)
    df_ids = pd.read_sql(f"""
        SELECT F_FUTURES_ID, F_FUTURES_CODE, F_CCID, F_Exch_Name
        FROM txnfdb.dbo.T_FUTURES
        WHERE F_CCID IN ({ccid_in})
        AND F_FUTURES_CODE IS NOT NULL
    """, conn)
    log(f"合约数: {len(df_ids)}", log_file)
    
    # 按品种统计合约数
    df_ids['variety'] = df_ids['F_CCID'].map(lambda x: CCID_MAP.get(int(x),('?','?'))[0])
    for v, g in df_ids.groupby('variety'):
        log(f"  {v:4s}: {len(g):3d}个合约", log_file)
    
    # 获取所有合约ID
    futures_ids = df_ids['F_FUTURES_ID'].dropna().astype(int).tolist()
    log(f"\n总合约ID数: {len(futures_ids)}", log_file)

    # Step 2: 分批查询行情数据
    log(f"\nStep 2: 分批查询行情数据 (2020-2025)", log_file)
    
    all_dfs = []
    batch_size = 200  # 每批200个合约
    total_batches = (len(futures_ids) + batch_size - 1) // batch_size
    
    t0 = time.time()
    for i in range(0, len(futures_ids), batch_size):
        batch = futures_ids[i:i+batch_size]
        batch_in = ",".join([str(x) for x in batch])
        batch_num = i // batch_size + 1
        
        query = f"""
            SELECT 
                F_FUTURES_ID,
                F_FUTURES_CODE,
                F_TRADE_DATE,
                F_PRECLOSE as pre_close,
                F_OPEN as [open],
                F_HIGH as [high],
                F_LOW as [low],
                F_CLOSE as [close],
                F_VOLUME as volume,
                F_AMOUNT as amount,
                F_SETTLED_PRICE as settle_price,
                F_OPEN_INTEREST as open_interest
            FROM txnfdb.dbo.T_FUTURES_TRADE
            WHERE F_TRADE_DATE >= 20200101
            AND F_TRADE_DATE <= 20251231
            AND F_FUTURES_ID IN ({batch_in})
        """
        
        try:
            df_batch = pd.read_sql(query, conn, )
            all_dfs.append(df_batch)
            if batch_num % 5 == 0 or batch_num == total_batches:
                elapsed = time.time() - t0
                log(f"  批次 {batch_num}/{total_batches} 完成, 累计 {sum(len(d) for d in all_dfs)}行, 耗时 {elapsed:.0f}秒", log_file)
        except Exception as e:
            log(f"  批次 {batch_num} 失败: {e}", log_file)
    
    t1 = time.time()
    df = pd.concat(all_dfs, ignore_index=True)
    log(f"\n采集完成! 总耗时: {t1-t0:.1f}秒, 总行数: {len(df)}", log_file)
    
    # 添加品种和交易所信息
    id_to_info = {}
    for _, r in df_ids.iterrows():
        fid = int(r['F_FUTURES_ID'])
        ccid = int(r['F_CCID'])
        variety, exch = CCID_MAP.get(ccid, ('?','?'))
        id_to_info[fid] = (variety, exch, r['F_FUTURES_CODE'])
    
    df['variety'] = df['F_FUTURES_ID'].map(lambda x: id_to_info.get(int(x), ('?','?','?'))[0] if pd.notna(x) else '?')
    df['exchange'] = df['F_FUTURES_ID'].map(lambda x: id_to_info.get(int(x), ('?','?','?'))[1] if pd.notna(x) else '?')
    
    # 重命名
    df = df.rename(columns={
        'F_FUTURES_ID': 'futures_id',
        'F_FUTURES_CODE': 'contract_code',
        'F_TRADE_DATE': 'trade_date',
    })
    
    # 统计
    log(f"\n品种数: {df['variety'].nunique()}", log_file)
    log(f"合约数: {df['contract_code'].nunique()}", log_file)
    log(f"日期范围: {df['trade_date'].min()} ~ {df['trade_date'].max()}", log_file)
    
    log(f"\n各品种数据量:", log_file)
    for v, g in df.groupby('variety'):
        log(f"  {v:5s} | {g['contract_code'].nunique():3d}个合约 | {len(g):6d}行 | {g['trade_date'].min()} ~ {g['trade_date'].max()}", log_file)
    
    # 保存
    output_path = os.path.join(OUTPUT_DIR, 'all_contracts_daily.csv')
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    log(f"\n已保存: {output_path}", log_file)
    log(f"文件大小: {os.path.getsize(output_path)/1024/1024:.2f} MB", log_file)
    
    # 质量检查
    log(f"\n数据质量检查:", log_file)
    for col in ['open','high','low','close','volume','open_interest']:
        n_null = df[col].isna().sum()
        log(f"  {col:15s}: 缺失={n_null} ({n_null/len(df)*100:.1f}%)", log_file)
    
    conn.close()
    log("\n=== 完成 ===", log_file)

except Exception as e:
    log(f"\n错误: {e}", log_file)
    log(traceback.format_exc(), log_file)
finally:
    log_file.close()

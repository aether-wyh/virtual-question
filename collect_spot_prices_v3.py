# -*- coding: utf-8 -*-
"""
采集主流品种现货价格数据(V3 - 手工精选指标)
基于V2结果,手工挑选每个品种的正确现货价格指标
"""
import pyodbc
import pandas as pd
import os
import warnings
warnings.filterwarnings('ignore')

OUT = 'collect_spot_prices_v3_log.txt'
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

OUT_DIR = 'futures_data/03_basis_spot'
os.makedirs(OUT_DIR, exist_ok=True)

VARIETY_CN = {
    'CU':'铜','AL':'铝','ZN':'锌','PB':'铅','NI':'镍','SN':'锡',
    'AU':'黄金','AG':'白银','RB':'螺纹钢','HC':'热轧卷板','RU':'天然橡胶',
    'FU':'燃料油','BU':'石油沥青','SP':'纸浆','SS':'不锈钢',
    'SC':'原油','LU':'低硫燃料油','NR':'20号胶','BC':'国际铜',
    'A':'豆一','M':'豆粕','Y':'豆油','P':'棕榈油','C':'玉米','CS':'玉米淀粉',
    'I':'铁矿石','J':'焦炭','JM':'焦煤',
    'L':'聚乙烯','V':'聚氯乙烯','PP':'聚丙烯','EB':'苯乙烯','EG':'乙二醇','PG':'液化石油气',
    'SR':'白糖','CF':'棉花','TA':'PTA','OI':'菜籽油','FG':'玻璃','MA':'甲醇',
    'SF':'硅铁','SM':'锰硅','AP':'苹果','UR':'尿素','SA':'纯碱','ZC':'动力煤',
    'RM':'菜粕','PK':'花生','PF':'短纤',
}

# 手工精选指标 - 通过IndicatorName人工核对
# 优先选择: 主流价/市场价 + 品种核心名称 + 全国/华东 + 日频
CURATED_INDICATORS = {
    # 有色金属 - 长江现货市场价是标准现货价
    'CU':  {'code': 1030240001, 'name': '长江有色金属现货市场价:铜:1#:日'},
    'AL':  {'code': 1030240002, 'name': '长江有色金属现货市场价:铝:A00:日'},
    'ZN':  {'code': 1030240004, 'name': '长江有色金属现货市场价:锌:1#:日'},
    'PB':  {'code': 1030240003, 'name': '长江有色金属现货市场价:铅:1#:日'},
    'NI':  {'code': 1030240006, 'name': '长江有色金属现货市场价:镍:1#:日'},
    'SN':  {'code': 1030240007, 'name': '长江有色金属现货市场价:锡:1#:日'},
    # 贵金属 - 黄金/白银现货价
    'AU':  {'code': 1330011454, 'name': '市场价格:黄金:Au≥99.99%:华东:日'},
    'AG':  {'code': 1330011455, 'name': '市场价格:白银:1#,IC-Ag99.99:华东:日'},
    # 黑色 - 螺纹钢/热卷/铁矿石/焦炭/焦煤
    'RB':  {'code': 1010050001, 'name': '市场价:螺纹钢:HRB400,20mm:全国:日'},
    'HC':  {'code': 1010100001, 'name': '市场价:热轧板卷:4.75mm:全国:日'},
    'I':   {'code': 1310200106, 'name': '市场价:铁矿石:PB粉,62%:澳大利亚:日'},
    'J':   {'code': 1320271324, 'name': '国内市场主流价:焦炭:河南地区:日'},
    'JM':  {'code': 1320260159, 'name': '市场价格:炼焦煤:G>50,V10-28:山西:日'},
    'SF':  {'code': 1010360002, 'name': '市场价:硅铁合金:75-A:全国:日'},
    'SM':  {'code': 1010360001, 'name': '市场价:硅锰合金:Mn65&Si17:全国:日'},
    'SS':  {'code': 1310300012, 'name': '市场价:不锈钢板卷:无锡:201/2B:1.0mm:日'},
    # 能源化工 - 沥青/燃料油/PTA/甲醇/乙二醇等
    'BU':  {'code': 1380037657, 'name': '国内市场价:主流价:沥青:重交沥青:华东:日'},
    'FU':  {'code': 1380033547, 'name': '国内市场价:主流价:燃料油:国产250#:华东:日'},
    'SC':  {'code': 1085340044, 'name': '现货价:西德克萨斯中级轻质原油(WTI):FOB库欣:日'},
    'TA':  {'code': 1380032185, 'name': '国内市场价:主流价:PTA:华东:日'},
    'MA':  {'code': 1380046603, 'name': '国内市场价:主流价:甲醇:国标:广西:日'},
    'EG':  {'code': 1380032883, 'name': '国内市场价:主流价:乙二醇:华东:日'},
    'L':   {'code': 1380041623, 'name': '国内市场价:主流价:LLDPE:7042,薄膜:余姚:大庆石化:日'},
    'V':   {'code': 1380041913, 'name': '国内市场价:主流价:PVC:SG-5:齐鲁化工城:日'},
    'PP':  {'code': 1380036142, 'name': '国内市场价:主流价:聚丙烯:拉丝:T30S:齐鲁石化:日'},
    'EB':  {'code': 1380045661, 'name': '国际市场价:到岸价:主流价:苯乙烯:东南亚:日'},
    'PG':  {'code': 1380036757, 'name': '国内市场价:主流价:液化气:温州:日'},
    'SA':  {'code': 1380047704, 'name': '国内市场价:主流价:纯碱:重质:华东:日'},
    'FG':  {'code': 1410013687, 'name': '市场主流价格:浮法玻璃:5.0mm:大板:华东:日'},
    'SP':  {'code': 1420021022, 'name': '国内市场主流价:纸浆:阔叶浆:江浙沪:金鱼:日'},
    'PF':  {'code': 1380032307, 'name': '国内市场价:主流价:涤纶短纤:1.4D*38mm:华东:日'},
    'UR':  {'code': 1380049206, 'name': '国内市场价:主流价:尿素:小颗粒:四川眉山:日'},
    # 橡胶
    'RU':  {'code': 1380050417, 'name': '国内市场价:主流价:全乳胶:SCRWF:上海:日'},
    'NR':  {'code': 1380050413, 'name': '国内市场价:主流价:干胶:TSR20,国产轮胎专用:昆明:日'},
    # 农产品
    'A':   {'code': 1340040041, 'name': '市场价:大豆:黄大豆,三级:黑龙江:日'},
    'M':   {'code': 1340040029, 'name': '市场价:豆粕:饲料用,带皮,粗蛋白质≥43%:日'},
    'Y':   {'code': 1340040042, 'name': '市场价:大豆油:压榨成品,一级:山东:日'},
    'P':   {'code': 1340040040, 'name': '市场价:棕榈油:食用精炼棕榈液油,熔点24℃:日'},
    'C':   {'code': 1340040043, 'name': '市场价:玉米:黄玉米,三级,水分14%:山东:日'},
    'CS':  {'code': 1340040045, 'name': '市场价:玉米淀粉:食品用,一级,水分≤14%:山东:日'},
    'SR':  {'code': 1040250001, 'name': '现货价:白砂糖:昆明:日'},
    'CF':  {'code': 1340062102, 'name': '国内市场主流价:棉花:3128B:锯齿:全国:日'},
    'OI':  {'code': 1340040037, 'name': '市场价:菜籽油:四级:日'},
    'RM':  {'code': 1340040187, 'name': '出厂价:菜粕:浙江新市:日'},
    'ZC':  {'code': 1320260109, 'name': '国内市场价格:动力煤:Q5500:河北:日'},
    'PK':  {'code': 1340074131, 'name': '市场价:花生油:一级普通:山东烟台:莱阳鲁花:日'},
}

try:
    conn = pyodbc.connect(CONN_JY, timeout=120)
    p("已连接聚源JYDB")

    p(f"\nStep 1: 手工精选指标({len(CURATED_INDICATORS)}个品种)")

    # Step 2: 采集每个指标的2020-2025时序数据
    p(f"\nStep 2: 采集2020-2025时序数据")
    all_data = []
    success_cnt = 0
    fail_list = []
    for vcode in sorted(CURATED_INDICATORS.keys()):
        info = CURATED_INDICATORS[vcode]
        code = info['code']
        name = info['name']
        vcn = VARIETY_CN.get(vcode, vcode)
        try:
            df_t = pd.read_sql(f"""
                SELECT IndicatorCode, EndDate, DataValue
                FROM C_IN_IndicatorDataV
                WHERE IndicatorCode = {code}
                AND EndDate >= '2020-01-01' AND EndDate <= '2025-12-31'
                ORDER BY EndDate
            """, conn)
            if len(df_t) > 0:
                df_t['variety'] = vcode
                df_t['variety_cn'] = vcn
                df_t['indicator_code'] = code
                df_t['indicator_name'] = name
                df_t['DataValue'] = pd.to_numeric(df_t['DataValue'], errors='coerce')
                all_data.append(df_t)
                success_cnt += 1
                p(f"  [{success_cnt}/{len(CURATED_INDICATORS)}] {vcode:4s} ({vcn:6s}) | {len(df_t):5d}行 | {df_t['EndDate'].min().date()} ~ {df_t['EndDate'].max().date()} | {name}")
            else:
                fail_list.append((vcode, code, '无数据'))
                p(f"  [失败] {vcode:4s} ({vcn}) | IndicatorCode={code} | 无数据 | {name}")
        except Exception as e:
            fail_list.append((vcode, code, str(e)))
            p(f"  [失败] {vcode:4s} ({vcn}) | IndicatorCode={code} | {e}")

    if all_data:
        df_all = pd.concat(all_data, ignore_index=True)
        # 重命名列
        df_all = df_all.rename(columns={
            'EndDate': 'trade_date',
            'DataValue': 'spot_price',
        })
        # 调整列顺序
        df_all = df_all[['variety','variety_cn','trade_date','spot_price','indicator_code','indicator_name']]
        df_all = df_all.sort_values(['variety','trade_date']).reset_index(drop=True)

        out_file = f'{OUT_DIR}/spot_prices_daily.csv'
        df_all.to_csv(out_file, index=False, encoding='utf-8-sig')
        size_mb = os.path.getsize(out_file) / 1024 / 1024
        p(f"\n已保存: {out_file}")
        p(f"文件大小: {size_mb:.2f} MB")
        p(f"总行数: {len(df_all):,}")
        p(f"品种数: {df_all['variety'].nunique()}")
        p(f"日期范围: {df_all['trade_date'].min().date()} ~ {df_all['trade_date'].max().date()}")

        p("\n数据质量检查:")
        for v, g in df_all.groupby('variety'):
            miss = g['spot_price'].isna().sum()
            zeros = (g['spot_price']==0).sum()
            p(f"  {v:4s} ({g['variety_cn'].iloc[0]:6s}) | {len(g):5d}行 | 缺失={miss:3d} | 零值={zeros:3d} | {g['trade_date'].min().date()} ~ {g['trade_date'].max().date()}")

    if fail_list:
        p(f"\n失败指标({len(fail_list)}个):")
        for v, code, msg in fail_list:
            p(f"  {v} | {code} | {msg}")

    conn.close()
    p("\n=== 完成 ===")
except Exception as e:
    p(f"ERROR: {e}")
    import traceback
    p(traceback.format_exc())

f.close()

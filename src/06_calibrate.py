"""주민등록 행정동별 연령 인구(2026.9)로 WorldPop 격자 인구를 재배분."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW, OUT, RES, FIG
import glob, csv, io, re, pandas as pd, geopandas as gpd, numpy as np
SRC=RAW; OUT=OUT
rows={}
for f in glob.glob(SRC+'*연령별인구현황*.csv'):
    txt=open(f,'rb').read().decode('cp949'); r=list(csv.reader(io.StringIO(txt))); h=r[0]
    if not h[-1].endswith('100세 이상'): continue   # 연령 범위가 잘린 파일 제외
    for row in r[1:]:
        m=re.search(r'\((\d{10})\)',row[0]); code=m.group(1)
        if code.endswith('00000'): continue  # 구 합계 행
        d={c:int(v.replace(',','')) for c,v in zip(h[1:],row[1:]) if c.startswith('2026년09월_계_')}
        tot=d['2026년09월_계_총인구수']
        old=sum(v for c,v in d.items() if re.search(r'_(6[5-9]|[7-9]\d)~\d+세$|100세 이상$',c))
        rows[code]=dict(emdcd=code,name=row[0].split('(')[0].strip(),reg_total=tot,reg_65=old)
reg=pd.DataFrame(rows.values()); print('행정동',len(reg),'총인구',reg.reg_total.sum(),'65+',reg.reg_65.sum())
reg.to_csv(OUT+'registered_pop_admdong_202609.csv',index=False,encoding='utf-8-sig')
g=gpd.read_file(OUT+'daejeon_grid100m.gpkg'); g['emdcd']=g.emdcd.astype(str)
miss=set(g.emdcd)-set(reg.emdcd); print('매칭 안 된 동',miss)
s=g.groupby('emdcd')[['pop65','pop_total']].sum().rename(columns={'pop65':'wp65','pop_total':'wptot'})
k=reg.set_index('emdcd').join(s)
k['f65']=k.reg_65/k.wp65; k['ftot']=k.reg_total/k.wptot
g=g.merge(k[['f65','ftot']],left_on='emdcd',right_index=True,how='left')
g['pop65_wp']=g.pop65; g['pop_total_wp']=g.pop_total
g['pop65']=(g.pop65*g.f65).round(2); g['pop_total']=(g.pop_total*g.ftot).round(2)
g['old_ratio']=np.where(g.pop_total>0,g.pop65/g.pop_total,np.nan).round(3)
g.drop(columns=['f65','ftot']).to_file(OUT+'daejeon_grid100m.gpkg',layer='grid',driver='GPKG')
print('보정 후 65+',round(g.pop65.sum()),'총',round(g.pop_total.sum()))
print(k.assign(ratio=k.reg_65/k.reg_total).sort_values('ratio',ascending=False)[['name','reg_total','reg_65','ratio']].head(5).round(3).to_string())
print('동별 고령비율 범위', round((k.reg_65/k.reg_total).min(),3), round((k.reg_65/k.reg_total).max(),3))

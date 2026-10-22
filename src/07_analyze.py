import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW, OUT, RES, FIG
import geopandas as gpd, pandas as pd, numpy as np, json
from scipy.spatial import cKDTree
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler
OUT=OUT; AN=RES
g=gpd.read_file(OUT+'daejeon_grid100m.gpkg').to_crs(5179)
st=gpd.read_file(OUT+'daejeon_bus_stops.geojson').to_crs(5179)
c=g.geometry.centroid; cxy=np.c_[c.x,c.y]; sxy=np.c_[st.geometry.x,st.geometry.y]
nr=st.n_routes.values.astype(float); nr[nr==0]=1  # 노선 매칭 안 된 정류장도 최소 1노선으로 간주
T=cKDTree(sxy)
# 1) 서비스 접근성 지수 (PTAL 단순화): 600m 내 정류장의 노선 수 × 거리감쇠
sai=np.zeros(len(g))
for i,idx in enumerate(T.query_ball_point(cxy,600)):
    if idx:
        d=np.hypot(sxy[idx,0]-cxy[i,0],sxy[idx,1]-cxy[i,1]); sai[i]=(nr[idx]*np.clip(1-d/600,0,1)).sum()
g['sai']=sai.round(2)
pop=g.pop_total>0
pct=g.loc[pop,'sai'].rank(pct=True); g['sai_pct']=np.nan; g.loc[pop,'sai_pct']=(pct*100).round(1)
# 1b) 보행거리 보정: 보행망이 끊겨(OSM 단지 내부 길 누락 등) 직선거리의 2.5배를 넘으면 직선×1.3으로 대체
w=g.walk_dist_stop_m; bad=w.isna()|(w>g.dist_stop_m*2.5+100)
g['walk_eff_m']=np.where(bad,g.dist_stop_m*1.3,w).round(0); g['walk_fixed']=bad
g['walk_dist_stop_m']=g['walk_eff_m']
print('보행거리 보정 격자',int(bad.sum()))
# 2) 사각지대 정의
WALK=500; LOWPCT=20; MINPOP=3
g['far']=(g.walk_dist_stop_m>WALK)|g.walk_dist_stop_m.isna()
g['low']=g.sai_pct<=LOWPCT
g['blind']=(g.pop65>=MINPOP)&(g.far|g.low)
# 3) 행정동: 평균 vs 격자
def wavg(x,w): return np.average(x,weights=w) if w.sum()>0 else np.nan
rows=[]
for (sgg,emd),d in g.groupby(['sggnm','emdnm']):
    rows.append(dict(sggnm=sgg,emdnm=emd,pop_total=d.pop_total.sum(),pop65=d.pop65.sum(),
      mean_walk_m=wavg(d.walk_dist_stop_m.fillna(5000),d.pop_total),
      mean_sai=wavg(d.sai,d.pop_total),
      blind_pop65=d.loc[d.blind,'pop65'].sum(), blind_cells=int(d.blind.sum())))
dz=pd.DataFrame(rows); dz['blind_share']=dz.blind_pop65/dz.pop65
city_med_walk=np.median(dz.mean_walk_m)
dz['avg_ok']=dz.mean_walk_m<=300   # 동 평균으로 보면 '정류장 300m 이내' 양호
dz['hidden']=dz.avg_ok&(dz.blind_pop65>=100)
dz=dz.sort_values('blind_pop65',ascending=False)
dz.round(3).to_csv(AN+'admdong_blindspot.csv',index=False,encoding='utf-8-sig')
# 4) 사각지대 포켓(DBSCAN) + 유형(KMeans)
b=g[g.blind].copy(); bc=b.geometry.centroid
lab=DBSCAN(eps=150,min_samples=3).fit_predict(np.c_[bc.x,bc.y]); b['pocket']=lab
p=b[b.pocket>=0].groupby('pocket').agg(cells=('cell_id','size'),pop65=('pop65','sum'),
   walk=('walk_dist_stop_m',lambda x:x.fillna(5000).mean()),sai=('sai','mean'),
   sggnm=('sggnm',lambda x:x.mode()[0]),emdnm=('emdnm',lambda x:x.mode()[0])).reset_index()
p['density']=p.pop65/p.cells
p=p[p.pop65>=30].copy()  # 노인 30명 이상 포켓만 정책 대상
X=StandardScaler().fit_transform(np.c_[np.log1p(p.pop65),p.density,np.log1p(p.walk)])
km=KMeans(3,n_init=20,random_state=42).fit(X); p['k']=km.labels_
cent=p.groupby('k')[['pop65','density','walk']].mean()
dense_k=cent.density.idxmax()                  # 밀도 최고 → 기존 노선 조정·정류장 신설
rest=cent.drop(dense_k).sort_values('pop65')   # 나머지 중 노인 수가 많은(넓게 퍼진) 군집 → DRT, 작은 군집 → 바우처
names={dense_k:'A. 밀집형 → 노선 경유 조정·정류장 신설',rest.index[1]:'B. 광역 저밀형 → 수요응답형(DRT) 버스',rest.index[0]:'C. 소규모 산재형 → 교통바우처·공공형 택시'}
p['type']=p.k.map(names)
b=b.merge(p[['pocket','type']],on='pocket',how='left')
p.sort_values('pop65',ascending=False).round(2).to_csv(AN+'blind_pockets.csv',index=False,encoding='utf-8-sig')
gpd.GeoDataFrame(b,geometry='geometry',crs=5179).to_crs(4326).to_file(AN+'blind_cells.gpkg',driver='GPKG')
g.to_crs(4326).to_file(AN+'grid_scored.gpkg',driver='GPKG')
# 5) 요약 통계
S=dict(pop_total=g.pop_total.sum(),pop65=g.pop65.sum(),
 pop65_far500=g.loc[g.far,'pop65'].sum(), blind_pop65=g.loc[g.blind,'pop65'].sum(), blind_cells=int(g.blind.sum()),
 pockets=len(p), pocket_pop65=p.pop65.sum(),
 hidden_dongs=int(dz.hidden.sum()), hidden_pop65=dz.loc[dz.hidden,'blind_pop65'].sum(),
 avg_ok_dongs=int(dz.avg_ok.sum()), dongs=len(dz),
 type_summary=p.groupby('type').agg(n=('pocket','size'),pop65=('pop65','sum'),density=('density','mean'),walk=('walk','mean')).round(1).reset_index().to_dict('records'),
 sgg_blind=g[g.blind].groupby('sggnm').pop65.sum().round(0).to_dict(),
 sgg_pop65=g.groupby('sggnm').pop65.sum().round(0).to_dict())
S={k:(round(float(v),1) if isinstance(v,(float,np.floating)) else v) for k,v in S.items()}
json.dump(S,open(AN+'summary.json','w'),ensure_ascii=False,indent=1,default=float)
print(json.dumps(S,ensure_ascii=False,indent=1,default=float))
print(dz.head(12).round(2).to_string(index=False))
print(p.sort_values('pop65',ascending=False).head(12).round(1).to_string(index=False))

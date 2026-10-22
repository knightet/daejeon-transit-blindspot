"""WorldPop 100m 연령별 인구 래스터 -> 대전 100m 격자(GeoPackage) + 교통 접근성 지표."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW, OUT, RES, FIG
import glob, os, numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio.windows import from_bounds
from shapely.geometry import box
SRC=RAW; OUT=OUT
bd=gpd.read_file(OUT+'daejeon_admdong_2026.geojson')[['emdcd','emdnm','sggnm','geometry']]
minx,miny,maxx,maxy=bd.total_bounds
bands={}
for f in sorted(glob.glob(SRC+'kor_*_2025_CN_100m_R2025A_v1.tif')):
    k=os.path.basename(f).split('_2025')[0].replace('kor_','')
    try: r=rasterio.open(f)
    except Exception as e: print('skip',f,str(e)[:60]); continue
    with r:
        w=from_bounds(minx-0.002,miny-0.002,maxx+0.002,maxy+0.002,r.transform).round_offsets().round_lengths()
        a=r.read(1,window=w).astype('float64'); nd=r.nodata
        if nd is not None: a[a==nd]=0
        a[a<0]=0; bands[k]=a; tr=r.window_transform(w)
print('bands',sorted(bands))
H,W=next(iter(bands.values())).shape
old=[k for k in ['t_65','t_70','t_75','t_80','t_85','t_90'] if k in bands]
pop65=sum(bands[k] for k in old)
tot=(bands.get('T_F',0)+bands.get('T_M',0)) if 'T_M' in bands and 'T_F' in bands else None
rows,cols=np.nonzero((pop65>0) | (tot>0 if tot is not None else False))
xs,ys=rasterio.transform.xy(tr,rows,cols,offset='center')
rx,ry=tr.a,-tr.e
geom=[box(x-rx/2,y-ry/2,x+rx/2,y+ry/2) for x,y in zip(xs,ys)]
g=gpd.GeoDataFrame({'row':rows,'col':cols,'pop65':pop65[rows,cols].round(2)},geometry=geom,crs=4326)
for k in old: g[k]=bands[k][rows,cols].round(2)
g['pop65_bands']=','.join(old)
if tot is not None:
    g['pop_total']=tot[rows,cols].round(2); g['old_ratio']=np.where(g.pop_total>0,g.pop65/g.pop_total,np.nan).round(3)
c=g.copy(); c['geometry']=g.geometry.centroid
c=gpd.sjoin(c,bd,how='inner',predicate='within').drop(columns='index_right')
g=g.loc[c.index].join(c[['emdcd','emdnm','sggnm']])
g['cell_id']=['DJ_%d_%d'%(r,cc) for r,cc in zip(g.row,g.col)]
# --- 접근성 지표 (EPSG:5179, m)
G=g.to_crs(5179); C=G.copy(); C['geometry']=G.centroid
st=gpd.read_file(OUT+'daejeon_bus_stops.geojson').to_crs(5179)
rl=pd.read_csv(OUT+'daejeon_route_stop_links.csv',dtype=str)
sub=gpd.read_file(OUT+'daejeon_rail_stations.geojson').to_crs(5179)
fac=gpd.read_file(OUT+'daejeon_facilities.geojson').to_crs(5179)
from scipy.spatial import cKDTree
cxy=np.c_[C.geometry.x,C.geometry.y]
sxy=np.c_[st.geometry.x,st.geometry.y]; T=cKDTree(sxy)
d,_=T.query(cxy); g['dist_stop_m']=d.round(0)
stop_ids=st.osm_id.astype(str).values
routes_by_stop=rl.groupby('osm_id').route_ref.apply(set).to_dict()
n400=[];r400=[]
for idx in T.query_ball_point(cxy,400):
    n400.append(len(idx)); s=set()
    for i in idx: s|=routes_by_stop.get(stop_ids[i],set())
    r400.append(len(s))
g['stops_400m']=n400; g['routes_400m']=r400
subxy=np.c_[sub.geometry.x,sub.geometry.y]
g['dist_subway_m']=cKDTree(subxy).query(cxy)[0].round(0)
for cat,col in [('의료(병의원)','dist_clinic_m'),('시장/마트','dist_market_m'),('복지시설','dist_welfare_m')]:
    f=fac[fac.category==cat]
    if len(f): g[col]=cKDTree(np.c_[f.geometry.centroid.x,f.geometry.centroid.y]).query(cxy)[0].round(0)

# --- 보행 네트워크 거리(가장 가까운 정류장까지 실제 걸어서 m)
import osmnx as ox, networkx as nx
WGp=ox.project_graph(ox.load_graphml(OUT+'daejeon_walk_network.graphml'),to_crs='EPSG:5179')
WGu=nx.MultiGraph(WGp)  # 보행은 양방향
stop_nodes=set(ox.distance.nearest_nodes(WGp,sxy[:,0],sxy[:,1]))
dist=nx.multi_source_dijkstra_path_length(WGu,stop_nodes,weight='length',cutoff=5000)
cn,cd=ox.distance.nearest_nodes(WGp,cxy[:,0],cxy[:,1],return_dist=True)
g['walk_dist_stop_m']=[round(dist.get(n,np.nan)+d,0) if n in dist else np.nan for n,d in zip(cn,cd)]
g.drop(columns=['row','col']).to_file(OUT+'daejeon_grid100m.gpkg',layer='grid',driver='GPKG')
g.drop(columns='geometry').drop(columns=['row','col']).to_csv(OUT+'daejeon_grid100m.csv',index=False,encoding='utf-8-sig')
print(len(g),'cells; pop65 sum',round(g.pop65.sum()), 'total', round(g.pop_total.sum()) if 'pop_total' in g else None)
print(g[['pop65','dist_stop_m','walk_dist_stop_m','stops_400m','routes_400m','dist_subway_m']].describe().round(1))

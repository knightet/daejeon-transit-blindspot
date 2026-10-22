"""최대커버링 입지(MCLP) 탐욕 알고리즘: 정류장 N개를 새로 둘 때 사각지대 노인을 가장 많이 해소하는 위치."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW, OUT, RES, FIG
import osmnx as ox, networkx as nx, geopandas as gpd, pandas as pd, numpy as np, json
from scipy.spatial import cKDTree
AN=RES
G=ox.project_graph(ox.load_graphml(OUT+'daejeon_walk_network.graphml'),to_crs='EPSG:5179')
U=nx.Graph()
for u,v,d in G.edges(data=True):
    w=d.get('length',1.0)
    if not U.has_edge(u,v) or U[u][v]['length']>w: U.add_edge(u,v,length=w)
nodes,edges=ox.graph_to_gdfs(G)
# 버스가 다닐 수 있는 도로(간선~집산로)에 붙은 노드만 후보
BUSROAD={'trunk','primary','secondary','tertiary','trunk_link','primary_link','secondary_link','tertiary_link','unclassified'}
def isbus(h): h=h if isinstance(h,list) else [h]; return any(x in BUSROAD for x in h)
cand_nodes=set()
for (u,v,k),h in edges['highway'].items():
    if isbus(h): cand_nodes.update([u,v])
b=gpd.read_file(AN+'blind_cells.gpkg').to_crs(5179)
bc=b.geometry.centroid; bn,bd=ox.distance.nearest_nodes(G,bc.x.values,bc.y.values,return_dist=True)
b['node']=bn; b['snapd']=bd; snap=bd
WALK=400  # 신설 정류장에서 노인 보행 400m(약 6~7분) 이내면 해소
# 후보: 사각지대에서 1km 이내 버스 도로 노드
nxy=nodes.loc[list(cand_nodes),['x','y']]; T=cKDTree(np.c_[bc.x,bc.y])
near=T.query_ball_point(nxy.values,1000); cands=[n for n,i in zip(nxy.index,near) if i]
print('후보 노드',len(cands),'사각지대 격자',len(b))
node2cells={}
for i,n in enumerate(b.node): node2cells.setdefault(n,[]).append(i)
cover={}
for c in cands:
    if c not in U: continue
    dist=nx.single_source_dijkstra_path_length(U,c,cutoff=WALK,weight='length')
    cells=[i for n,dd in dist.items() for i in node2cells.get(n,[]) if dd+snap[i]<=WALK]
    if cells: cover[c]=set(cells)
pop=b.pop65.values; covered=set(); picks=[]
for k in range(30):
    best=max(cover,key=lambda c: pop[list(cover[c]-covered)].sum() if cover[c]-covered else 0)
    gain=pop[list(cover[best]-covered)].sum()
    if gain<20: break
    covered|=cover[best]
    x,y=nodes.loc[best,['x','y']]
    cell=b.iloc[list(cover[best])]
    picks.append(dict(rank=k+1,node=int(best),x=x,y=y,gain65=round(gain),cum65=round(pop[list(covered)].sum()),
       emdnm=cell.emdnm.mode()[0],sggnm=cell.sggnm.mode()[0],type=cell['type'].mode()[0] if cell['type'].notna().any() else '소규모'))
P=gpd.GeoDataFrame(picks,geometry=gpd.points_from_xy([p['x'] for p in picks],[p['y'] for p in picks]),crs=5179)
P4=P.to_crs(4326); P['lon']=P4.geometry.x.round(6); P['lat']=P4.geometry.y.round(6)
P.drop(columns=['geometry','x','y','node']).to_csv(AN+'new_stop_candidates.csv',index=False,encoding='utf-8-sig')
P.to_crs(4326).to_file(AN+'new_stop_candidates.gpkg',driver='GPKG')
b['covered']=[i in covered for i in range(len(b))]
b.to_crs(4326).to_file(AN+'blind_cells_covered.gpkg',driver='GPKG')
tot=pop.sum()
res=dict(blind_pop65=round(tot),cands=len(cover),
  by_n={n:dict(cum=int(P.cum65.iloc[n-1]),share=round(P.cum65.iloc[n-1]/tot*100,1)) for n in (5,10,20,len(P)) if n<=len(P)},n_picked=len(P))
S=json.load(open(AN+'summary.json')); S['mclp']=res; json.dump(S,open(AN+'summary.json','w'),ensure_ascii=False,indent=1)
print(json.dumps(res,ensure_ascii=False)); print(P[['rank','sggnm','emdnm','gain65','cum65','type','lat','lon']].head(12).to_string(index=False))

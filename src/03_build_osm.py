import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW, OUT, RES, FIG
import pandas as pd, geopandas as gpd, sys
src=RAW; out=OUT
bd=gpd.read_file(out+'daejeon_admdong_2026.geojson')[['emdcd','emdnm','sggnm','geometry']]
def pts(df,lat='@lat',lon='@lon'):
    return gpd.GeoDataFrame(df,geometry=gpd.points_from_xy(df[lon],df[lat]),crs=4326)
s=pd.read_csv(src+'daejeon_osm_bus_stops.tsv',sep='\t',dtype=str).rename(columns={'@id':'osm_id','@lat':'lat','@lon':'lon'})
s[['lat','lon']]=s[['lat','lon']].astype(float)
r=pd.read_csv(src+'daejeon_osm_bus_routes.tsv',sep='\t',dtype=str).fillna('')
r['n_stops']=r.stop_node_ids.str.split().str.len()
rows=[(sid,row.osm_id,row.ref,row.network) for row in r.itertuples() for sid in set(row.stop_node_ids.split())]
m=pd.DataFrame(rows,columns=['osm_id','route_id','route_ref','network'])
agg=m.groupby('osm_id').agg(n_routes=('route_ref','nunique'),routes=('route_ref',lambda x:','.join(sorted(set(x))))).reset_index()
s=s.merge(agg,on='osm_id',how='left'); s['n_routes']=s.n_routes.fillna(0).astype(int)
g=gpd.sjoin(pts(s,'lat','lon'),bd,how='left',predicate='within').drop(columns='index_right')
g.to_file(out+'daejeon_bus_stops.geojson',driver='GeoJSON')
r.drop(columns='stop_node_ids').to_csv(out+'daejeon_bus_routes.csv',index=False,encoding='utf-8-sig')
m.to_csv(out+'daejeon_route_stop_links.csv',index=False)
f=pd.read_csv(src+'daejeon_osm_facilities.tsv',sep='\t',dtype=str).fillna('').rename(columns={'@type':'osm_type','@id':'osm_id','@lat':'lat','@lon':'lon'})
f=f[f.lat!='']; f[['lat','lon']]=f[['lat','lon']].astype(float)
def cat(x):
    if x.amenity in('hospital','clinic','doctors'): return '의료(병의원)'
    if x.amenity=='pharmacy': return '약국'
    if x.amenity=='marketplace' or x.shop=='supermarket': return '시장/마트'
    if x.amenity=='social_facility': return '복지시설'
    if x.amenity in('community_centre','townhall'): return '주민센터/커뮤니티'
    return '기타'
f['category']=f.apply(cat,axis=1)
fg=gpd.sjoin(pts(f,'lat','lon'),bd,how='left',predicate='within').drop(columns='index_right')
fg.to_file(out+'daejeon_facilities.geojson',driver='GeoJSON')
rs=pd.read_csv(src+'daejeon_osm_rail_stations.tsv',sep='\t',dtype=str).fillna('').rename(columns={'@id':'osm_id','@lat':'lat','@lon':'lon'})
rs[['lat','lon']]=rs[['lat','lon']].astype(float)
pts(rs,'lat','lon').to_file(out+'daejeon_rail_stations.geojson',driver='GeoJSON')
print('stops',len(g),'in-boundary',g.emdcd.notna().sum(),'with routes',(g.n_routes>0).sum())
print(g.n_routes.describe())
print('routes',len(r), 'with interval tag',(r.interval!='').sum()); print(r.network.value_counts().head(8))
print(fg.category.value_counts())

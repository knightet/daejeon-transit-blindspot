import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW, OUT, RES, FIG
import osmnx as ox, networkx as nx, geopandas as gpd, glob
bd=gpd.read_file(OUT+'daejeon_admdong_2026.geojson'); poly=bd.union_all().buffer(0.005)
gs=[]
for f in glob.glob(RAW+'daejeon_walk_*.osm'):
    G=ox.graph_from_xml(f,simplify=False,retain_all=True)
    G=ox.truncate.truncate_graph_polygon(G,poly,truncate_by_edge=True)
    print(f.split('_')[-1],len(G.nodes),len(G.edges)); gs.append(G)
G=nx.compose_all(gs); G=ox.simplify_graph(G)
import networkx as _nx; print("components",_nx.number_weakly_connected_components(G))
print('merged',len(G.nodes),len(G.edges))
ox.save_graphml(G,OUT+'daejeon_walk_network.graphml')
n,e=ox.graph_to_gdfs(G)
e[['osmid','highway','length','geometry']].assign(osmid=lambda d:d.osmid.astype(str),highway=lambda d:d.highway.astype(str)).reset_index().to_file(OUT+'daejeon_walk_edges.gpkg',driver='GPKG')
# per-district edge length check
ej=gpd.sjoin(e.reset_index()[['length','geometry']].assign(geometry=lambda d:d.geometry.centroid),bd[['sggnm','geometry']],predicate='within')
print((ej.groupby('sggnm').length.sum()/1000).round(0))

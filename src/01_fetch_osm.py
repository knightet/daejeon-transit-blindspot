"""OpenStreetMap(Overpass API)에서 대전 버스정류장·노선·시설·철도역·보행 도로망 수집.
Overpass 서버가 붐비면 504가 날 수 있어 재시도합니다. 데이터: © OpenStreetMap contributors (ODbL)."""
import os, sys, time, json, requests; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW
URL = 'https://overpass-api.de/api/interpreter'
A = 'area["name"="대전광역시"]["admin_level"="4"]->.a;'
def op(q, tries=6):
    for i in range(tries):
        r = requests.post(URL, data={'data': q}, timeout=400)
        if r.ok and 'runtime error' not in r.text[:2000]:
            return r.text
        print('retry', r.status_code); time.sleep(15)
    raise RuntimeError('Overpass 실패')
def save(name, text): open(RAW + name, 'w', encoding='utf-8').write(text); print(name, len(text))
save('daejeon_osm_bus_stops.tsv', op(f'[out:csv(::id,::lat,::lon,name,"ref","local_ref";true;"\\t")][timeout:180];{A}(node["highway"="bus_stop"](area.a);node["public_transport"="platform"]["bus"="yes"](area.a););out;'))
rj = json.loads(op(f'[out:json][timeout:180];{A}relation["route"="bus"](area.a);out body;'))
rows = ['osm_id\tref\tname\tnetwork\toperator\tinterval\tduration\topening_hours\tstop_node_ids']
for e in rj['elements']:
    t = e.get('tags', {})
    rows.append('\t'.join([str(e['id'])] + [t.get(k, '') for k in ('ref','name','network','operator','interval','duration','opening_hours')] + [' '.join(str(m['ref']) for m in e['members'] if m['type']=='node')]))
save('daejeon_osm_bus_routes.tsv', '\n'.join(rows))
save('daejeon_osm_facilities.tsv', op(f'[out:csv(::type,::id,::lat,::lon,amenity,healthcare,social_facility,shop,name;true;"\\t")][timeout:180];{A}(nwr["amenity"~"^(hospital|clinic|doctors|pharmacy|marketplace|community_centre|social_facility|townhall)$"](area.a);nwr["shop"="supermarket"](area.a););out center;'))
save('daejeon_osm_rail_stations.tsv', op(f'[out:csv(::id,::lat,::lon,name,railway,station,subway;true;"\\t")][timeout:180];{A}(node["railway"="station"](area.a);node["station"="subway"](area.a););out;'))
WALK = 'way["highway"]["area"!~"yes"]["highway"!~"abandoned|bus_guideway|construction|cycleway|motor|no|planned|platform|proposed|raceway|razed"]["foot"!~"no"]["service"!~"private"](area.g);(._;>;);out;'
for gu in ['동구', '중구', '서구', '유성구', '대덕구']:
    q = f'[out:xml][timeout:300];{A}rel["admin_level"="6"]["name"="{gu}"](area.a);map_to_area->.g;{WALK}'
    save(f'daejeon_walk_{gu}.osm', op(q))

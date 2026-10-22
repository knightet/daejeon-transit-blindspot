"""대전 행정동 경계(2026.7) 추출 — vuski/admdongkor 패키지."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUT
import admdongkor as a
g = a.get('20260701', level='emd', detail=True, crs=4326)
d = g[g['sidonm'].str.contains('대전')].copy()
d.to_file(OUT + 'daejeon_admdong_2026.geojson', driver='GeoJSON')
print('행정동', len(d))

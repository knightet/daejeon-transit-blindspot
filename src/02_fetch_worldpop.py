"""WorldPop 2025 연령별 인구 100m 격자(R2025A, constrained) 내려받기 — 한국 전체, 파일당 약 37MB.
데이터: WorldPop (CC BY 4.0)."""
import os, sys, requests; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW
BASE = 'https://data.worldpop.org/GIS/AgeSex_structures/Global_2015_2030/R2025A/2025/KOR/v1/100m/constrained/'
for k in ['t_65', 't_70', 't_75', 't_80', 't_85', 't_90', 'T_F', 'T_M']:
    f = f'kor_{k}_2025_CN_100m_R2025A_v1.tif'
    if os.path.exists(RAW + f): print('있음', f); continue
    with requests.get(BASE + f, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(RAW + f, 'wb') as o:
            for c in r.iter_content(1 << 20): o.write(c)
    print('완료', f)

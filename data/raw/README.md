# 원본 데이터 (data/raw)

용량과 라이선스 때문에 원본 데이터는 저장소에 올리지 않았습니다. 아래 방법으로 이 폴더에 넣으면 `python run_all.py`로 전체 분석이 재현됩니다.

| 파일 | 받는 방법 | 출처 · 라이선스 |
|---|---|---|
| `daejeon_osm_*.tsv`, `daejeon_walk_*.osm` | `python src/01_fetch_osm.py` (자동) | OpenStreetMap contributors, ODbL · Overpass API |
| `kor_t_65~90_…tif`, `kor_T_F/T_M_…tif` | `python src/02_fetch_worldpop.py` (자동, 약 300MB) | WorldPop R2025A, CC BY 4.0 |
| `*연령별인구현황*.csv` (5개 구) | 수동: [jumin.mois.go.kr](https://jumin.mois.go.kr) → 연령별 인구현황 → 2026년 9월, 대전광역시 각 구, 읍면동 포함, 5세 단위, 0세~100세 이상 → CSV | 행정안전부 주민등록 인구통계, 공공누리 |
| (검증용) 버스정류장 현황 | 수동: [공공데이터포털 15066754](https://www.data.go.kr/data/15066754/fileData.do) | 한국교통안전공단, 공공누리 |

행정동 경계는 `src/00_boundary.py`가 `admdongkor` 패키지로 자동으로 가져옵니다.

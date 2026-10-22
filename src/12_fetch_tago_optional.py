"""
대전 시내버스 노선별 배차간격 + 경유 정류장 수집 (국토교통부 TAGO 버스노선정보 API)

사용법 (내 PC에서 실행):
  1) 공공데이터포털에서 '국토교통부_(TAGO)_버스노선정보' 활용신청 → 일반 인증키(Decoding) 복사
     https://www.data.go.kr/data/15098529/openapi.do
  2) pip install requests pandas
  3) python fetch_tago_daejeon.py 발급받은키
결과: tago_daejeon_routes.csv (노선별 평일/토/일 배차간격, 첫차·막차)
      tago_daejeon_route_stops.csv (노선별 경유 정류장, 정류소번호·좌표)
"""
import sys, time, requests, pandas as pd
KEY = sys.argv[1]; CITY = 25  # 대전광역시 도시코드
BASE = 'http://apis.data.go.kr/1613000/BusRouteInfoInqireService'

def call(op, **p):
    p.update(serviceKey=KEY, cityCode=CITY, _type='json', numOfRows=1000, pageNo=1)
    for _ in range(3):
        try:
            j = requests.get(f'{BASE}/{op}', params=p, timeout=20).json()
            it = j['response']['body']['items']
            if not it: return []
            it = it['item']; return it if isinstance(it, list) else [it]
        except Exception as e:
            print('retry', op, e); time.sleep(2)
    return []

routes = call('getRouteNoList')
print('노선 수', len(routes))
info, stops = [], []
for r in routes:
    rid = r['routeid']
    d = call('getRouteInfoIem', routeId=rid)
    if d: info.append(d[0])
    for s in call('getRouteAcctoThrghSttnList', routeId=rid):
        s['routeid'] = rid; s['routeno'] = r.get('routeno'); stops.append(s)
    time.sleep(0.1)
pd.DataFrame(info).to_csv('tago_daejeon_routes.csv', index=False, encoding='utf-8-sig')
pd.DataFrame(stops).to_csv('tago_daejeon_route_stops.csv', index=False, encoding='utf-8-sig')
print('완료:', len(info), '노선 /', len(stops), '노선-정류장')

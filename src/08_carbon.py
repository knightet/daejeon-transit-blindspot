import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW, OUT, RES, FIG
import json
S=json.load(open(RES+'summary.json'))
P=S['pocket_pop65']; EF=0.187
sc={'보수':dict(trips=1.0,km=3,shift=0.2),'중립':dict(trips=2.0,km=4,shift=0.3),'적극':dict(trips=2.0,km=5,shift=0.5)}
drt_n=next(t['n'] for t in S['type_summary'] if t['type'].startswith('B')); DKM=150; DI=0.45
res={}
for k,v in sc.items():
    car_km=P*v['trips']*v['km']*v['shift']*365; gross=car_km*EF/1000; dd=drt_n*DKM*365*DI/1000
    res[k]=dict(**v,car_km=round(car_km),gross_t=round(gross),net_diesel_t=round(gross-dd),net_ev_t=round(gross))
S['carbon']=dict(pocket_pop65=P,ef_kg_km=EF,drt_vehicles=drt_n,drt_km_day=DKM,diesel_kg_km=DI,scenarios=res)
json.dump(S,open(RES+'summary.json','w'),ensure_ascii=False,indent=1); print(res)

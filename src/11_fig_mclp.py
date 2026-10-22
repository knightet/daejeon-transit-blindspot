import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW, OUT, RES, FIG
import geopandas as gpd, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'Noto Sans CJK KR','axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#bdbcb6','xtick.color':'#52514e','ytick.color':'#52514e','axes.labelcolor':'#52514e'})
F=FIG
P=pd.read_csv(RES+'new_stop_candidates.csv'); tot=gpd.read_file(RES+'blind_cells_covered.gpkg').pop65.sum()
fig,ax=plt.subplots(figsize=(8,4.2))
ax.plot(P['rank'],P.cum65,color='#2a78d6',lw=2); ax.scatter(P['rank'],P.cum65,s=16,color='#2a78d6',zorder=3)
for n in (5,10,20,30):
    r=P[P['rank']==n]
    if len(r): v=r.cum65.iloc[0]; ax.annotate(f'{n}곳: {v:,}명 ({v/tot*100:.0f}%)',(n,v),xytext=(-10,10),textcoords='offset points',fontsize=9,ha='right',color='#0b0b0b')
ax.set_xlabel('새로 설치하는 정류장 수 (효과 큰 순서)'); ax.set_ylabel('보행 400m 안으로 들어오는 노인(명)')
ax.grid(axis='y',color='#e6e5e0'); ax.set_axisbelow(True)
ax.set_title('')  # 제목은 보고서 캡션으로: 정류장 신설 효과: 처음 10곳이 가장 효율적이고 이후 효과는 점점 줄어듦
plt.tight_layout(); plt.savefig(F+'fig4_mclp_curve.png',dpi=200); plt.close()
b=gpd.read_file(RES+'blind_cells_covered.gpkg').to_crs(5179); bd=gpd.read_file(OUT+'daejeon_admdong_2026.geojson').to_crs(5179)
s=gpd.read_file(RES+'new_stop_candidates.gpkg').to_crs(5179); s10=s[s['rank']<=10]
fig,ax=plt.subplots(figsize=(8.5,8.5))
bd.boundary.plot(ax=ax,color='#d6d5cf',lw=.5)
b[~b.covered].plot(ax=ax,color='#bdbcb6',edgecolor='#bdbcb6',lw=.8)
b[b.covered].plot(ax=ax,color='#1baf7a',edgecolor='#1baf7a',lw=.8)
s10.plot(ax=ax,color='#eb6834',markersize=70,edgecolor='white',linewidth=1.2,zorder=5)
for _,r in s10.iterrows(): ax.annotate(f"{r['rank']}. {r.emdnm}",(r.geometry.x,r.geometry.y),xytext=(7,5),textcoords='offset points',fontsize=9,bbox=dict(boxstyle='round,pad=.15',fc='white',ec='none',alpha=.85))
x0,y0,x1,y1=s10.total_bounds; ax.set_xlim(x0-2500,x1+2500); ax.set_ylim(y0-2500,y1+2500); ax.set_axis_off()
from matplotlib.lines import Line2D; from matplotlib.patches import Patch
ax.legend(handles=[Line2D([],[],marker='o',ls='',color='#eb6834',markersize=9,label='신설 정류장 후보(상위 10곳)'),Patch(color='#1baf7a',label='상위 30곳 신설 시 해소되는 사각지대'),Patch(color='#bdbcb6',label='정류장만으로 해소 안 됨 → DRT·바우처')],loc='lower left',fontsize=9,frameon=False)
ax.set_title('')  # 제목은 보고서 캡션으로: AI 최적화로 찾은 정류장 신설 후보지
plt.savefig(F+'fig5_new_stops.png',dpi=200,bbox_inches='tight'); plt.close(); print('ok')

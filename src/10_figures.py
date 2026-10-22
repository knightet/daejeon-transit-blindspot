import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW, OUT, RES, FIG
import geopandas as gpd, pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Patch
plt.rcParams.update({'font.family':'Noto Sans CJK KR','axes.edgecolor':'#bdbcb6','axes.labelcolor':'#52514e',
  'xtick.color':'#52514e','ytick.color':'#52514e','axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#ffffff'})
F=FIG
bd=gpd.read_file(OUT+'daejeon_admdong_2026.geojson').to_crs(5179)
sgg=bd.dissolve('sggnm').reset_index()
g=gpd.read_file(RES+'grid_scored.gpkg').to_crs(5179)
b=gpd.read_file(RES+'blind_cells.gpkg').to_crs(5179)
dz=pd.read_csv(RES+'admdong_blindspot.csv'); p=pd.read_csv(RES+'blind_pockets.csv')
TXT='#0b0b0b'; MUTE='#8a8984'; GRID='#e6e5e0'
COL={'A':'#2a78d6','B':'#eb6834','C':'#1baf7a'}
def base(ax):
    bd.boundary.plot(ax=ax,color='#d6d5cf',linewidth=.4); sgg.boundary.plot(ax=ax,color='#8a8984',linewidth=.9)
    for _,r in sgg.iterrows():
        c=r.geometry.representative_point(); ax.text(c.x,c.y,r.sggnm,fontsize=11,color=MUTE,ha='center',fontweight='bold')
    ax.set_axis_off()
# 그림1: 노인 인구 + 정류장 보행거리
fig,ax=plt.subplots(1,2,figsize=(13,6.6))
g.plot(column='pop65',ax=ax[0],cmap='Blues',vmax=g.pop65.quantile(.98),linewidth=0,legend=True,legend_kwds={'shrink':.6,'label':'격자당 65세 이상(명)'})
base(ax[0]); ax[0].set_title('')  # 제목은 보고서 캡션으로: 65세 이상 인구 분포 (100m 격자)
gg=g[g.pop_total>0]
gg.plot(column=gg.walk_eff_m.clip(upper=1000),ax=ax[1],cmap='Oranges',linewidth=0,legend=True,legend_kwds={'shrink':.6,'label':'가장 가까운 정류장까지 보행거리(m, 1,000m 이상은 1,000)'})
base(ax[1]); ax[1].set_title('')  # 제목은 보고서 캡션으로: 가장 가까운 버스 정류장까지 걷는 거리
plt.tight_layout(); plt.savefig(F+'fig1_pop_access.png',dpi=200); plt.close()
# 그림2: 사각지대 유형 지도
fig,ax=plt.subplots(figsize=(9,9.5))
g[g.pop_total>0].plot(ax=ax,color='#f0efec',linewidth=0)
b[b['type'].isna()].plot(ax=ax,color='#bdbcb6',edgecolor='#bdbcb6',linewidth=.8)
for k,c in COL.items():
    s=b[b['type'].fillna('').str.startswith(k)]
    if len(s): s.plot(ax=ax,color=c,edgecolor=c,linewidth=1.2)
base(ax)
top=p.sort_values('pop65',ascending=False).drop_duplicates('emdnm').head(8)
x0,y0,x1,y1=b.total_bounds; pad=1500; ax.set_xlim(x0-pad,x1+pad); ax.set_ylim(y0-pad,y1+pad)
bc=b.dissolve('pocket').reset_index()
for _,(__,r) in enumerate(top.iterrows()):
    geom=bc.loc[bc.pocket==r.pocket,'geometry']
    if len(geom):
        c=geom.iloc[0].centroid; ax.annotate(f"{r.emdnm} {int(round(r.pop65,-1))}명",(c.x,c.y),xytext=(14,10) if _%2==0 else (-90,-16),textcoords='offset points',fontsize=9,color=TXT,
           arrowprops=dict(arrowstyle='-',color=MUTE,lw=.6),bbox=dict(boxstyle='round,pad=.2',fc='white',ec='none',alpha=.85))
names=sorted(p.type.unique())
h=[Patch(color=COL[n[0]],label=n) for n in names]+[Patch(color='#bdbcb6',label='사각지대(노인 30명 미만 소규모)')]
ax.legend(handles=h,loc='lower left',fontsize=9,frameon=False)
ax.set_title('')  # 제목은 보고서 캡션으로: 교통 사각지대와 유형별 처방
plt.tight_layout(); plt.savefig(F+'fig2_blind_types.png',dpi=200); plt.close()
# 그림3: 동 평균 vs 숨은 사각지대
fig,ax=plt.subplots(figsize=(9,5.6))
ax.axvspan(dz.mean_walk_m.min()-20,300,color='#eaf2fb',zorder=0)
ax.scatter(dz.mean_walk_m,dz.blind_pop65,s=34,color='#2a78d6',edgecolor='white',linewidth=1.2,zorder=3)
for _,r in dz.sort_values('blind_pop65',ascending=False).head(8).iterrows():
    ax.annotate(r.emdnm,(r.mean_walk_m,r.blind_pop65),xytext=(6,4),textcoords='offset points',fontsize=9,color=TXT)
ax.axvline(300,color=MUTE,lw=1,ls='--'); ax.axhline(100,color=MUTE,lw=1,ls=':')
ax.text(dz.mean_walk_m.min(),ax.get_ylim()[1]*.95,'동 평균으로 보면 \"양호\"\n(평균 보행거리 300m 이하)',fontsize=9,color='#52514e',va='top')
ax.set_xlabel('행정동 평균 정류장 보행거리 (m, 인구가중)'); ax.set_ylabel('사각지대에 사는 65세 이상 (명)')
ax.grid(axis='y',color=GRID,lw=.8); ax.set_axisbelow(True)
ax.set_title('')  # 제목은 보고서 캡션으로: 평균에 가려진 사각지대: 동 평균은 양호해도 노인 수백 명이 사각지대에
plt.tight_layout(); plt.savefig(F+'fig3_hidden_dongs.png',dpi=200); plt.close()
print('ok')

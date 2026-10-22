"""경로 설정. 모든 스크립트가 여기서 폴더 위치를 가져옵니다."""
import os
ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, 'data', 'raw') + os.sep        # 원본 데이터 (직접/스크립트로 내려받기)
OUT = os.path.join(ROOT, 'data', 'processed') + os.sep  # 가공 데이터 (자동 생성)
RES = os.path.join(ROOT, 'results') + os.sep            # 분석 결과 표·요약
FIG = os.path.join(RES, 'figures') + os.sep             # 그림
for d in (RAW, OUT, RES, FIG):
    os.makedirs(d, exist_ok=True)

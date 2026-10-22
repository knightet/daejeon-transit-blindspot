"""전체 파이프라인 실행. 수집 단계(01·02)는 이미 data/raw에 파일이 있으면 --skip-fetch로 건너뛰세요.
사용: python run_all.py [--skip-fetch]"""
import subprocess, sys, os, glob
ROOT = os.path.dirname(os.path.abspath(__file__))
steps = sorted(glob.glob(os.path.join(ROOT, 'src', '[0-1][0-9]_*.py')))
skip = '--skip-fetch' in sys.argv
for s in steps:
    name = os.path.basename(s)
    if name.startswith('12_') or (skip and name[:2] in ('01', '02')):
        continue
    print(f'\n===== {name}')
    subprocess.run([sys.executable, s], check=True, cwd=ROOT)
print('\n모든 단계 완료 → results/ 폴더를 확인하세요.')

import argparse
from . import prepare, run, evaluate
def main():
 p=argparse.ArgumentParser(prog='parallax'); p.add_argument('command',choices=['prepare','run','evaluate','dashboard']); a=p.parse_args()
 if a.command=='prepare': prepare.main()
 elif a.command=='run': run.main()
 elif a.command=='evaluate': evaluate.main()
 else:
  import subprocess,sys; subprocess.run([sys.executable,'-m','streamlit','run',str(__import__('pathlib').Path(__file__).with_name('dashboard.py'))],check=True)
if __name__=='__main__': main()

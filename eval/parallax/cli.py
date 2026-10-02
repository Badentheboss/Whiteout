"""Thin dispatcher; all commands share the same tested modules."""
import argparse,importlib,subprocess,sys
from pathlib import Path
def main():
    commands={'prepare':'smoke','fetch-real':'corpus','dataset':'dataset','run':'run','evaluate':'evaluate','train':'train','diagnose':'diagnose','calibrate':'calibrate'}
    parser=argparse.ArgumentParser(prog='parallax');parser.add_argument('command',choices=[*commands,'dashboard'])
    args,rest=parser.parse_known_args()
    if args.command=='dashboard':
        subprocess.run([sys.executable,'-m','streamlit','run',str(Path(__file__).with_name('dashboard.py')),'--server.address','127.0.0.1',*rest],check=True)
    else:
        sys.argv=['parallax '+args.command,*rest];importlib.import_module('.'+commands[args.command],__package__).main()
if __name__=='__main__':main()

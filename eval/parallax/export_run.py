"""Export a completed run without changing its evidence files."""
import argparse,gzip,hashlib,json,shutil,zipfile
from pathlib import Path
def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    folder=Path(a.run).resolve();out=Path(a.output).resolve()
    if not (folder/'metadata.json').exists() or not (folder/'metrics.json').exists():raise ValueError('Evaluate a completed run before exporting')
    if out.exists():raise ValueError('Refusing to overwrite an export')
    if out.is_relative_to(folder):raise ValueError('Export must be outside the run directory')
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob('*')):
            if path.is_file():archive.write(path,str(path.relative_to(folder)))
    out.with_suffix('.sha256').write_text(hashlib.sha256(out.read_bytes()).hexdigest()+'  '+out.name+'\n')
    print(out)
if __name__=='__main__':main()

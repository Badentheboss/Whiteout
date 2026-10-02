"""Portable release packaging with content hashes and model artifacts."""
import hashlib,json,zipfile
from .config import ROOT
def main():
    source=ROOT/'extension/dist';manifest=json.loads((source/'manifest.json').read_text())
    output=ROOT/'store'/('parallax-'+manifest['version']+'.zip')
    if output.exists():raise SystemExit('Release already exists; choose a new version instead of overwriting it.')
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob('*')):
            if path.is_file():archive.write(path,str(path.relative_to(source)))
    output.with_suffix('.sha256').write_text(hashlib.sha256(output.read_bytes()).hexdigest()+'  '+output.name+'\n')
    print(output)
if __name__=='__main__':main()

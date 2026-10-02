"""Read-only dependency checks with actionable Windows guidance."""
import importlib.util,platform,shutil,ssl,sys
from .config import ROOT
def main():
    print('Python:',sys.executable,sys.version.split()[0]);print('OS:',platform.platform())
    for package in ['playwright','pandas','streamlit','sklearn','bs4','skimage']:
        print(package,'OK' if importlib.util.find_spec(package) else 'MISSING: install eval/requirements.txt')
    for command in ['node','npm']:print(command,shutil.which(command) or 'MISSING: install Node.js LTS, then reopen Command Prompt')
    print('Manifest:',(ROOT/'extension/dist/manifest.json').exists())
    print('TLS defaults:',ssl.get_default_verify_paths())
    print('Never disable TLS verification. On a managed PC ask IT for its trusted CA certificate and installation/download policy.')
    try:
        from playwright.sync_api import sync_playwright
        from pathlib import Path
        with sync_playwright() as p:print('Bundled Chromium:',p.chromium.executable_path,'exists:',Path(p.chromium.executable_path).exists())
    except Exception as error:print('Browser diagnostic:',error)
if __name__=='__main__':main()

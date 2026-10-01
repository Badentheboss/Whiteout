from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data'
RUNS = DATA / 'runs'
FIXTURES = DATA / 'fixtures'
SEED = 20261001
DETECTOR_CONFIG = {'contrast_ratio': 1.35, 'min_font_px': 2, 'classifier_cutoff': .42, 'payload_token_overlap': .60}

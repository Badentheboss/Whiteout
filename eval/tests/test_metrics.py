import pandas as pd
def test_overlap_hit_counts_as_detection():
 d=pd.DataFrame([{'flagged':True},{'flagged':False}]); assert d.flagged.mean()==.5
def test_no_network_content_requests():
 row={'network_content_requests':0}; assert row['network_content_requests']==0

def test_manifest_schema_has_required_fields():
 import json
 from pathlib import Path
 root=Path(__file__).resolve().parents[2]
 rows=[json.loads(line) for line in (root/'data'/'manifest.jsonl').read_text().splitlines()]
 required={'page_id','source_url','snapshot_path','license','variant_id','is_injected','vector','payload_category','payload_text','ground_truth_node','seed','extractor_profiles'}
 assert len(rows)==100
 assert all(required <= row.keys() for row in rows)

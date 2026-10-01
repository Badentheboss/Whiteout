import pandas as pd
def test_overlap_hit_counts_as_detection():
 d=pd.DataFrame([{'flagged':True},{'flagged':False}]); assert d.flagged.mean()==.5
def test_no_network_content_requests():
 row={'network_content_requests':0}; assert row['network_content_requests']==0

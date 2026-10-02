import json
import pytest
from parallax.review import append_review, node_metrics, prepare_negatives, prepare_sources
from parallax.ratings import inter_rater
from parallax.freeze import capture, check, digest, safe_path
from parallax.corpus_audit import near_duplicates
from parallax.extractors import exposure, equality
from parallax.run import profile_result
from parallax.artifacts import artifact_path
from parallax.source_registry import reviewed_sources
from parallax.payloads_v3 import FAMILIES,render,expected


def test_review_requires_explicit_judgments(tmp_path):
    path=tmp_path/'ratings.jsonl'
    with pytest.raises(ValueError):append_review(path,{'rater':'a','instruction':None},['instruction'])
    assert not path.exists()
    row=append_review(path,{'rater':'a','instruction':False},['instruction'])
    assert row['label_origin']=='human' and row['reviewed_at']


def test_partial_node_labels_and_conflicts():
    candidates=[{'id':x} for x in 'abcd'];findings=[{'id':x} for x in 'abd']
    labels=[{'rater':'one','candidate_id':x,'instruction':truth,'human_visible':False} for x,truth in [('a',True),('b',False),('c',True)]]
    result=node_metrics(candidates,findings,labels)
    assert (result['tp'],result['fp'],result['fn'],result['f1'])==(1,1,1,.5)
    assert result['reviewed']==3  # d is not silently a false positive
    labels.append({'rater':'two','candidate_id':'a','instruction':False,'human_visible':False})
    result=node_metrics(candidates,findings,labels)
    assert result['conflicts']==1 and result['reviewed']==2


def test_inter_rater_agreement_uses_overlapping_latest_votes():
    rows=[{'rater':r,'variant_id':'v','candidate_id':str(i),'instruction':bool(i),'human_visible':not bool(i)} for r in ['a','b'] for i in [0,1]]
    result=inter_rater(rows)
    assert all(p['kappa']==1 and p['shared_items']==2 for p in result['pairs'])
    assert not inter_rater(rows[:2])['pairs']


def test_pending_forms_exclude_test_negatives():
    rows=[{'id':str(i),'source_group':str(i%2),'split':split,'label':0} for i,split in enumerate(['train','validation','test'])]
    forms=prepare_negatives(rows,300)
    assert len(forms)==2 and all(r['instruction'] is None for r in forms)
    forms=prepare_sources([{'page_id':'a'},{'page_id':'a'}])
    assert len(forms)==1 and forms[0]['terms_checked'] is None


def test_near_duplicate_cross_split_detection():
    text='one two three four five six seven eight nine ten'
    result=near_duplicates([{'page_id':'a','split':'train','text':text},{'page_id':'b','split':'test','text':text}])
    assert result[0]['jaccard']==1 and result[0]['cross_split']
    assert not near_duplicates([{'page_id':'a','split':'train','text':text},{'page_id':'b','split':'test','text':'entirely different words here to compare against the original source'}])


def test_missing_extraction_is_not_negative():
    candidate={'text':'same','frame':'top','path':'p'}
    assert exposure(candidate,{'inner-text':'same'},'inner-text')[0] is True
    assert exposure({**candidate,'frame':'top/frame'},{'inner-text':'same'},'inner-text')[0] is None
    assert equality(None,None) is None
    extraction={'accessibility-tree':None,'unavailable':{'accessibility-tree':'denied'}}
    row=profile_result({'canary':'CANARY-A','is_injected':True},extraction,extraction,'accessibility-tree')
    assert row['canary_success_on'] is None and row['unavailable_before']=='denied'


def test_lock_changes_and_path_traversal(tmp_path):
    ext=tmp_path/'extension/dist';ext.mkdir(parents=True);(ext/'manifest.json').write_text('{}')
    code=tmp_path/'eval/parallax';code.mkdir(parents=True);(code/'engine.py').write_text('# initial')
    replay=tmp_path/'page.html';replay.write_text('<p>hello</p>')
    row=dict(schema_version=2,source_group='a',page_id='a',content_hash='abc',split='train',license='CC0',source_url='urn:a',snapshot_path='page.html',variant_id='a',is_injected=False,variant_sha256=digest(replay))
    manifest=tmp_path/'manifest.jsonl';manifest.write_text(json.dumps(row)+'\n')
    lock=capture(tmp_path,manifest);assert not check(tmp_path,lock)
    replay.write_text('changed');assert 'page.html' in check(tmp_path,lock)
    (ext/'extra.js').write_text('extra');assert 'extension/dist/extra.js' in check(tmp_path,lock)
    with pytest.raises(ValueError):safe_path(tmp_path,'../escape')
    with pytest.raises(ValueError):artifact_path(tmp_path,'../escape')


def test_source_registry_rejects_pending_approval():
    row=dict(source_group='article-project',category='article',source_url='https://example.invalid/page',license_url='https://example.invalid/license',terms_url='https://example.invalid/terms',terms_checked=True,page_license_checked=True,asset_licenses_checked=True,reviewer='reviewer',reviewed_at='2026-10-02',license='CC0',review_notes='Fixture approval only')
    assert reviewed_sources([row])==[row]
    with pytest.raises(ValueError,match='Pending'):reviewed_sources([{**row,'terms_checked':None}])
    with pytest.raises(ValueError,match='duplicate'):reviewed_sources([row,row])


def test_expanded_families_are_split_disjoint_and_vary_wording():
    seen=set()
    for category in FAMILIES:
        for split in ['train','validation','test']:
            family,text=render(category,split,0,'CANARY-RANDOM')
            assert family not in seen;seen.add(family)
            variations=[render(category,split,i,'CANARY-RANDOM')[1] for i in range(3)]
            assert len(set(variations))==3 and all('CANARY-RANDOM' in t for t in variations)
            assert expected(family,0,'CANARY-RANDOM',split)==(category,text)
            wrong='test' if split!='test' else 'train'
            with pytest.raises(ValueError,match='different split'):expected(family,0,'CANARY-RANDOM',wrong)
    assert len(seen)==18

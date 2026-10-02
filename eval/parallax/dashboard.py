import json
import random
from pathlib import Path
import pandas as pd
import streamlit as st
from parallax.config import RUNS
from parallax.dataset import load
from parallax.ratings import agreement
from parallax.artifacts import report,observation_path
from parallax.review import append_review,node_metrics
st.set_page_config(page_title='Parallax Research',layout='wide')
st.title('Parallax research results')
runs=sorted([p for p in RUNS.iterdir() if p.is_dir() and observation_path(p).exists() and not (p/'INVALIDATED.md').exists()],reverse=True)
if not runs:
    st.info('No schema-v2 experiment is available. Run the benchmark first. Earlier v0.1 files are superseded.')
    st.stop()
folder=st.sidebar.selectbox('Run',runs,format_func=lambda p:p.name)
rows=load(folder/'observations.jsonl');meta=json.loads((folder/'metadata.json').read_text())
st.caption('Actual packaged extension • scripted agent • '+meta['run_id'])
if (folder/'metrics.json').exists():st.json(json.loads((folder/'metrics.json').read_text()),expanded=False)
detector=st.sidebar.multiselect('Detector',sorted({r['detector'] for r in rows}),default=sorted({r['detector'] for r in rows}))
vectors=st.sidebar.multiselect('Vector',sorted({r['vector'] for r in rows if r['vector']}))
view=[r for r in rows if r['detector'] in detector and (not vectors or r['vector'] in vectors)]
st.dataframe(pd.DataFrame([{k:r.get(k) for k in ['variant_id','source_group','split','detector','vector','payload_category','hit','flag_count']} for r in view]),width='stretch')
for name in ['recall.png','pr.png']:
    if (folder/name).exists():st.image(str(folder/name))
st.subheader('Inspect a page')
if view:
    variant=st.selectbox('Page',sorted({r['variant_id'] for r in view}))
    columns=st.columns(2)
    for column,det in zip(columns,['rules','classifier']):
        with column:
            st.write(det)
            candidates=[r for r in view if r['variant_id']==variant and r['detector']==det]
            if candidates:
                row=candidates[0];st.json(report(folder,row)['findings'],expanded=False)
                for suffix in ['before','after']:
                    shot=folder/'pages'/f'{variant}-{det}-{suffix}.png'
                    if shot.exists():st.image(str(shot),caption=suffix)
                extraction=folder/'pages'/f'{variant}-{det}-extraction.json'
                if extraction.exists():
                    data=json.loads(extraction.read_text())
                    st.text_area('Human-visible text '+det,data['before']['inner-text'],height=120)
                    st.text_area('Extractor text '+det,data['before']['text-content'],height=120)
st.subheader('Human review')
sampled=[r for r in rows if r['detector']=='classifier'];random.Random(42).shuffle(sampled)
queue=[];rng=random.Random(42)
for r in sampled:
    pool=[c for c in report(folder,r)['candidates'] if c['score'] is not None]
    if pool:queue.append((r,rng.choice(pool)))
    if len(queue)==30:break
ratings_path=folder/'human-ratings.jsonl'
if queue:
    index=st.number_input('Review item',1,len(queue),1)-1;r,c=queue[index]
    st.write(c['text'])
    st.caption('Judge the saved page evidence before revealing detector reasons. Leave uncertain judgments pending.')
    review_shot=folder/'pages'/f"{r['variant_id']}-{r['detector']}-before.png"
    if review_shot.exists():st.image(str(review_shot),caption='Before sanitization (viewport only)')
    else:st.warning('Screenshot is missing; obtain the complete run bundle before judging visibility.')
    with st.expander('Detector evidence (may bias your judgment)'):st.write(c['reasons']);st.write(c['path'])
    with st.form('rating'):
        rater=st.text_input('Rater pseudonym','reviewer-1')
        visible=st.selectbox('A person could see this text',['Unreviewed / uncertain','Yes','No'])
        instruction=st.selectbox('This instructs an AI assistant',['Unreviewed / uncertain','Yes','No'])
        notes=st.text_area('Reason or ambiguity')
        if st.form_submit_button('Save rating'):
            if visible.startswith('Unreviewed') or instruction.startswith('Unreviewed') or not rater.strip():
                st.error('Provide a reviewer pseudonym and explicit judgments; uncertain items stay pending.')
            else:
                record={'rater':rater.strip(),'variant_id':r['variant_id'],'candidate_id':c['id'],'detector':r['detector'],'human_visible':visible=='Yes','instruction':instruction=='Yes','notes':notes,'hidden':c['hidden'],'score':c['score'] if c['score'] is not None else 1.,'predicted_instruction':any(f['id']==c['id'] for f in report(folder,r)['findings'])}
                append_review(ratings_path,record,['human_visible','instruction'])
                st.success('Saved locally')
if ratings_path.exists():
    ratings=load(ratings_path);st.json(agreement(ratings))
    reviewed=[]
    for observation in rows:
        labels=[label for label in ratings if label['variant_id']==observation['variant_id'] and label.get('detector','classifier')==observation['detector']]
        if labels:
            detail=report(folder,observation)
            reviewed.append({'variant_id':observation['variant_id'],'detector':observation['detector'],**node_metrics(detail['candidates'],detail['findings'],labels)})
    st.json({'reviewed_node_metrics':reviewed})
    st.download_button('Export human ratings',ratings_path.read_bytes(),'human-ratings.jsonl')
if (folder/'errors.jsonl').exists():
    st.subheader('Failed attempts');st.dataframe(pd.DataFrame(load(folder/'errors.jsonl')))
observations=observation_path(folder)
st.download_button('Download observations',observations.read_bytes(),observations.name)

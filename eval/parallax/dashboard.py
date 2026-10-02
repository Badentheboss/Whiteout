import json
import random
from pathlib import Path
import pandas as pd
import streamlit as st
from parallax.config import RUNS
from parallax.dataset import load
from parallax.ratings import agreement
from parallax.artifacts import report,observation_path
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
st.dataframe(pd.DataFrame([{k:r.get(k) for k in ['variant_id','source_group','split','detector','vector','payload_category','hit','flag_count']} for r in view]),use_container_width=True)
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
    st.write(c['text']);st.write(c['reasons'])
    with st.form('rating'):
        rater=st.text_input('Rater pseudonym','reviewer-1')
        visible=st.checkbox('A person could see this text')
        instruction=st.checkbox('This instructs an AI assistant')
        if st.form_submit_button('Save rating'):
            record={'rater':rater,'variant_id':r['variant_id'],'candidate_id':c['id'],'human_visible':visible,'instruction':instruction,'hidden':c['hidden'],'score':c['score'] if c['score'] is not None else 1.,'predicted_instruction':any(f['id']==c['id'] for f in report(folder,r)['findings']),'label_origin':'human'}
            with ratings_path.open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
            st.success('Saved locally')
if ratings_path.exists():st.json(agreement(load(ratings_path)))
if (folder/'errors.jsonl').exists():
    st.subheader('Failed attempts');st.dataframe(pd.DataFrame(load(folder/'errors.jsonl')))
observations=observation_path(folder)
st.download_button('Download observations',observations.read_bytes(),observations.name)

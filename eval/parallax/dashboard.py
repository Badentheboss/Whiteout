import json
from pathlib import Path
import pandas as pd
import streamlit as st
from parallax.config import RUNS, DATA
st.set_page_config(page_title='Parallax evaluation',layout='wide'); st.title('Parallax evaluation dashboard')
results=pd.read_parquet(RUNS/'results.parquet'); st.caption('Real local five-fixture run; scripted naive-agent measurement, not a real LLM-agent result.')
detector=st.sidebar.selectbox('Detector',results.detector.unique()); view=results[results.detector==detector]; st.dataframe(view,use_container_width=True); st.bar_chart(view.set_index('vector')['latency_p50_ms']); st.subheader('Failure gallery'); st.json(json.loads((RUNS/'flags.json').read_text()))
st.subheader('Human rating tool'); st.info('Rate queued findings after importing ratings.jsonl. Agreement report supports Cohen kappa when labels exist.')

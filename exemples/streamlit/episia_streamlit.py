import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
 
# Config
st.set_page_config(
    page_title="Episia Streamlit",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Sora:wght@400;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Sora', sans-serif !important; }
  .metric-box {
    background: #070f1a;
    border: 1px solid rgba(41,151,255,0.18);
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    text-align: center;
    margin-bottom: 0.5rem;
  }
  .metric-box .val {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.9rem; font-weight: 700; color: #2997ff; line-height: 1;
  }
  .metric-box .lbl { font-size: 0.72rem; color: #5c7a96; margin-top: 0.3rem; letter-spacing: 0.06em; }
  .metric-box .sub { font-size: 0.65rem; color: #3d5a72; margin-top: 0.2rem; }
  .alert-epidemic { background:#2a0f0f; border-left:4px solid #e05c5c; padding:0.7rem 1rem; border-radius:5px; margin:0.3rem 0; font-size:0.82rem; }
  .alert-warning  { background:#2a1c0a; border-left:4px solid #f5a623; padding:0.7rem 1rem; border-radius:5px; margin:0.3rem 0; font-size:0.82rem; }
  .alert-alert    { background:#07111e; border-left:4px solid #2997ff; padding:0.7rem 1rem; border-radius:5px; margin:0.3rem 0; font-size:0.82rem; }
  .section-header { font-size:1.1rem; font-weight:700; color:#eef2f7; margin-bottom:0.5rem; border-bottom:2px solid #2997ff; padding-bottom:0.4rem; }
  .badge { display:inline-block; background:rgba(41,151,255,0.12); color:#2997ff; border:1px solid rgba(41,151,255,0.3); border-radius:4px; padding:0.15rem 0.55rem; font-family:'IBM Plex Mono',monospace; font-size:0.65rem; margin:0.1rem; }
  .stTabs [data-baseweb="tab"] { font-family:'IBM Plex Mono',monospace; font-size:0.78rem; }
  .case-intro { background:#070f1a; border:1px solid rgba(41,151,255,0.1); border-radius:8px; padding:1rem 1.25rem; margin-bottom:1.25rem; font-size:0.85rem; color:#8aa8c4; line-height:1.6; }
</style>
""", 
unsafe_allow_html=True
)

PLOTLY_DARK = dict(
    plot_bgcolor="#070f1a",
    paper_bgcolor="#03080f",
    font_color="#eef2f7",
    xaxis=dict(gridcolor="rgba(41,151,255,0.07)", linecolor="rgba(41,151,255,0.2)"),
    yaxis=dict(gridcolor="rgba(41,151,255,0.07)", linecolor="rgba(41,151,255,0.2)"),
) 

# Sidebar

with st.sidebar:
    st.markdown('<div style="font-family:IBM Plex Mono,monospace;font-size:1.1rem;font-weight:700;color:#2997ff">Epi<span style="color:#eef2f7">sia</span></div>', unsafe_allow_html=True)
    st.caption("Open-source epidemiology for Python")
    st.divider()
    
    page = st.radio("", [
    "Meningitis Outbreak  Burkina Faso",
    "Vaccine Efficacy  MenAfriVac",
    "Malaria RDT Evaluation",
    "Cholera Outbreak Response",
    "Sample Size Calculator",
    ], label_visibility="collapsed")
    
    st.divider()
    st.markdown('<div class="badge">v0.1.1</div> <div class="badge">Xcept-Health</div>', unsafe_allow_html=True)
    st.caption("[GitHub](https://github.com/Xcept-Health/episia) · MIT")
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
    
    
    
# CAS 1 : Meningitis Outbreak in Burkina Faso

if page == "Meningitis Outbreak  Burkina Faso":
    st.title("Meningitis Outbreak Surveillance with episia & Streamlit")
    st.markdown('<div class="case-intro">Real-world scenario: meningococcal meningitis in the Sahel meningitis belt. Seasonal epidemic pattern with peak during the dry season (weeks 10–20). This tool simulates the SNIS/DHIS2 weekly surveillance pipeline used by the Ministry of Health of Burkina Faso.</div>', unsafe_allow_html=True)
    
    from episia.models import SEIRModel
    from episia.models.parameters import SEIRParameters, ScenarioSet
    from episia.models.scenarios import ScenarioRunner
    from episia.data.surveillance import SurveillanceDataset, AlertEngine
    
    # Paramter
    
    col_p, col_r = st.columns([1, 2.5])
    
    with col_p:
        st.markdown('<div class="section-header">District parameters</div>', unsafe_allow_html=True)
        district   = st.selectbox("District", ["Kaya (Centre-Nord)", "Dori (Sahel)", "Ouahigouya (Nord)", "Titao (Nord)"])
        population = st.number_input("Population", value=350_000, step=10_000)
        year       = st.selectbox("Epidemic year", [2024, 2023, 2022])

        st.markdown('<div class="section-header" style="margin-top:1rem">Transmission</div>', unsafe_allow_html=True)
        beta  = st.slider("β (transmission)", 0.20, 0.70, 0.42, 0.01,
                           help="Meningococcus: typically 0.35–0.55 in dry season")
        sigma = st.slider("σ (1/incubation)", 0.15, 0.50, 0.25, 0.01,
                           help="Incubation 2–10 days → σ ≈ 0.20–0.50")
        gamma = st.slider("γ (1/infectious period)", 0.10, 0.50, 1/7, 0.01)
        vax_coverage = st.slider("Vaccine coverage (%)", 0, 100, 35,
                                  help="MenAfriVac coverage in district")

        st.markdown('<div class="section-header" style="margin-top:1rem">Alert thresholds</div>', unsafe_allow_html=True)
        thresh_abs = st.slider("Cases/week threshold", 5, 50, 15,
                                help="WHO meningitis belt: 15 cases/100k/week in district <100k pop")
        zscore_t   = st.slider("Z-score threshold", 1.0, 4.0, 2.0, 0.1)
    
    with col_r:
        # Simulate weekly surveillance data
        np.random.seed(42 + year - 2024)
        weeks = np.arange(1, 53)
        endemic   = np.random.poisson(3, 52).astype(float)
        peak_week = 15
        peak_amp  = int(population / 1000 * 0.9 * (1 - vax_coverage/100))
        epidemic  = np.exp(-0.5*((weeks - peak_week)/3.5)**2) * peak_amp
        cases     = np.clip((endemic + epidemic).astype(int), 0, None)
        dates     = pd.date_range(f"{year}-01-01", periods=52, freq="W")

        df_s = pd.DataFrame({"date": dates, "cases": cases, "district": district})
        ds   = SurveillanceDataset(df_s, date_col="date", cases_col="cases", district_col="district")
        engine = AlertEngine(ds)
        alerts = engine.run(threshold=thresh_abs, zscore_threshold=zscore_t)

        n_epidemic = sum(1 for a in alerts if a.severity == "epidemic")
        n_warning  = sum(1 for a in alerts if a.severity == "warning")
        attack_rate = cases.sum() / population * 100_000
        
        # Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-box"><div class="val">{cases.sum():,}</div><div class="lbl">Total cases</div><div class="sub">Year {year}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-box"><div class="val">{n_epidemic}</div><div class="lbl">Epidemic alerts</div><div class="sub">weeks above threshold</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-box"><div class="val">{cases.max()}</div><div class="lbl">Peak cases/week</div><div class="sub">week {int(weeks[np.argmax(cases)])}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-box"><div class="val">{attack_rate:.0f}</div><div class="lbl">Attack rate</div><div class="sub">per 100,000</div></div>', unsafe_allow_html=True)

        # Epidemic curve
        fig = go.Figure()
        fig.add_trace(go.Bar(x=dates, y=cases, name="Weekly cases",
                             marker_color="#2997ff", opacity=0.75))
        fig.add_hline(y=thresh_abs, line_dash="dash", line_color="#e05c5c",
                      annotation_text=f"Epidemic threshold ({thresh_abs}/week)",
                      annotation_font_color="#e05c5c")
        
        # Shade epidemic weeks
        for a in alerts:
            if a.severity == "epidemic" and a.period in list(dates):
                idx = list(dates).index(a.period)
                if idx < len(dates)-1:
                    fig.add_vrect(x0=dates[idx], x1=dates[min(idx+1, 51)],
                                  fillcolor="rgba(224,92,92,0.07)", layer="below",
                                  line_width=0)
        fig.update_layout(title=f"Weekly meningitis cases  {district} ({year})",
                          xaxis_title="Week", yaxis_title="Cases",
                          height=320, **PLOTLY_DARK, showlegend=False,
                          bargap=0.15)
        st.plotly_chart(fig, use_container_width=True)
        
         # SEIR model + scenarios
        st.markdown('<div class="section-header">Outbreak projection & intervention scenarios</div>', unsafe_allow_html=True)

        N_eff = int(population * (1 - vax_coverage/100))
        scenarios = ScenarioSet([
            ("No intervention",  SEIRParameters(N=population, I0=5, E0=20, beta=beta, sigma=sigma, gamma=gamma, t_span=(0,120))),
            ("Mass vaccination", SEIRParameters(N=N_eff, I0=5, E0=20, beta=beta, sigma=sigma, gamma=gamma, t_span=(0,120))),
            ("Ring vaccination", SEIRParameters(N=population, I0=5, E0=20, beta=beta*0.45, sigma=sigma, gamma=gamma, t_span=(0,120))),
            ("Combined",         SEIRParameters(N=N_eff, I0=5, E0=20, beta=beta*0.45, sigma=sigma, gamma=gamma, t_span=(0,120))),
        ])
        runner  = ScenarioRunner(SEIRModel)
        res_sc  = runner.run(scenarios)
        df_sc   = res_sc.to_dataframe()

        colors = ["#e05c5c", "#f5a623", "#2997ff", "#00c8b4"]
        fig2 = go.Figure()
        for (name, params), color in zip(scenarios, colors):
            r = SEIRModel(params).run()
            fig2.add_trace(go.Scatter(
                x=r.t, y=r.compartments["I"],
                name=name, line=dict(color=color, width=2.2),
            ))
        fig2.update_layout(title="Infected (I)  intervention scenarios",
                           xaxis_title="Days", yaxis_title="Infected",
                           height=300, hovermode="x unified",
                           **PLOTLY_DARK,
                           legend=dict(bgcolor="#070f1a", x=0.65, y=0.95))
        st.plotly_chart(fig2, use_container_width=True)
        
        
        
        # Summary table
        col_t, col_a = st.columns([2, 1])
        with col_t:
            df_display = df_sc.copy().reset_index()
            df_display.columns = ["Scenario","R₀","Peak infected","Peak day","Final size"]
            df_display["R₀"]            = df_display["R₀"].round(2)
            df_display["Peak infected"] = df_display["Peak infected"].apply(lambda x: f"{int(x):,}")
            df_display["Peak day"]      = df_display["Peak day"].round(0).astype(int)
            df_display["Final size"]    = (df_display["Final size"]*100).round(1).astype(str)+"%"
            st.dataframe(df_display.set_index("Scenario"), use_container_width=True)
        with col_a:
            st.markdown("**Top alerts**")
            for a in sorted(alerts, key=lambda x: x.severity)[:6]:
                cls = f"alert-{a.severity}"
                st.markdown(f'<div class="{cls}"><strong>{a.severity.upper()}</strong><br>{str(a.period)[:10]}<br><small>{a.message[:60]}</small></div>', unsafe_allow_html=True)


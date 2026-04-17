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
                st.markdown(
                    f'<div class="{cls}"><strong>{a.severity.upper()}</strong><br>{str(a.period)[:10]}<br><small>{a.message[:60]}</small></div>', 
                    unsafe_allow_html=True
                    )
                
  
# CASE 2 : Efficacy of the MenAfriVac vaccine 

elif page == "Vaccine Efficacy  MenAfriVac":
    st.title("Vaccine Efficacy Analysis MenAfriVac with episia & Streamlit")
    st.markdown('<div class="case-intro">MenAfriVac (PsA-TT) is the meningococcal conjugate vaccine deployed across the Sahel belt since 2010. This tool computes vaccine efficacy (VE = 1 - RR) from cohort or case-control study data, with confidence intervals validated against OpenEpi.</div>', unsafe_allow_html=True)
    
    from episia.stats.contingency import risk_ratio, odds_ratio, Table2x2
    from episia.stats.stratified import mantel_haenszel_or

    tab_cohort, tab_stratified = st.tabs(["Cohort Analysis", "Age-stratified (Mantel-Haenszel)"])

    with tab_cohort:
        col_p, col_r = st.columns([1, 2])
        with col_p:
            st.markdown('<div class="section-header">Study data</div>', unsafe_allow_html=True)
            st.markdown("**Vaccinated group**")
            a = st.number_input("Cases (vaccinated)", value=12, min_value=0, help="Meningitis cases in vaccinated group")
            b = st.number_input("Non-cases (vaccinated)", value=2988, min_value=0)
            st.markdown("**Unvaccinated group**")
            c = st.number_input("Cases (unvaccinated)", value=87, min_value=0)
            d = st.number_input("Non-cases (unvaccinated)", value=2913, min_value=0)

            study_site = st.text_input("Study site", value="Kaya District, Burkina Faso")
            study_year = st.text_input("Study period", value="2023–2024")
                

        with col_r:
            try:
                rr  = risk_ratio(a=a, b=b, c=c, d=d)
                or_ = odds_ratio(a=a, b=b, c=c, d=d)

                ve     = (1 - rr.estimate) * 100
                ve_lo  = (1 - rr.ci_upper) * 100
                ve_hi  = (1 - rr.ci_lower) * 100
                r_vacc = a / (a+b) * 1000
                r_unv  = c / (c+d) * 1000

                c1, c2, c3, c4 = st.columns(4)
                c1.markdown(f'<div class="metric-box"><div class="val">{ve:.1f}%</div><div class="lbl">Vaccine Efficacy</div><div class="sub">[{ve_lo:.1f}% – {ve_hi:.1f}%]</div></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-box"><div class="val">{rr.estimate:.3f}</div><div class="lbl">Risk Ratio</div><div class="sub">p={rr.p_value:.4f}</div></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="metric-box"><div class="val">{r_vacc:.1f}</div><div class="lbl">Risk (vaccinated)</div><div class="sub">per 1,000</div></div>', unsafe_allow_html=True)
                c4.markdown(f'<div class="metric-box"><div class="val">{r_unv:.1f}</div><div class="lbl">Risk (unvaccinated)</div><div class="sub">per 1,000</div></div>', unsafe_allow_html=True)

                # Interpretation
                if ve > 70 and rr.p_value < 0.05:
                    st.success(f"**High vaccine efficacy** ({ve:.1f}%)  statistically significant (p={rr.p_value:.4f}). The vaccine provides substantial protection against meningococcal meningitis.")
                elif ve > 50:
                    st.warning(f"Moderate vaccine efficacy ({ve:.1f}%). Consider coverage improvements.")
                elif ve < 0:
                    st.error(f"Negative VE  possible bias or low vaccine quality. Investigate cold chain.")

                # Risk comparison bar chart
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=["Vaccinated", "Unvaccinated"],
                    y=[r_vacc, r_unv],
                    marker_color=["#00c8b4", "#e05c5c"],
                    text=[f"{r_vacc:.1f}/1000", f"{r_unv:.1f}/1000"],
                    textposition="outside",
                ))
                fig.update_layout(
                    title=f"Meningitis risk comparison  {study_site} ({study_year})",
                    yaxis_title="Cases per 1,000 person-years",
                    height=320, **PLOTLY_DARK, showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)

                # VE across different studies (simulated for comparison)
                st.markdown('<div class="section-header">VE estimates regional comparison</div>', unsafe_allow_html=True)
                studies = {
                    "Mali 2011 (Djibo)":        (94.0, 88.0, 97.0),
                    "Niger 2012 (Zinder)":      (89.3, 79.4, 94.5),
                    "Burkina Faso 2012":        (87.6, 72.1, 94.3),
                    "Chad 2013":                (79.4, 63.1, 88.5),
                    f"{study_site} ({study_year})": (ve, ve_lo, ve_hi),
                }
                fig2 = go.Figure()
                for i, (name, (est, lo, hi)) in enumerate(studies.items()):
                    clr = "#2997ff" if study_site.split(",")[0] in name or study_year in name else "#8aa8c4"
                    fig2.add_trace(go.Scatter(
                        x=[lo, est, hi], y=[name]*3,
                        mode="lines+markers",
                        marker=dict(size=[9, 15, 9], color=clr),
                        line=dict(color=clr, width=2.5),
                        showlegend=False,
                    ))
                fig2.add_vline(x=0, line_dash="dash", line_color="#5c7a96", opacity=0.5)
                fig2.update_layout(
                    title="Vaccine efficacy estimates across sites (Forest plot)",
                    xaxis_title="Vaccine Efficacy (%)",
                    xaxis=dict(range=[-20, 105]),
                    height=300, **PLOTLY_DARK,
                )
                st.plotly_chart(fig2, use_container_width=True)

            except Exception as e:
                st.error(f"Error: {e}")
                
    with tab_stratified:
        st.markdown("Mantel-Haenszel pooled estimate controlling for age group.")
        col_p, col_r = st.columns([1, 2])
        
        with col_p:
            st.markdown('<div class="section-header">Data by age group</div>', unsafe_allow_html=True)
            st.markdown("**Children < 5 years**")
            a1,b1,c1_v,d1 = (st.number_input(f"a1",value=4,key="a1"),st.number_input("b1",value=896,key="b1"),
                              st.number_input("c1",value=31,key="c1"),st.number_input("d1",value=869,key="d1"))
            st.markdown("**Children 5–14 years**")
            a2,b2,c2_v,d2 = (st.number_input("a2",value=5,key="a2"),st.number_input("b2",value=1145,key="b2"),
                              st.number_input("c2",value=38,key="c2"),st.number_input("d2",value=1112,key="d2"))
            st.markdown("**Adults 15+ years**")
            a3,b3,c3_v,d3 = (st.number_input("a3",value=3,key="a3"),st.number_input("b3",value=947,key="b3"),
                              st.number_input("c3",value=18,key="c3"),st.number_input("d3",value=932,key="d3"))
            
        with col_r:
            from episia.stats.contingency import Table2x2
            from episia.stats.stratified import mantel_haenszel_or
            strata = [Table2x2(a1,b1,c1_v,d1), Table2x2(a2,b2,c2_v,d2), Table2x2(a3,b3,c3_v,d3)]
            mh = mantel_haenszel_or(strata)
            pooled_ve = (1 - mh.common_or) * 100
            lo_or, hi_or = mh.or_ci
            pooled_ve_lo = (1 - hi_or) * 100
            pooled_ve_hi = (1 - lo_or) * 100

            c1x, c2x, c3x = st.columns(3)
            c1x.metric("Pooled OR (MH)", f"{mh.common_or:.3f}", f"[{lo_or:.3f} – {hi_or:.3f}]")
            c2x.metric("Pooled VE", f"{pooled_ve:.1f}%", f"[{pooled_ve_lo:.1f}% – {pooled_ve_hi:.1f}%]")
            c3x.metric("p heterogeneity", f"{mh.q_p_value:.3f}", "Cochran Q")

            age_labels = ["< 5 years", "5–14 years", "15+ years"]
            ages_or  = [Table2x2(a1,b1,c1_v,d1).odds_ratio(), Table2x2(a2,b2,c2_v,d2).odds_ratio(), Table2x2(a3,b3,c3_v,d3).odds_ratio()]
            fig = go.Figure()
            for i, (lbl, or_res) in enumerate(zip(age_labels, ages_or)):
                fig.add_trace(go.Scatter(
                    x=[or_res.ci_lower, or_res.estimate, or_res.ci_upper],
                    y=[lbl]*3, mode="lines+markers",
                    marker=dict(size=[9,14,9], color="#2997ff"),
                    line=dict(color="#2997ff", width=2), showlegend=False,
                ))
            fig.add_trace(go.Scatter(
                x=[lo_or, mh.common_or, hi_or],
                y=["Pooled (MH)"]*3, mode="lines+markers",
                marker=dict(size=[10,18,10], symbol=["line-ew","diamond","line-ew"], color="#00c8b4"),
                line=dict(color="#00c8b4", width=3), showlegend=False,
            ))
            fig.add_vline(x=1, line_dash="dash", line_color="#5c7a96")
            fig.update_layout(
                title="Stratified OR by age group  Forest plot",
                xaxis_title="Odds Ratio (log scale)", xaxis_type="log",
                height=280, **PLOTLY_DARK,
            )
            st.plotly_chart(fig, use_container_width=True)
            

# CASE 3 : Malaria RDT Evaluation

elif page == "Malaria RDT Evaluation":
    st.title("Malaria RDT Performance Evaluation with episia & Streamlit")
    st.markdown('<div class="case-intro">Rapid Diagnostic Tests (RDTs) are the frontline tool for malaria diagnosis in low-resource settings. This analysis evaluates RDT performance against gold-standard microscopy and computes clinical utility (PPV/NPV) at different prevalence levels  critical for district-level decision making in Burkina Faso.</div>', unsafe_allow_html=True)
    
    from episia.stats.diagnostic import (
        diagnostic_test_2x2,
        predictive_values_from_sens_spec
    )
    
    col_p, col_r = st.columns([1, 2.2])
    
    with col_p:
        st.markdown('<div class="section-header">RDT validation data</div>', unsafe_allow_html=True)
        st.markdown("*(vs. expert microscopy)*")
        tp = st.number_input("True Positives",  value=142, min_value=0,
                              help="RDT+ and Microscopy+")
        fp = st.number_input("False Positives", value=18, min_value=0,
                              help="RDT+ but Microscopy-")
        fn = st.number_input("False Negatives", value=23, min_value=0,
                              help="RDT- but Microscopy+")
        tn = st.number_input("True Negatives",  value=317, min_value=0,
                              help="RDT- and Microscopy-")

        rdt_name = st.text_input("RDT name", value="CareStart HRP2/pLDH")
        site     = st.text_input("Site", value="CHR Koudougou, Burkina Faso")

        st.markdown('<div class="section-header" style="margin-top:1rem">Clinical context</div>', unsafe_allow_html=True)
        prev_range = st.slider("Prevalence range to explore (%)", 1, 80, (5, 40))
        n_patients = st.number_input("Daily patient volume", value=120, min_value=10)
        
    with col_r:
        try:
            d = diagnostic_test_2x2(tp=tp, fp=fp, fn=fn, tn=tn)

            c1,c2,c3,c4 = st.columns(4)
            c1.markdown(f'<div class="metric-box"><div class="val">{d.sensitivity*100:.1f}%</div><div class="lbl">Sensitivity</div><div class="sub">True positive rate</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-box"><div class="val">{d.specificity*100:.1f}%</div><div class="lbl">Specificity</div><div class="sub">True negative rate</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-box"><div class="val">{d.lr_positive:.1f}</div><div class="lbl">LR+</div><div class="sub">Likelihood ratio</div></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="metric-box"><div class="val">{d.lr_negative:.3f}</div><div class="lbl">LR-</div><div class="sub">Likelihood ratio</div></div>', unsafe_allow_html=True)

            # PPV/NPV across prevalence range
            prevs  = np.linspace(prev_range[0]/100, prev_range[1]/100, 60)
            ppvs, npvs = [], []
            for p in prevs:
                ppv, npv = predictive_values_from_sens_spec(d.sensitivity, d.specificity, p)
                ppvs.append(ppv*100); npvs.append(npv*100)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=prevs*100, y=ppvs, name="PPV", line=dict(color="#2997ff",width=2.5)))
            fig.add_trace(go.Scatter(x=prevs*100, y=npvs, name="NPV", line=dict(color="#00c8b4",width=2.5)))
            fig.add_hline(y=90, line_dash="dot", line_color="#5c7a96", opacity=0.5, annotation_text="90%")
            fig.update_layout(
                title=f"PPV & NPV across prevalence  {rdt_name}",
                xaxis_title="True prevalence (%)",
                yaxis_title="Predictive value (%)",
                yaxis=dict(range=[0,105]),
                height=300, hovermode="x unified",
                **PLOTLY_DARK,
                legend=dict(bgcolor="#070f1a"),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Operational impact
            st.markdown('<div class="section-header">Operational impact at your site</div>', unsafe_allow_html=True)
            for prev_pct in [10, 20, 35]:
                prev_f = prev_pct / 100
                ppv_v, npv_v = predictive_values_from_sens_spec(d.sensitivity, d.specificity, prev_f)
                expected_pos = int(n_patients * prev_f)
                false_neg    = int(expected_pos * (1-d.sensitivity))
                false_pos    = int((n_patients - expected_pos) * (1-d.specificity))
                st.markdown(f"""
                **Prevalence {prev_pct}%** | {expected_pos} expected cases/day
                 PPV {ppv_v*100:.0f}% · NPV {npv_v*100:.0f}%
                 ~{false_neg} missed cases · ~{false_pos} false alarms
                """)

            # Radar
            cats = ["Sensitivity","Specificity","PPV @ 20%","NPV @ 20%","Accuracy"]
            ppv20, npv20 = predictive_values_from_sens_spec(d.sensitivity, d.specificity, 0.20)
            acc = (tp+tn)/(tp+fp+fn+tn)*100
            vals = [d.sensitivity*100, d.specificity*100, ppv20*100, npv20*100, acc]
            fig2 = go.Figure(go.Scatterpolar(
                r=vals+[vals[0]], theta=cats+[cats[0]],
                fill="toself", fillcolor="rgba(41,151,255,0.12)",
                line=dict(color="#2997ff",width=2),
                name=rdt_name,
            ))
            fig2.update_layout(
                polar=dict(radialaxis=dict(range=[0,100]), bgcolor="#070f1a"),
                plot_bgcolor="#03080f", paper_bgcolor="#03080f", font_color="#eef2f7",
                title=f"Diagnostic profile  {rdt_name} · {site}",
                height=340,
            )
            st.plotly_chart(fig2, use_container_width=True)

        except Exception as e:
            st.error(f"Error: {e}")
            
# CASE 4 : Cholera Outbreak Response
        
elif page == "Cholera Outbreak Response":
    st.title("Cholera Outbreak Response Simulation with episia & Streamlit")
    st.markdown('<div class="case-intro">Cholera remains a major public health threat in West Africa. This tool uses a SEIRD model to simulate the epidemic trajectory and project the impact of WASH interventions (water, sanitation, hygiene) and oral cholera vaccine (OCV) deployment on case fatalities.</div>', unsafe_allow_html=True)

    from episia.models import SEIRDModel
    from episia.models.parameters import SEIRDParameters, ScenarioSet
    from episia.models.scenarios import ScenarioRunner

    col_p, col_r = st.columns([1, 2.3])

    with col_p:
        st.markdown('<div class="section-header">Outbreak settings</div>', unsafe_allow_html=True)
        location = st.selectbox("Location", ["Niamey (Niger)", "Ndjamena (Chad)", "Tahoua (Niger)", "Maradi (Niger)"])
        N     = st.number_input("At-risk population", value=180_000, step=10_000)
        I0    = st.number_input("Initial cases", value=12, min_value=1)
        E0    = st.number_input("Initial exposed", value=40, min_value=0)
        t_end = st.slider("Simulation (days)", 30, 180, 90)

        st.markdown('<div class="section-header" style="margin-top:1rem">Disease parameters</div>', unsafe_allow_html=True)
        beta  = st.slider("β (transmission)", 0.10, 1.0, 0.55, 0.01,
                           help="Cholera: high in poor WASH settings (0.4–0.8)")
        sigma = st.slider("σ (1/incubation)", 0.3, 2.0, 0.5, 0.05,
                           help="Incubation 0.5–5 days")
        gamma = st.slider("γ (1/infectious period)", 0.1, 0.5, 0.25, 0.01)
        mu    = st.slider("μ (case fatality rate)", 0.001, 0.05, 0.015, 0.001,
                           help="CFR 0.2–5% with treatment, up to 50% untreated")

        st.markdown('<div class="section-header" style="margin-top:1rem">Interventions</div>', unsafe_allow_html=True)
        wash_eff = st.slider("WASH effectiveness (%)", 0, 80, 40,
                              help="β reduction from water/sanitation")
        ocv_cov  = st.slider("OCV coverage (%)", 0, 90, 50,
                              help="Oral cholera vaccine  2-dose regimen")
        ocv_eff  = st.slider("OCV efficacy (%)", 50, 90, 76,
                              help="76% protective efficacy in outbreaks")

    with col_r:
        try:
            wash_b = beta * (1 - wash_eff/100)
            ocv_N  = int(N * (1 - ocv_cov/100 * ocv_eff/100))

            scenarios = ScenarioSet([
                ("No intervention",     SEIRDParameters(N=N, I0=I0, E0=E0, beta=beta, sigma=sigma, gamma=gamma, mu=mu, t_span=(0,t_end))),
                ("WASH only",           SEIRDParameters(N=N, I0=I0, E0=E0, beta=wash_b, sigma=sigma, gamma=gamma, mu=mu*0.6, t_span=(0,t_end))),
                ("OCV only",            SEIRDParameters(N=ocv_N, I0=I0, E0=E0, beta=beta, sigma=sigma, gamma=gamma, mu=mu, t_span=(0,t_end))),
                ("WASH + OCV",          SEIRDParameters(N=ocv_N, I0=I0, E0=E0, beta=wash_b, sigma=sigma, gamma=gamma, mu=mu*0.6, t_span=(0,t_end))),
            ])

            runner = ScenarioRunner(SEIRDModel)
            res    = runner.run(scenarios)
            df_sc  = res.to_dataframe()

            colors = ["#e05c5c","#f5a623","#2997ff","#00c8b4"]
            fig = go.Figure()
            for (name, params), color in zip(scenarios, colors):
                r = SEIRDModel(params).run()
                deaths = r.compartments.get("D", [0])[-1]
                fig.add_trace(go.Scatter(
                    x=r.t, y=r.compartments["I"],
                    name=f"{name} ({int(deaths):,} deaths)",
                    line=dict(color=color, width=2.2),
                ))
            fig.update_layout(
                title=f"Cholera cases over time  {location}",
                xaxis_title="Days", yaxis_title="Active cases",
                height=340, hovermode="x unified",
                **PLOTLY_DARK,
                legend=dict(bgcolor="#070f1a", font_size=11),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Deaths comparison
            deaths_by_scenario = {}
            for name, params in scenarios:
                r = SEIRDModel(params).run()
                deaths_by_scenario[name] = int(r.compartments.get("D",[0])[-1])

            fig2 = go.Figure(go.Bar(
                x=list(deaths_by_scenario.keys()),
                y=list(deaths_by_scenario.values()),
                marker_color=colors,
                text=[f"{v:,}" for v in deaths_by_scenario.values()],
                textposition="outside",
            ))
            baseline_d = deaths_by_scenario["No intervention"]
            combined_d = deaths_by_scenario["WASH + OCV"]
            lives_saved = baseline_d - combined_d

            fig2.update_layout(
                title=f"Projected deaths by scenario  {lives_saved:,} lives saved with combined intervention",
                yaxis_title="Deaths",
                height=300, **PLOTLY_DARK, showlegend=False,
            )
            st.plotly_chart(fig2, use_container_width=True)

            # Key message
            pct_reduction = (1 - combined_d/baseline_d)*100 if baseline_d > 0 else 0
            st.success(f"Combined WASH + OCV reduces mortality by **{pct_reduction:.0f}%**  saving an estimated **{lives_saved:,} lives** in {location} over {t_end} days.")

        except Exception as e:
            st.error(f"Error: {e}")


import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

#  Page config 
st.set_page_config(
    page_title="Episia · Epidemiology for Africa",
    layout="wide",
    initial_sidebar_state="expanded",
)

#  Pages list (shared) 
PAGES = [
    "Home",
    "Disease Burden Globe",
    "Meningitis · Burkina Faso",
    "Vaccine Efficacy · MenAfriVac",
    "Malaria RDT Evaluation",
    "Cholera Outbreak Response",
    "HIV Treatment Cascade",
    "Child Malnutrition · MUAC",
    "Sample Size Calculator",
]

# Country → dedicated page mapping
COUNTRY_PAGES = {
    "Burkina Faso": "Meningitis · Burkina Faso",
}

#  Session state 
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "page_idx" not in st.session_state:
    st.session_state.page_idx = 0

T = st.session_state.theme

#  Theme tokens 
if T == "dark":
    BG0        = "#020912"
    BG1        = "#060e1b"
    BG2        = "#0a1628"
    CARD_BG    = "#0d1c35"
    BORDER     = "rgba(41,151,255,0.14)"
    BORDER_H   = "rgba(41,151,255,0.40)"
    T_PRI      = "#e8f0f9"
    T_SEC      = "#7a9dc0"
    T_MUT      = "#3d5e7d"
    ACC        = "#2997ff"
    ACC2       = "#00c8b4"
    ACC3       = "#e05c5c"
    ACC4       = "#f5a623"
    PLT_BG     = "#060e1b"
    PLT_PAPER  = "#020912"
    PLT_GRID   = "rgba(41,151,255,0.06)"
    PLT_LINE   = "rgba(41,151,255,0.18)"
    PLT_FONT   = "#e8f0f9"
    SIDEBAR_BG = "#030b17"
    INPUT_BG   = "#0a1628"
    SUCCESS_BG = "#051e14"
    SUCCESS_BD = "#00c8b4"
    INFO_BG    = "#051020"
    INFO_BD    = "#2997ff"
    WARN_BG    = "#1e1200"
    WARN_BD    = "#f5a623"
    ERR_BG     = "#1e0505"
    ERR_BD     = "#e05c5c"
    BTN_BG     = "#0d1c35"
    BTN_HOVER  = "#0a2550"
    NAV_ACTIVE = "rgba(41,151,255,0.15)"
else:
    BG0        = "#f0f4fa"
    BG1        = "#f8fafd"
    BG2        = "#ffffff"
    CARD_BG    = "#ffffff"
    BORDER     = "rgba(15,80,180,0.15)"
    BORDER_H   = "rgba(15,80,180,0.40)"
    T_PRI      = "#0d1f33"
    T_SEC      = "#2a4a6e"
    T_MUT      = "#6a8aaa"
    ACC        = "#0a6fd8"
    ACC2       = "#008f80"
    ACC3       = "#c0392b"
    ACC4       = "#b06800"
    PLT_BG     = "#ffffff"
    PLT_PAPER  = "#f0f4fa"
    PLT_GRID   = "rgba(15,80,180,0.07)"
    PLT_LINE   = "rgba(15,80,180,0.18)"
    PLT_FONT   = "#0d1f33"
    SIDEBAR_BG = "#e6edf7"
    INPUT_BG   = "#f0f4fa"
    SUCCESS_BG = "#e0f5f0"
    SUCCESS_BD = "#008f80"
    INFO_BG    = "#e0eeff"
    INFO_BD    = "#0a6fd8"
    WARN_BG    = "#fff4e0"
    WARN_BD    = "#b06800"
    ERR_BG     = "#ffecec"
    ERR_BD     = "#c0392b"
    BTN_BG     = "#e8f0fa"
    BTN_HOVER  = "#d0e0f5"
    NAV_ACTIVE = "rgba(10,111,216,0.12)"

PLOTLY_THEME = dict(
    plot_bgcolor=PLT_BG,
    paper_bgcolor=PLT_PAPER,
    font=dict(color=PLT_FONT, family="IBM Plex Mono, monospace", size=11),
    xaxis=dict(gridcolor=PLT_GRID, linecolor=PLT_LINE, zerolinecolor=PLT_GRID),
    yaxis=dict(gridcolor=PLT_GRID, linecolor=PLT_LINE, zerolinecolor=PLT_GRID),
    margin=dict(l=48, r=20, t=48, b=36),
)

#  Global CSS 
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=Sora:wght@300;400;500;600;700&family=Playfair+Display:wght@400;600&display=swap');

:root {{
  --bg0: {BG0}; --bg1: {BG1}; --bg2: {BG2};
  --card: {CARD_BG}; --border: {BORDER}; --border-h: {BORDER_H};
  --t-pri: {T_PRI}; --t-sec: {T_SEC}; --t-mut: {T_MUT};
  --acc: {ACC}; --acc2: {ACC2}; --acc3: {ACC3}; --acc4: {ACC4};
  --sidebar: {SIDEBAR_BG}; --input: {INPUT_BG};
  --btn-bg: {BTN_BG}; --btn-hover: {BTN_HOVER};
  --nav-active: {NAV_ACTIVE};
}}

html, body, [class*="css"], .stApp {{
  font-family: 'Sora', sans-serif !important;
  background-color: var(--bg0) !important;
  color: var(--t-pri) !important;
}}

/*  Sidebar  */
section[data-testid="stSidebar"] {{
  background-color: var(--sidebar) !important;
  border-right: 1px solid var(--border) !important;
}}
section[data-testid="stSidebar"] * {{
  color: var(--t-pri) !important;
}}
section[data-testid="stSidebar"] .stRadio label {{
  color: var(--t-sec) !important;
  font-size: .74rem !important;
}}
section[data-testid="stSidebar"] .stRadio [data-checked="true"] label {{
  color: var(--acc) !important;
  font-weight: 600 !important;
}}
section[data-testid="stSidebar"] [data-baseweb="radio"] {{
  background: transparent !important;
}}

/*  Inputs  */
.stTextInput > div > div,
.stNumberInput > div > div,
.stSelectbox > div > div {{
  background-color: var(--input) !important;
  border-color: var(--border) !important;
  color: var(--t-pri) !important;
}}
.stTextInput input, .stNumberInput input {{
  color: var(--t-pri) !important;
  background-color: var(--input) !important;
}}
.stSelectbox div[data-baseweb="select"] span {{
  color: var(--t-pri) !important;
}}
.stSlider > div > div > div > div {{
  background: var(--acc) !important;
}}
.stSlider [data-testid="stTickBarMin"],
.stSlider [data-testid="stTickBarMax"] {{
  color: var(--t-mut) !important;
}}
label[data-testid="stWidgetLabel"] {{
  color: var(--t-sec) !important;
}}

/*  Buttons  */
.stButton > button {{
  background-color: var(--btn-bg) !important;
  color: var(--acc) !important;
  border: 1px solid var(--border) !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: .72rem !important;
  transition: background .2s, border-color .2s !important;
}}
.stButton > button:hover {{
  background-color: var(--btn-hover) !important;
  border-color: var(--acc) !important;
}}

/*  Tabs  */
.stTabs [data-baseweb="tab-list"] {{
  background-color: var(--bg1) !important;
  border-bottom: 1px solid var(--border) !important;
}}
.stTabs [data-baseweb="tab"] {{
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: .72rem !important;
  letter-spacing: .04em !important;
  color: var(--t-sec) !important;
  background-color: transparent !important;
}}
.stTabs [aria-selected="true"] {{
  color: var(--acc) !important;
  border-bottom: 2px solid var(--acc) !important;
}}

/*  Dataframe  */
.stDataFrame {{
  background-color: var(--card) !important;
}}
.stDataFrame th {{
  background-color: var(--bg1) !important;
  color: var(--t-sec) !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: .7rem !important;
}}
.stDataFrame td {{
  color: var(--t-pri) !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: .72rem !important;
}}

/*  Metric card  */
.m-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.1rem 1.2rem 1rem;
  text-align: center;
  position: relative;
  overflow: hidden;
  transition: border-color .2s, box-shadow .2s;
}}
.m-card::before {{
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--acc), var(--acc2));
  opacity: 0;
  transition: opacity .2s;
}}
.m-card:hover {{ border-color: var(--border-h); box-shadow: 0 4px 24px rgba(41,151,255,.10); }}
.m-card:hover::before {{ opacity: 1; }}
.m-card .val {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 2rem; font-weight: 600;
  color: var(--acc); line-height: 1.1;
  letter-spacing: -0.02em;
}}
.m-card .lbl {{
  font-size: 0.68rem; color: var(--t-sec);
  margin-top: 0.3rem; letter-spacing: 0.08em;
  text-transform: uppercase;
}}
.m-card .sub {{
  font-size: 0.62rem; color: var(--t-mut);
  margin-top: 0.2rem; font-family: 'IBM Plex Mono', monospace;
}}
.m-card .delta-up   {{ color: var(--acc2); font-size:.62rem; font-family:'IBM Plex Mono',monospace; }}
.m-card .delta-down {{ color: var(--acc3); font-size:.62rem; font-family:'IBM Plex Mono',monospace; }}

/*  Section header  */
.sec-hdr {{
  font-size: .78rem; font-weight: 600;
  color: var(--t-sec); letter-spacing: .1em;
  text-transform: uppercase;
  border-bottom: 1px solid var(--border);
  padding-bottom: .4rem; margin-bottom: .8rem;
  margin-top: 1.2rem;
}}

/*  Case intro  */
.case-intro {{
  background: var(--card);
  border: 1px solid var(--border);
  border-left: 3px solid var(--acc);
  border-radius: 8px;
  padding: .9rem 1.25rem;
  margin-bottom: 1.25rem;
  font-size: .82rem; color: var(--t-sec); line-height: 1.65;
}}

/*  Alert boxes  */
.al-epic {{ background:{ERR_BG}; border-left:3px solid {ERR_BD}; padding:.65rem .9rem; border-radius:6px; margin:.25rem 0; font-size:.78rem; color:{T_PRI}; }}
.al-warn {{ background:{WARN_BG}; border-left:3px solid {WARN_BD}; padding:.65rem .9rem; border-radius:6px; margin:.25rem 0; font-size:.78rem; color:{T_PRI}; }}
.al-info {{ background:{INFO_BG}; border-left:3px solid {INFO_BD}; padding:.65rem .9rem; border-radius:6px; margin:.25rem 0; font-size:.78rem; color:{T_PRI}; }}

/*  Badges  */
.badge {{
  display: inline-block;
  background: rgba(41,151,255,.1);
  color: var(--acc); border: 1px solid rgba(41,151,255,.25);
  border-radius: 4px; padding: .12rem .5rem;
  font-family: 'IBM Plex Mono', monospace; font-size: .6rem;
  margin: .1rem;
}}

/*  Country nav card  */
.country-nav {{
  background: var(--nav-active);
  border: 1px solid var(--acc);
  border-radius: 10px;
  padding: .8rem 1rem;
  margin-top: .5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}}
.country-nav .cn-title {{
  font-size: .8rem; font-weight: 600; color: var(--acc);
  font-family: 'Sora', sans-serif;
}}
.country-nav .cn-sub {{
  font-size: .65rem; color: var(--t-sec);
  font-family: 'IBM Plex Mono', monospace;
}}

/*  Map view toggle  */
.view-toggle {{
  display: flex; gap: .4rem; margin-bottom: .6rem;
}}

/*  Page title  */
h1 {{
  font-family: 'Sora', sans-serif !important;
  font-weight: 700 !important; font-size: 1.55rem !important;
  color: var(--t-pri) !important; letter-spacing: -.02em !important;
  margin-bottom: .1rem !important;
}}
h2, h3 {{
  color: var(--t-pri) !important;
}}

/*  Logo  */
.logo-wrap {{
  font-family: 'Sora', sans-serif;
  font-size: 1.3rem; font-weight: 700; margin-bottom: .15rem;
}}
.logo-epi {{ color: var(--acc); }}
.logo-sia {{ color: var(--t-pri); }}
.logo-tag {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: .6rem; color: var(--t-mut);
  letter-spacing: .08em; text-transform: uppercase;
}}

/*  Streamlit alerts  */
div[data-testid="stSuccess"] {{
  background: {SUCCESS_BG} !important;
  border: 1px solid {SUCCESS_BD} !important; color: {T_PRI} !important;
}}
div[data-testid="stInfo"] {{
  background: {INFO_BG} !important;
  border: 1px solid {INFO_BD} !important; color: {T_PRI} !important;
}}
div[data-testid="stWarning"] {{
  background: {WARN_BG} !important;
  border: 1px solid {WARN_BD} !important; color: {T_PRI} !important;
}}
div[data-testid="stError"] {{
  background: {ERR_BG} !important;
  border: 1px solid {ERR_BD} !important; color: {T_PRI} !important;
}}
div[data-testid="stSuccess"] p,
div[data-testid="stInfo"] p,
div[data-testid="stWarning"] p,
div[data-testid="stError"] p {{
  color: {T_PRI} !important;
}}

/*  Divider  */
hr {{
  border-color: var(--border) !important;
}}

/*  Plotly chart container  */
.js-plotly-plot .plotly {{
  border-radius: 8px;
}}
</style>
""", unsafe_allow_html=True)

#  Helpers 
def card(val, lbl, sub="", delta=None, delta_dir="up"):
    delta_html = ""
    if delta:
        cls = "delta-up" if delta_dir == "up" else "delta-down"
        arrow = "▲" if delta_dir == "up" else "▼"
        delta_html = f'<div class="{cls}">{arrow} {delta}</div>'
    return f"""
    <div class="m-card">
      <div class="val">{val}</div>
      <div class="lbl">{lbl}</div>
      <div class="sub">{sub}</div>
      {delta_html}
    </div>"""

def sec(title):
    return f'<div class="sec-hdr">{title}</div>'

def intro(text):
    return f'<div class="case-intro">{text}</div>'

def navigate_to(page_name):
    """Navigate programmatically to a page."""
    if page_name in PAGES:
        st.session_state.page_idx = PAGES.index(page_name)
        st.rerun()

# P value format

def fmt_p(p: float) -> str:
    """P-value formatted according to standard epidemiological conventions."""
    if p < 0.0001:
        return "<0.0001"
    elif p < 0.001:
        return f"{p:.4f}"
    else:
        return f"{p:.3f}"

#  Sidebar 
with st.sidebar:
    st.markdown("""
    <div class="logo-wrap">
      <span class="logo-epi">Epi</span><span class="logo-sia">sia</span>
    </div>
    <div class="logo-tag">Open epidemiology · Africa</div>
    """, unsafe_allow_html=True)

    st.divider()

    page = st.radio(
        "Navigation",
        PAGES,
        index=st.session_state.page_idx,
        label_visibility="collapsed"
    )
    # Sync session state with manual radio click
    st.session_state.page_idx = PAGES.index(page)

    st.divider()
    st.markdown(
        f'<div class="badge">v0.1.1</div> <div class="badge">Xcept-Health</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div style="font-size:.62rem;color:{T_MUT};margin-top:.5rem;font-family:IBM Plex Mono,monospace">'
        '[GitHub](https://github.com/Xcept-Health/episia) · MIT License</div>',
        unsafe_allow_html=True
    )


# PAGE : Home

#  Session state
if "lang" not in st.session_state:
    st.session_state.lang = "en"

if page == "Home":
    st.title("Episia · Open Epidemiology for Africa")

    #  Toggle langue 
    col_lang, _ = st.columns([1, 4])
    with col_lang:
        lang_label = "Passer en français" if st.session_state.lang == "en" else "Switch to English"
        if st.button(lang_label, use_container_width=True):
            st.session_state.lang = "fr" if st.session_state.lang == "en" else "en"
            st.rerun()

    L = st.session_state.lang

    #  Contenu bilingue 
    content = {
        "intro": {
            "en": (
                "Episia is an open source Python library that ports OpenEpi algorithms "
                "to an African context. This interactive dashboard lets you explore its "
                "capabilities without writing a single line of code."
            ),
            "fr": (
                "Episia est une bibliothèque Python open source qui porte les algorithmes d'OpenEpi "
                "dans un contexte africain. Ce tableau de bord interactif permet d'explorer ses "
                "capacités sans écrire une seule ligne de code."
            ),
        },
        "what_title": {"en": "What is Episia?", "fr": "Qu'est-ce qu'Episia ?"},
        "what_body": {
            "en": (
                "Episia is a tool for <strong style='color:{T_PRI}'>epidemiologists, "
                "public health officers, and researchers</strong> working in sub-Saharan Africa. "
                "It automates the most common statistical computations in epidemic surveillance: "
                "attack rates, vaccine efficacy, diagnostic test performance, sample size, "
                "and outbreak modelling."
                "<br><br>All formulas are validated against "
                "<strong style='color:{ACC}'>OpenEpi</strong> (WHO reference tool) "
                "and <strong style='color:{ACC}'>WHO/UNICEF</strong> guidelines."
            ),
            "fr": (
                "Episia est un outil pour les <strong style='color:{T_PRI}'>épidémiologistes, "
                "agents de santé publique et chercheurs</strong> qui travaillent en Afrique "
                "sub-saharienne. Il automatise les calculs statistiques les plus courants en "
                "surveillance épidémiologique : taux d'attaque, efficacité vaccinale, performance "
                "des tests diagnostiques, taille d'échantillon, et modélisation d'épidémies."
                "<br><br>Toutes les formules sont validées contre "
                "<strong style='color:{ACC}'>OpenEpi</strong> "
                "(l'outil de référence de l'OMS) et les recommandations "
                "<strong style='color:{ACC}'>WHO/UNICEF</strong>."
            ),
        },
        "modules_title": {
            "en": "The 7 dashboard modules",
            "fr": "Les 7 modules du tableau de bord",
        },
        "concepts_title": {
            "en": "Key concepts — glossary",
            "fr": "Concepts clés — glossaire",
        },
        "access_title": {"en": "Access & source code", "fr": "Accès & code source"},
    }

    #  Intro 
    st.markdown(intro(content["intro"][L]), unsafe_allow_html=True)

    #  Qu'est-ce qu'Episia ? 
    st.markdown(sec(content["what_title"][L]), unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:10px;'
        f'padding:1.1rem 1.4rem;font-size:.84rem;color:{T_SEC};line-height:1.75">'
        + content["what_body"][L].format(T_PRI=T_PRI, ACC=ACC) +
        f'</div>',
        unsafe_allow_html=True
    )

    #  Modules 
    st.markdown(sec(content["modules_title"][L]), unsafe_allow_html=True)

    modules = [
        (
            "Disease Burden Globe", ACC,
            {"en": "Disease burden map",           "fr": "Carte de charge de morbidité"},
            {
                "en": "Interactive geographic visualization of 5 disease burdens "
                      "(meningitis, malaria, cholera, HIV, malnutrition) across 47 African countries. "
                      "Toggle between 3D globe and flat map. Select a country to open its dedicated analysis.",
                "fr": "Visualisation géographique interactive du fardeau de 5 maladies "
                      "(méningite, paludisme, choléra, VIH, malnutrition) dans 47 pays africains. "
                      "Basculez entre vue 3D et carte plate. Sélectionnez un pays pour ouvrir son analyse dédiée.",
            },
            {
                "en": "Used by: public health planners, journalists, donors.",
                "fr": "Qui l'utilise : planificateurs santé publique, journalistes, bailleurs de fonds.",
            },
        ),
        (
            "Meningitis · Burkina Faso", ACC3,
            {"en": "Weekly epidemic surveillance",  "fr": "Surveillance épidémique hebdomadaire"},
            {
                "en": "Simulates the SNIS/DHIS2 surveillance system of the Burkina Faso Ministry of Health. "
                      "Detects epidemic weeks, generates alerts, and projects the impact of 4 intervention "
                      "scenarios (none, mass vaccination, ring, combined).",
                "fr": "Simule le système de surveillance SNIS/DHIS2 du Ministère de la Santé du Burkina Faso. "
                      "Détecte les semaines épidémiques, génère des alertes, et projette l'impact de "
                      "4 scénarios d'intervention (aucune, vaccination de masse, anneau, combinée).",
            },
            {
                "en": "Used by: district epidemiologists, outbreak response teams.",
                "fr": "Qui l'utilise : épidémiologistes districts, équipes de riposte.",
            },
        ),
        (
            "Vaccine Efficacy · MenAfriVac", ACC4,
            {"en": "Vaccine efficacy",              "fr": "Efficacité vaccinale"},
            {
                "en": "Computes VE = 1 − Risk Ratio from cohort or case-control data. "
                      "Includes a comparative forest plot with published MenAfriVac studies in the Sahel "
                      "and Mantel-Haenszel age-stratified adjustment.",
                "fr": "Calcule VE = 1 − Risque Relatif à partir de données de cohorte ou cas-témoin. "
                      "Inclut un forest plot comparatif avec les études publiées sur MenAfriVac au Sahel "
                      "et un ajustement de Mantel-Haenszel par tranche d'âge.",
            },
            {
                "en": "Used by: vaccinology researchers, programme evaluators.",
                "fr": "Qui l'utilise : chercheurs vaccinologie, évaluateurs de programmes.",
            },
        ),
        (
            "Malaria RDT Evaluation", ACC2,
            {"en": "Rapid diagnostic test performance", "fr": "Performance des tests diagnostiques rapides"},
            {
                "en": "Evaluates a malaria RDT against expert microscopy. Computes sensitivity, "
                      "specificity, LR+, LR−, PPV and NPV by local prevalence. "
                      "Projects daily missed cases and false alarms at your site.",
                "fr": "Évalue un TDR paludisme contre la microscopie experte. Calcule sensibilité, "
                      "spécificité, LR+, LR−, PPV et NPV selon la prévalence locale. "
                      "Projette le nombre de cas manqués et fausses alarmes par jour dans votre site.",
            },
            {
                "en": "Used by: lab managers, biologists, district health officers.",
                "fr": "Qui l'utilise : biologistes, responsables laboratoire, DSP.",
            },
        ),
        (
            "Cholera Outbreak Response", ACC,
            {"en": "SEIRD outbreak simulation",     "fr": "Simulation de réponse épidémique SEIRD"},
            {
                "en": "Compartmental SEIRD model (Susceptible → Exposed → Infected → Recovered → Dead). "
                      "Compares 4 scenarios: none, WASH only, oral cholera vaccine (OCV) only, combined. "
                      "Calculates lives saved and mortality reduction.",
                "fr": "Modèle compartimental SEIRD (Susceptible → Exposé → Infecté → Rétabli → Décédé). "
                      "Compare 4 scénarios : aucun, WASH seul, vaccin oral (OCV) seul, combiné. "
                      "Calcule le nombre de vies sauvées et la réduction de mortalité.",
            },
            {
                "en": "Used by: emergency coordinators, MSF/WHO/UNICEF teams.",
                "fr": "Qui l'utilise : coordinateurs urgences, équipes MSF/OMS/UNICEF.",
            },
        ),
        (
            "HIV Treatment Cascade", ACC3,
            {"en": "HIV cascade · 90-90-90 targets", "fr": "Cascade de traitement VIH · cibles 90-90-90"},
            {
                "en": "Analyses attrition across the cascade: testing → ART initiation → viral suppression. "
                      "Compares current situation to UNAIDS 90-90-90 targets. "
                      "Quantifies unmet need at each stage.",
                "fr": "Analyse l'attrition dans la cascade : dépistage → mise sous ARV → suppression virale. "
                      "Compare la situation actuelle aux cibles ONUSIDA 90-90-90. "
                      "Quantifie le besoin non couvert à chaque étape.",
            },
            {
                "en": "Used by: national HIV programmes, PEPFAR, Global Fund.",
                "fr": "Qui l'utilise : programmes nationaux VIH, PEPFAR, Global Fund.",
            },
        ),
        (
            "Child Malnutrition · MUAC", ACC4,
            {"en": "Acute malnutrition screening (MUAC)", "fr": "Dépistage malnutrition aiguë (MUAC)"},
            {
                "en": "Simulates a MUAC distribution by season and automatically classifies "
                      "SAM/MAM/Normal according to WHO thresholds. "
                      "Compares caseload to ITFC/OTP/TSFP programme capacity.",
                "fr": "Simule une distribution de MUAC selon la saison et génère automatiquement "
                      "les classifications SAM/MAM/Normal selon les seuils OMS. "
                      "Compare la charge de cas à la capacité des programmes ITFC/OTP/TSFP.",
            },
            {
                "en": "Used by: nutritionists, ACF/NRC, community health workers.",
                "fr": "Qui l'utilise : nutritionnistes, ACF/NRC, agents communautaires.",
            },
        ),
        (
            "Sample Size Calculator", ACC2,
            {"en": "Sample size calculation",       "fr": "Calcul de taille d'échantillon"},
            {
                "en": "4 methods validated against OpenEpi and Fleiss: cohort (RR), case-control (OR), "
                      "diagnostic test evaluation (sensitivity/specificity), and single proportion survey. "
                      "Includes design effect (DEFF) for cluster surveys.",
                "fr": "4 méthodes validées contre OpenEpi et Fleiss : cohorte (RR), cas-témoin (OR), "
                      "évaluation de test diagnostique (sensibilité/spécificité), et enquête de proportion. "
                      "Inclut le facteur de grappe (DEFF) pour les sondages en grappes.",
            },
            {
                "en": "Used by: researchers, MSc/PhD students, ethics committees.",
                "fr": "Qui l'utilise : chercheurs, étudiants master/doctorat, comités éthiques.",
            },
        ),
    ]

    for mod_name, color, subtitle_d, desc_d, users_d in modules:
        st.markdown(
            f'<div style="background:{CARD_BG};border:1px solid {BORDER};'
            f'border-left:4px solid {color};border-radius:10px;'
            f'padding:1rem 1.25rem;margin-bottom:.7rem">'
            f'<div style="display:flex;align-items:baseline;gap:.7rem;margin-bottom:.35rem">'
            f'<span style="font-size:.82rem;font-weight:700;color:{T_PRI}">{mod_name}</span>'
            f'<span style="font-size:.65rem;color:{color};font-family:IBM Plex Mono,monospace;'
            f'background:rgba(41,151,255,.07);border:1px solid {color}33;'
            f'border-radius:4px;padding:.1rem .45rem">{subtitle_d[L]}</span>'
            f'</div>'
            f'<div style="font-size:.79rem;color:{T_SEC};line-height:1.65;margin-bottom:.4rem">'
            f'{desc_d[L]}</div>'
            f'<div style="font-size:.67rem;color:{T_MUT};font-family:IBM Plex Mono,monospace">'
            f'{users_d[L]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    #  Glossaire 
    st.markdown(sec(content["concepts_title"][L]), unsafe_allow_html=True)

    concepts = {
        "RR · Risk Ratio / Risque Relatif": {
            "en": "Ratio of disease risk between exposed and unexposed. RR=1 → no association. RR=2 → exposed have twice the risk.",
            "fr": "Rapport du risque de maladie entre exposés et non-exposés. RR=1 → pas d'association. RR=2 → les exposés ont 2× plus de risque.",
        },
        "OR · Odds Ratio": {
            "en": "Used in case-control studies. Approximates RR when disease is rare. OR>1 → risk factor. OR<1 → protective factor.",
            "fr": "Utilisé dans les études cas-témoin. Approxime le RR quand la maladie est rare. OR>1 → facteur de risque. OR<1 → facteur protecteur.",
        },
        "VE · Vaccine Efficacy / Efficacité Vaccinale": {
            "en": "VE = (1 − RR) × 100%. VE=76% → vaccine reduces risk by 76% compared to unvaccinated.",
            "fr": "VE = (1 − RR) × 100%. VE=76% → le vaccin réduit le risque de 76% par rapport aux non-vaccinés.",
        },
        "Sensitivity / Sensibilité — Specificity / Spécificité": {
            "en": "Sensitivity = % of true cases correctly detected. Specificity = % of healthy subjects correctly negative.",
            "fr": "Sensibilité = % de vrais malades correctement détectés. Spécificité = % de sujets sains correctement négatifs.",
        },
        "PPV / NPV": {
            "en": "Positive/Negative Predictive Value: accounts for real prevalence. A highly sensitive test yields a high NPV.",
            "fr": "Valeur prédictive positive/négative : tient compte de la prévalence réelle. Un test très sensible a un NPV élevé.",
        },
        "SEIR / SEIRD": {
            "en": "Compartmental models: S=Susceptible, E=Exposed, I=Infected, R=Recovered, D=Dead. Simulate epidemic dynamics.",
            "fr": "Modèles compartimentaux : S=Susceptible, E=Exposé, I=Infecté, R=Rétabli, D=Décédé. Simulent la dynamique d'une épidémie.",
        },
        "R₀ · Basic Reproduction Number": {
            "en": "Average secondary cases generated by one index case. R₀ > 1 → epidemic grows. R₀ < 1 → epidemic dies out.",
            "fr": "Nombre moyen de cas secondaires générés par un cas index. R₀ > 1 → épidémie s'étend. R₀ < 1 → épidémie s'éteint.",
        },
        "MUAC": {
            "en": "Mid-Upper Arm Circumference. < 115mm = severe acute malnutrition (SAM). 115–125mm = moderate (MAM).",
            "fr": "Périmètre brachial. < 115mm = malnutrition aiguë sévère (MAS). 115–125mm = modérée (MAM).",
        },
        "DEFF · Design Effect": {
            "en": "Correction factor for cluster surveys. DEFF=1.5 → multiply sample size by 1.5 vs simple random sampling.",
            "fr": "Facteur correctif pour les sondages en grappes. DEFF=1,5 → taille d'échantillon à multiplier par 1,5 vs sondage aléatoire simple.",
        },
        "90-90-90 UNAIDS / ONUSIDA": {
            "en": "HIV targets: 90% of PLHIV know status · 90% on ART · 90% virally suppressed. Equals 73% overall suppression.",
            "fr": "Cibles VIH : 90% des PVVIH connaissent leur statut · 90% sous ARV · 90% en suppression virale. Équivaut à 73% de suppression globale.",
        },
    }

    col_a, col_b = st.columns(2)
    items = list(concepts.items())
    for i, (term, def_d) in enumerate(items):
        target_col = col_a if i % 2 == 0 else col_b
        with target_col:
            st.markdown(
                f'<div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:8px;'
                f'padding:.65rem .9rem;margin-bottom:.4rem">'
                f'<div style="font-size:.72rem;font-weight:600;color:{ACC};'
                f'font-family:IBM Plex Mono,monospace;margin-bottom:.25rem">{term}</div>'
                f'<div style="font-size:.76rem;color:{T_SEC};line-height:1.6">{def_d[L]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    #  Accès & code source 
    st.markdown(sec(content["access_title"][L]), unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:10px;'
        f'padding:1rem 1.25rem;display:flex;gap:2rem;align-items:center">'
        f'<div><div style="font-size:.72rem;color:{T_MUT};font-family:IBM Plex Mono,monospace">DASHBOARD</div>'
        f'<div style="font-size:.9rem;font-weight:600;color:{ACC};margin-top:.2rem">episia-dashboard.streamlit.app</div></div>'
        f'<div style="width:1px;background:{BORDER};height:40px"></div>'
        f'<div><div style="font-size:.72rem;color:{T_MUT};font-family:IBM Plex Mono,monospace">PYPI</div>'
        f'<div style="font-size:.9rem;font-weight:600;color:{ACC2};margin-top:.2rem">pip install episia</div></div>'
        f'<div style="width:1px;background:{BORDER};height:40px"></div>'
        f'<div><div style="font-size:.72rem;color:{T_MUT};font-family:IBM Plex Mono,monospace">GITHUB</div>'
        f'<div style="font-size:.9rem;font-weight:600;color:{T_PRI};margin-top:.2rem">Xcept-Health/episia · MIT</div></div>'
        f'</div>',
        unsafe_allow_html=True
    )

# PAGE : Disease Burden Globe

if page == "Disease Burden Globe":
    st.title("Disease Burden · Africa Interactive Globe")
    st.markdown(intro(
        "Geospatial visualization of infectious disease burden across sub-Saharan Africa. "
        "Toggle between diseases, switch between <strong>Flat map</strong> and <strong>3D Globe</strong>, "
        "and click <em>Explore country</em> to open a dedicated analysis page."
    ), unsafe_allow_html=True)

    col_ctrl, col_globe = st.columns([1, 2.8])

    #  Africa countries 
    africa_countries = {
        "DZA": "Algeria", "AGO": "Angola", "BEN": "Benin", "BWA": "Botswana",
        "BFA": "Burkina Faso", "BDI": "Burundi", "CMR": "Cameroon", "CAF": "CAR",
        "TCD": "Chad", "COD": "DR Congo", "COG": "Congo", "CIV": "Ivory Coast",
        "DJI": "Djibouti", "EGY": "Egypt", "ETH": "Ethiopia", "GAB": "Gabon",
        "GHA": "Ghana", "GIN": "Guinea", "GNB": "Guinea-Bissau", "KEN": "Kenya",
        "LSO": "Lesotho", "LBR": "Liberia", "LBY": "Libya", "MDG": "Madagascar",
        "MWI": "Malawi", "MLI": "Mali", "MRT": "Mauritania", "MAR": "Morocco",
        "MOZ": "Mozambique", "NAM": "Namibia", "NER": "Niger", "NGA": "Nigeria",
        "RWA": "Rwanda", "SEN": "Senegal", "SLE": "Sierra Leone", "SOM": "Somalia",
        "ZAF": "South Africa", "SSD": "South Sudan", "SDN": "Sudan",
        "TZA": "Tanzania", "TGO": "Togo", "TUN": "Tunisia", "UGA": "Uganda",
        "ZMB": "Zambia", "ZWE": "Zimbabwe", "ERI": "Eritrea", "GMB": "Gambia",
    }

    # ISO → full name reverse map
    iso_to_name = {iso: name for iso, name in africa_countries.items()}
    name_to_iso  = {name: iso for iso, name in africa_countries.items()}

    # Countries that have dedicated pages
    navigable_countries = list(COUNTRY_PAGES.keys())

    disease_data = {
        "Meningitis belt": {
            "BFA": 95, "NER": 90, "MLI": 85, "TCD": 80, "NGA": 70,
            "SDN": 65, "ETH": 55, "SEN": 50, "GHA": 40, "CMR": 45,
            "BEN": 35, "TGO": 30, "GIN": 25, "SLE": 15, "GNB": 18,
            "CAF": 50, "MRT": 40, "DJI": 20, "SOM": 30, "ERI": 22,
            "GMB": 20, "UGA": 25, "KEN": 20, "LBR": 15, "CIV": 30,
        },
        "Malaria burden": {
            "COD": 98, "NGA": 95, "BFA": 88, "MOZ": 85, "TZA": 82,
            "CMR": 80, "UGA": 78, "GHA": 72, "MLI": 70, "NER": 68,
            "ETH": 55, "KEN": 60, "RWA": 65, "BEN": 66, "TGO": 64,
            "SEN": 58, "CIV": 62, "GIN": 60, "SLE": 58, "LBR": 56,
            "CAF": 75, "TCD": 70, "BDI": 72, "MWI": 78, "ZMB": 70,
            "AGO": 68, "ZWE": 60, "MDG": 65, "SOM": 45, "SSD": 72,
        },
        "Cholera risk": {
            "COD": 92, "ETH": 75, "TCD": 78, "NER": 70, "NGA": 68,
            "SDN": 72, "SOM": 80, "CMR": 55, "CAF": 65, "UGA": 50,
            "ZMB": 55, "MWI": 58, "MOZ": 60, "TZA": 52, "KEN": 48,
            "RWA": 35, "BDI": 60, "SSD": 75, "ERI": 42, "DJI": 38,
            "MLI": 60, "GIN": 55, "SLE": 50, "LBR": 48,
        },
        "HIV prevalence": {
            "ZAF": 99, "LSO": 95, "BWA": 92, "ZWE": 85,
            "ZMB": 82, "MOZ": 80, "MWI": 78, "TZA": 70, "UGA": 65,
            "KEN": 62, "NAM": 72, "AGO": 45, "COD": 40, "CMR": 38,
            "NGA": 30, "ETH": 28, "RWA": 45, "BDI": 42, "GHA": 22,
            "CIV": 32, "MLI": 18, "SEN": 12, "NER": 10, "BFA": 15,
        },
        "Child malnutrition (wasting)": {
            "SOM": 99, "SSD": 95, "NER": 92, "TCD": 88, "MLI": 82,
            "BFA": 78, "ETH": 72, "DJI": 68, "ERI": 65, "GIN": 62,
            "CAF": 70, "SDN": 68, "NGA": 55, "MRT": 60, "GMB": 50,
            "SEN": 45, "GNB": 52, "SLE": 55, "LBR": 48, "MDG": 65,
            "MOZ": 58, "ZMB": 45, "MWI": 50, "TZA": 40, "UGA": 38,
        },
    }

    with col_ctrl:
        st.markdown(sec("Disease layer"), unsafe_allow_html=True)
        disease = st.radio("Disease layer", [
            "Meningitis belt",
            "Malaria burden",
            "Cholera risk",
            "HIV prevalence",
            "Child malnutrition (wasting)",
        ], label_visibility="collapsed")

        st.markdown(sec("Map view"), unsafe_allow_html=True)
        map_view = st.radio("Map view", ["3D Globe", "Flat Africa map"], label_visibility="collapsed")
        globe_3d = (map_view == "3D Globe")

        show_capitals   = st.checkbox("Show capital cities", value=True)
        show_clusters   = st.checkbox("Show epidemic clusters", value=False)
        colorscale_inv  = st.checkbox("Invert color scale",    value=False)

        st.markdown(sec("Context"), unsafe_allow_html=True)
        captions = {
            "Meningitis belt": (
                "The meningitis belt spans 26 countries from Senegal to Ethiopia. "
                "Burkina Faso, Niger, Mali and Chad report the highest seasonal incidence "
                "during the dry harmattan season (Dec–Jun)."
            ),
            "Malaria burden": (
                "Sub-Saharan Africa bears >90% of global malaria mortality. "
                "DRC, Nigeria, and Burkina Faso alone account for ~40% of global cases."
            ),
            "Cholera risk": (
                "Cholera risk is driven by WASH infrastructure deficits. "
                "Lake Chad basin and coastal West Africa remain hyperendemic zones."
            ),
            "HIV prevalence": (
                "Southern and Eastern Africa carry the highest HIV burden globally. "
                "West Africa shows lower prevalence but significant treatment gaps."
            ),
            "Child malnutrition (wasting)": (
                "GAM >15% constitutes an emergency threshold. "
                "Sahel countries including Burkina Faso, Mali, Niger face chronic crisis levels."
            ),
        }
        st.markdown(
            f'<div style="font-size:.75rem;color:{T_SEC};line-height:1.65;padding:.7rem .9rem;'
            f'background:{CARD_BG};border:1px solid {BORDER};border-radius:8px">'
            f'{captions[disease]}</div>',
            unsafe_allow_html=True
        )

        #  Country quick-nav 
        st.markdown(sec("Explore a country"), unsafe_allow_html=True)
        all_country_names = sorted(africa_countries.values())
        explore = st.selectbox(
            "Select country",
            [" select a country "] + all_country_names,
            label_visibility="collapsed"
        )

        if explore != " select a country ":
            iso_sel = name_to_iso.get(explore, "")
            data_sel = disease_data.get(disease, {})
            idx_val  = data_sel.get(iso_sel, 0)
            has_page = explore in COUNTRY_PAGES
            
            analysis_badge = f"&nbsp;·&nbsp;<span style='color:{ACC2}'>Analysis available</span>" if has_page else ""

            border_color = ACC if has_page else T_MUT
            st.markdown(
                f'<div style="background:{CARD_BG};border:1px solid {BORDER};'
                f'border-left:3px solid {border_color};border-radius:8px;padding:.7rem .9rem;margin:.3rem 0">'
                f'<div style="font-size:.82rem;font-weight:600;color:{T_PRI}">{explore}</div>'
                f'<div style="font-family:IBM Plex Mono,monospace;font-size:.7rem;color:{T_SEC};margin-top:.2rem">'
                f'Burden index: <span style="color:{ACC};font-weight:600">{idx_val}</span>/100{analysis_badge}'
                f'</div></div>',
                unsafe_allow_html=True
            )

            if has_page:
                target_page = COUNTRY_PAGES[explore]
                if st.button(f"→ Open {target_page}", use_container_width=True):
                    navigate_to(target_page)

    with col_globe:
        iso_list, val_list, name_list, hover_list = [], [], [], []
        data = disease_data.get(disease, {})

        # Extra info for tooltip
        country_pop = {
            "BFA": "22M", "NER": "26M", "MLI": "23M", "TCD": "18M",
            "NGA": "220M", "ETH": "125M", "COD": "100M", "SEN": "18M",
            "GHA": "33M", "CMR": "28M", "KEN": "55M", "UGA": "48M",
            "TZA": "64M", "ZAF": "60M", "MOZ": "33M", "ZMB": "19M",
        }
        alert_countries = {
            "Meningitis belt": ["BFA", "NER", "MLI", "TCD"],
            "Malaria burden":  ["COD", "NGA", "BFA"],
            "Cholera risk":    ["COD", "ETH", "SOM"],
            "HIV prevalence":  ["ZAF", "LSO", "BWA"],
            "Child malnutrition (wasting)": ["SOM", "SSD", "NER"],
        }
        active_alerts = alert_countries.get(disease, [])

        for iso, name in africa_countries.items():
            iso_list.append(iso)
            v = data.get(iso, 0)
            val_list.append(v)
            name_list.append(name)
            pop_str  = country_pop.get(iso, "-")
            alert_str = " HIGH ALERT" if iso in active_alerts else ""
            nav_str   = " · Analysis available" if name in COUNTRY_PAGES else ""
            hover_list.append(
                f"<b>{name}</b>{alert_str}<br>"
                f"Burden index: {v}/100<br>"
                f"Population: {pop_str}"
                f"{nav_str}"
            )

        scale_map = {
            "Meningitis belt":              "YlOrRd",
            "Malaria burden":               "RdPu",
            "Cholera risk":                 "Blues",
            "HIV prevalence":               "Oranges",
            "Child malnutrition (wasting)": "YlOrBr",
        }
        scale = scale_map[disease]
        if colorscale_inv:
            scale += "_r"

        disease_unit = {
            "Meningitis belt":              "Risk index (0–100)",
            "Malaria burden":               "Burden index (0–100)",
            "Cholera risk":                 "Risk score (0–100)",
            "HIV prevalence":               "Prevalence index (0–100)",
            "Child malnutrition (wasting)": "GAM index (0–100)",
        }

        fig_globe = go.Figure(go.Choropleth(
            locations=iso_list,
            z=val_list,
            text=hover_list,
            colorscale=scale,
            zmin=0, zmax=100,
            marker_line_color=PLT_LINE,
            marker_line_width=0.6,
            colorbar=dict(
                title=dict(text=disease_unit[disease], font=dict(size=9, color=PLT_FONT)),
                tickfont=dict(size=9, color=PLT_FONT, family="IBM Plex Mono"),
                bgcolor=PLT_BG,
                bordercolor=PLT_LINE,
                len=0.7,
            ),
            hovertemplate="%{text}<extra></extra>",
        ))

        #  Geo projection 
        if globe_3d:
            fig_globe.update_geos(
                projection_type="orthographic",
                projection_rotation=dict(lon=20, lat=5, roll=0),
                showcoastlines=True,
                coastlinecolor=PLT_LINE,
                showland=True, landcolor=BG2,
                showocean=True, oceancolor=BG1,
                showlakes=True, lakecolor=BG1,
                showframe=False,
                bgcolor=PLT_PAPER,
            )
        else:
            fig_globe.update_geos(
                projection_type="natural earth",
                showcoastlines=True,
                coastlinecolor=PLT_LINE,
                showland=True, landcolor=BG2,
                showocean=True, oceancolor=BG1,
                showlakes=True, lakecolor=BG1,
                showframe=False,
                bgcolor=PLT_PAPER,
                scope="africa",
                lataxis_range=[-40, 40],
                lonaxis_range=[-25, 55],
            )

        #  Capitals 
        capitals = {
            "Ouagadougou": (12.36, -1.53), "Niamey":       (13.51, 2.12),
            "Bamako":      (12.65, -8.00), "N'Djamena":    (12.11, 15.04),
            "Abuja":       (9.07,   7.40), "Dakar":        (14.69, -17.44),
            "Nairobi":     (-1.28, 36.82), "Kinshasa":     (-4.32, 15.32),
            "Accra":       (5.55,  -0.20), "Addis Ababa":  (9.02,  38.74),
            "Khartoum":    (15.55, 32.53), "Kampala":      (0.32,  32.58),
            "Lomé":        (6.14,   1.22), "Conakry":      (9.54, -13.68),
        }
        if show_capitals:
            cap_names = list(capitals.keys())
            cap_lats  = [v[0] for v in capitals.values()]
            cap_lons  = [v[1] for v in capitals.values()]
            fig_globe.add_trace(go.Scattergeo(
                lat=cap_lats, lon=cap_lons,
                text=cap_names, mode="markers+text",
                marker=dict(size=5, color=ACC, symbol="circle",
                            line=dict(width=1, color=PLT_PAPER)),
                textfont=dict(size=8, color=PLT_FONT, family="IBM Plex Mono"),
                textposition="top center",
                hoverinfo="text",
                name="Capitals",
            ))

        #  Epidemic clusters 
        cluster_defs = {
            "Meningitis belt": {
                "label": "Meningitis Belt",
                "lats":  [15.0, 14.0, 13.5, 12.5, 15.0],
                "lons":  [-16.0, 0.0, 15.0, 25.0, 35.0],
                "color": f"rgba(224,92,92,0.18)",
            },
            "Malaria burden": {
                "label": "Central Africa Hotspot",
                "lats":  [5.0, -5.0, -10.0, 5.0],
                "lons":  [10.0, 15.0, 25.0, 30.0],
                "color": f"rgba(186,85,211,0.15)",
            },
        }
        if show_clusters and disease in cluster_defs:
            cl = cluster_defs[disease]
            fig_globe.add_trace(go.Scattergeo(
                lat=cl["lats"], lon=cl["lons"],
                mode="lines",
                fill="toself",
                fillcolor=cl["color"],
                line=dict(color=ACC3, width=1.2, dash="dot"),
                name=cl["label"],
                hoverinfo="name",
            ))

        #  Navigable countries highlight 
        # Highlight BFA with a special marker
        bfa_lat, bfa_lon = 12.36, -1.53
        fig_globe.add_trace(go.Scattergeo(
            lat=[bfa_lat], lon=[bfa_lon],
            mode="markers",
            marker=dict(
                size=14, color="rgba(0,0,0,0)",
                symbol="circle",
                line=dict(width=2.5, color=ACC2)
            ),
            name="Analysis available",
            hovertext="Burkina Faso · Click 'Explore' to open analysis",
            hoverinfo="text",
        ))

        fig_globe.update_layout(
            title=dict(
                text=f"{disease}  · Sub-Saharan Africa",
                font=dict(size=13, color=PLT_FONT, family="Sora"),
                x=0.02,
            ),
            paper_bgcolor=PLT_PAPER,
            height=530,
            margin=dict(l=0, r=0, t=40, b=0),
            legend=dict(
                bgcolor=PLT_BG,
                bordercolor=PLT_LINE,
                font=dict(size=9, color=PLT_FONT),
                x=0.01, y=0.01,
            ),
        )
        st.plotly_chart(fig_globe, use_container_width=True)

        #  Stats row 
        vals_nonzero = [v for v in val_list if v > 0]
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(card(
            f"{len(vals_nonzero)}", "Countries affected",
            f"out of {len(iso_list)} mapped"
        ), unsafe_allow_html=True)
        c2.markdown(card(
            f"{np.mean(vals_nonzero):.0f}", "Mean index",
            "burden-weighted"
        ), unsafe_allow_html=True)
        c3.markdown(card(
            f"{max(val_list):.0f}", "Peak burden",
            name_list[val_list.index(max(val_list))]
        ), unsafe_allow_html=True)
        high_burden = sum(1 for v in val_list if v >= 70)
        c4.markdown(card(
            f"{high_burden}", "High-burden countries",
            "index ≥ 70"
        ), unsafe_allow_html=True)

        #  Navigation hint 
        st.markdown(
            f'<div style="font-size:.72rem;color:{T_MUT};font-family:IBM Plex Mono,monospace;'
            f'margin-top:.4rem;padding:.5rem .8rem;background:{CARD_BG};border:1px solid {BORDER};'
            f'border-radius:6px">Use <strong style="color:{T_SEC}">Explore a country</strong> '
            f'in the left panel to open dedicated analyses. '
            f'Countries with <span style="color:{ACC2}">◯ teal ring</span> have a full analysis page.</div>',
            unsafe_allow_html=True
        )



# PAGE : Meningitis Outbreak

elif page == "Meningitis · Burkina Faso":
    st.title("Meningitis Outbreak Surveillance · Burkina Faso")
    st.markdown(intro(
        "Real-world scenario: meningococcal meningitis in the Sahel belt. "
        "Seasonal epidemic pattern with peak during the dry harmattan season (weeks 10–20). "
        "Pipeline replicates the SNIS/DHIS2 weekly surveillance used by the Ministry of Health."
    ), unsafe_allow_html=True)

    from episia.models import SEIRModel
    from episia.models.parameters import SEIRParameters, ScenarioSet
    from episia.models.scenarios import ScenarioRunner
    from episia.data.surveillance import SurveillanceDataset, AlertEngine

    col_p, col_r = st.columns([1, 2.5])
    with col_p:
        st.markdown(sec("District parameters"), unsafe_allow_html=True)
        district   = st.selectbox("District", ["Kaya (Centre-Nord)", "Dori (Sahel)", "Ouahigouya (Nord)", "Titao (Nord)"])
        population = st.number_input("Population", value=350_000, step=10_000)
        year       = st.selectbox("Epidemic year", [2024, 2023, 2022])

        st.markdown(sec("Transmission"), unsafe_allow_html=True)
        beta  = st.slider("β (transmission)", 0.20, 0.70, 0.42, 0.01)
        sigma = st.slider("σ (1/incubation)", 0.15, 0.50, 0.25, 0.01)
        gamma = st.slider("γ (1/infectious period)", 0.10, 0.50, 1/7, 0.01)
        vax_coverage = st.slider("Vaccine coverage (%)", 0, 100, 35)

        st.markdown(sec("Alert thresholds"), unsafe_allow_html=True)
        thresh_abs = st.slider("Cases/week threshold", 5, 50, 15)
        zscore_t   = st.slider("Z-score threshold", 1.0, 4.0, 2.0, 0.1)

    with col_r:
        np.random.seed(42 + year - 2024)
        weeks    = np.arange(1, 53)
        endemic  = np.random.poisson(3, 52).astype(float)
        peak_amp = int(population / 1000 * 0.9 * (1 - vax_coverage/100))
        epidemic = np.exp(-0.5*((weeks - 15)/3.5)**2) * peak_amp
        cases    = np.clip((endemic + epidemic).astype(int), 0, None)
        dates    = pd.date_range(f"{year}-01-01", periods=52, freq="W")

        df_s   = pd.DataFrame({"date": dates, "cases": cases, "district": district})
        ds     = SurveillanceDataset(df_s, date_col="date", cases_col="cases", district_col="district")
        engine = AlertEngine(ds)
        alerts = engine.run(threshold=thresh_abs, zscore_threshold=zscore_t)

        n_epidemic   = sum(1 for a in alerts if a.severity == "epidemic")
        n_warning    = sum(1 for a in alerts if a.severity == "warning")
        attack_rate  = cases.sum() / population * 100_000

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(card(f"{cases.sum():,}", "Total cases", f"Year {year}"), unsafe_allow_html=True)
        c2.markdown(card(f"{n_epidemic}", "Epidemic alerts", "weeks above threshold",
                         delta=f"{n_warning} warnings", delta_dir="down"), unsafe_allow_html=True)
        c3.markdown(card(f"{cases.max()}", "Peak cases/wk", f"week {int(weeks[np.argmax(cases)])}"), unsafe_allow_html=True)
        c4.markdown(card(f"{attack_rate:.0f}", "Attack rate", "per 100,000"), unsafe_allow_html=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=dates, y=cases, name="Weekly cases",
                             marker_color=ACC, opacity=0.7))
        fig.add_hline(y=thresh_abs, line_dash="dash", line_color=ACC3,
                      annotation_text=f"Epidemic threshold ({thresh_abs}/week)",
                      annotation_font_color=ACC3)
        for a in alerts:
            if a.severity == "epidemic" and a.period in list(dates):
                idx = list(dates).index(a.period)
                if idx < len(dates)-1:
                    fig.add_vrect(x0=dates[idx], x1=dates[min(idx+1, 51)],
                                  fillcolor="rgba(224,92,92,0.06)", layer="below", line_width=0)
        fig.update_layout(title=f"Weekly meningitis cases · {district} ({year})",
                          xaxis_title="Week", yaxis_title="Cases",
                          height=300, **PLOTLY_THEME, showlegend=False, bargap=0.15)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(sec("Outbreak projection · intervention scenarios"), unsafe_allow_html=True)
        N_eff = int(population * (1 - vax_coverage/100))
        scenarios = ScenarioSet([
            ("No intervention",  SEIRParameters(N=population, I0=5, E0=20, beta=beta, sigma=sigma, gamma=gamma, t_span=(0,120))),
            ("Mass vaccination", SEIRParameters(N=N_eff, I0=5, E0=20, beta=beta, sigma=sigma, gamma=gamma, t_span=(0,120))),
            ("Ring vaccination", SEIRParameters(N=population, I0=5, E0=20, beta=beta*0.45, sigma=sigma, gamma=gamma, t_span=(0,120))),
            ("Combined",         SEIRParameters(N=N_eff, I0=5, E0=20, beta=beta*0.45, sigma=sigma, gamma=gamma, t_span=(0,120))),
        ])
        runner = ScenarioRunner(SEIRModel)
        res_sc = runner.run(scenarios)
        df_sc  = res_sc.to_dataframe()

        colors = [ACC3, ACC4, ACC, ACC2]
        fig2 = go.Figure()
        for (name, params), color in zip(scenarios, colors):
            r = SEIRModel(params).run()
            fig2.add_trace(go.Scatter(x=r.t, y=r.compartments["I"],
                                      name=name, line=dict(color=color, width=2.2)))
        fig2.update_layout(title="Infected (I) · intervention scenarios",
                           xaxis_title="Days", yaxis_title="Infected",
                           height=280, hovermode="x unified", **PLOTLY_THEME,
                           legend=dict(bgcolor=PLT_BG, x=0.62, y=0.95, font_size=10))
        st.plotly_chart(fig2, use_container_width=True)

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
            st.markdown('<div class="sec-hdr">Top alerts</div>', unsafe_allow_html=True)
            for a in sorted(alerts, key=lambda x: x.severity)[:6]:
                cls = "al-epic" if a.severity == "epidemic" else "al-warn" if a.severity == "warning" else "al-info"
                st.markdown(
                    f'<div class="{cls}"><strong>{a.severity.upper()}</strong> · '
                    f'{str(a.period)[:10]}<br><small style="opacity:.8">{a.message[:65]}</small></div>',
                    unsafe_allow_html=True)



# PAGE : Vaccine Efficacy

elif page == "Vaccine Efficacy · MenAfriVac":
    st.title("Vaccine Efficacy Analysis · MenAfriVac")
    st.markdown(intro(
        "MenAfriVac (PsA-TT) deployed across the Sahel belt since 2010. "
        "This tool computes VE = 1 − RR from cohort or case-control data, "
        "with confidence intervals validated against OpenEpi."
    ), unsafe_allow_html=True)

    from episia.stats.contingency import risk_ratio, odds_ratio, Table2x2
    from episia.stats.stratified import mantel_haenszel_or

    tab_cohort, tab_stratified = st.tabs(["Cohort Analysis", "Age-stratified · Mantel-Haenszel"])

    with tab_cohort:
        col_p, col_r = st.columns([1, 2])
        with col_p:
            st.markdown(sec("Study data"), unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:.72rem;color:{T_SEC};margin-bottom:.4rem">Vaccinated group</div>', unsafe_allow_html=True)
            a = st.number_input("Cases (vaccinated)",     value=12,   min_value=0)
            b = st.number_input("Non-cases (vaccinated)", value=2988, min_value=0)
            st.markdown(f'<div style="font-size:.72rem;color:{T_SEC};margin-bottom:.4rem">Unvaccinated group</div>', unsafe_allow_html=True)
            c = st.number_input("Cases (unvaccinated)",     value=87,   min_value=0)
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
                c1.markdown(card(f"{ve:.1f}%", "Vaccine Efficacy", f"[{ve_lo:.1f}% – {ve_hi:.1f}%]"), unsafe_allow_html=True)
                c2.markdown(card(f"{rr.estimate:.3f}", "Risk Ratio", f"p={fmt_p(rr.p_value)}"), unsafe_allow_html=True)
                c3.markdown(card(f"{r_vacc:.1f}", "Risk vaccinated", "per 1,000"), unsafe_allow_html=True)
                c4.markdown(card(f"{r_unv:.1f}", "Risk unvaccinated", "per 1,000"), unsafe_allow_html=True)

                if ve > 70 and rr.p_value < 0.05:
                    st.success(f"High vaccine efficacy ({ve:.1f}%)  statistically significant (p={fmt_p(rr.p_value)}).")
                elif ve > 50:
                    st.warning(f"Moderate vaccine efficacy ({ve:.1f}%). Consider coverage improvements.")
                elif ve < 0:
                    st.error("Negative VE  investigate cold chain or selection bias.")

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=["Vaccinated", "Unvaccinated"], y=[r_vacc, r_unv],
                    marker_color=[ACC2, ACC3],
                    text=[f"{r_vacc:.1f}/1000", f"{r_unv:.1f}/1000"],
                    textposition="outside",
                    textfont=dict(color=PLT_FONT),
                ))
                fig.update_layout(
                    title=f"Meningitis risk comparison · {study_site} ({study_year})",
                    yaxis_title="Cases per 1,000 person-years",
                    height=300, **PLOTLY_THEME, showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)

                st.markdown(sec("VE estimates · regional comparison"), unsafe_allow_html=True)
                studies = {
                    "Mali 2011 (Djibo)":        (94.0, 88.0, 97.0),
                    "Niger 2012 (Zinder)":      (89.3, 79.4, 94.5),
                    "Burkina Faso 2012":        (87.6, 72.1, 94.3),
                    "Chad 2013":                (79.4, 63.1, 88.5),
                    f"{study_site} ({study_year})": (ve, ve_lo, ve_hi),
                }
                fig2 = go.Figure()
                for i, (sname, (est, lo, hi)) in enumerate(studies.items()):
                    clr = ACC if (study_site.split(",")[0] in sname or study_year in sname) else T_SEC
                    fig2.add_trace(go.Scatter(
                        x=[lo, est, hi], y=[sname]*3, mode="lines+markers",
                        marker=dict(size=[9, 15, 9], color=clr),
                        line=dict(color=clr, width=2.5), showlegend=False,
                    ))
                fig2.add_vline(x=0, line_dash="dash", line_color=T_MUT, opacity=0.5)
                fig2.update_layout(
                    title="Forest plot · VE across sites",
                    xaxis_title="Vaccine Efficacy (%)",
                    height=290, **PLOTLY_THEME,
                )
                st.plotly_chart(fig2, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {e}")

    with tab_stratified:
        st.markdown(f'<div style="font-size:.78rem;color:{T_SEC};margin-bottom:.8rem">Mantel-Haenszel pooled estimate controlling for age group.</div>', unsafe_allow_html=True)
        col_p, col_r = st.columns([1, 2])
        with col_p:
            st.markdown(sec("Data by age group"), unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:.72rem;color:{T_SEC}">Children &lt; 5 years</div>', unsafe_allow_html=True)
            a1,b1,c1_v,d1 = (st.number_input("a1",value=4,key="a1"),st.number_input("b1",value=896,key="b1"),
                              st.number_input("c1",value=31,key="c1"),st.number_input("d1",value=869,key="d1"))
            st.markdown(f'<div style="font-size:.72rem;color:{T_SEC}">Children 5–14 years</div>', unsafe_allow_html=True)
            a2,b2,c2_v,d2 = (st.number_input("a2",value=5,key="a2"),st.number_input("b2",value=1145,key="b2"),
                              st.number_input("c2",value=38,key="c2"),st.number_input("d2",value=1112,key="d2"))
            st.markdown(f'<div style="font-size:.72rem;color:{T_SEC}">Adults 15+ years</div>', unsafe_allow_html=True)
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
            c1x.markdown(card(f"{mh.common_or:.3f}", "Pooled OR (MH)", f"[{lo_or:.3f} – {hi_or:.3f}]"), unsafe_allow_html=True)
            c2x.markdown(card(f"{pooled_ve:.1f}%", "Pooled VE", f"[{pooled_ve_lo:.1f}% – {pooled_ve_hi:.1f}%]"), unsafe_allow_html=True)
            c3x.markdown(card(f"{mh.q_p_value:.3f}", "p heterogeneity", "Cochran Q"), unsafe_allow_html=True)

            ages_or    = [Table2x2(a1,b1,c1_v,d1).odds_ratio(), Table2x2(a2,b2,c2_v,d2).odds_ratio(), Table2x2(a3,b3,c3_v,d3).odds_ratio()]
            age_labels = ["< 5 years","5–14 years","15+ years"]
            fig = go.Figure()
            for lbl, or_res in zip(age_labels, ages_or):
                fig.add_trace(go.Scatter(
                    x=[or_res.ci_lower, or_res.estimate, or_res.ci_upper],
                    y=[lbl]*3, mode="lines+markers",
                    marker=dict(size=[9,14,9], color=ACC),
                    line=dict(color=ACC, width=2), showlegend=False,
                ))
            fig.add_trace(go.Scatter(
                x=[lo_or, mh.common_or, hi_or],
                y=["Pooled (MH)"]*3, mode="lines+markers",
                marker=dict(size=[10,18,10], symbol=["line-ew","diamond","line-ew"], color=ACC2),
                line=dict(color=ACC2, width=3), showlegend=False,
            ))
            fig.add_vline(x=1, line_dash="dash", line_color=T_MUT)
            fig.update_layout(title="Stratified OR by age group · Forest plot",
                               xaxis_title="Odds Ratio (log scale)", xaxis_type="log",
                               height=280, **PLOTLY_THEME)
            st.plotly_chart(fig, use_container_width=True)



# PAGE : Malaria RDT

elif page == "Malaria RDT Evaluation":
    st.title("Malaria RDT Performance Evaluation")
    st.markdown(intro(
        "RDTs are the frontline diagnostic tool in low-resource settings. "
        "This analysis evaluates RDT performance against gold-standard microscopy "
        "and computes clinical utility (PPV/NPV) across prevalence levels  "
        "critical for district-level decision making in Burkina Faso."
    ), unsafe_allow_html=True)

    from episia.stats.diagnostic import diagnostic_test_2x2, predictive_values_from_sens_spec

    col_p, col_r = st.columns([1, 2.2])
    with col_p:
        st.markdown(sec("RDT validation data"), unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:.72rem;color:{T_SEC};margin-bottom:.3rem">vs. expert microscopy</div>', unsafe_allow_html=True)
        tp = st.number_input("True Positives",  value=142, min_value=0)
        fp = st.number_input("False Positives", value=18,  min_value=0)
        fn = st.number_input("False Negatives", value=23,  min_value=0)
        tn = st.number_input("True Negatives",  value=317, min_value=0)
        rdt_name = st.text_input("RDT name",   value="CareStart HRP2/pLDH")
        site     = st.text_input("Site",        value="CHR Koudougou, Burkina Faso")

        st.markdown(sec("Clinical context"), unsafe_allow_html=True)
        prev_range = st.slider("Prevalence range (%)", 1, 80, (5, 40))
        n_patients = st.number_input("Daily patient volume", value=120, min_value=10)

    with col_r:
        try:
            d = diagnostic_test_2x2(tp=tp, fp=fp, fn=fn, tn=tn)
            c1,c2,c3,c4 = st.columns(4)
            c1.markdown(card(f"{d.sensitivity*100:.1f}%", "Sensitivity",  "True positive rate"), unsafe_allow_html=True)
            c2.markdown(card(f"{d.specificity*100:.1f}%", "Specificity",  "True negative rate"), unsafe_allow_html=True)
            c3.markdown(card(f"{d.lr_positive:.1f}",      "LR+",          "Likelihood ratio+"),  unsafe_allow_html=True)
            c4.markdown(card(f"{d.lr_negative:.3f}",      "LR-",          "Likelihood ratio-"),  unsafe_allow_html=True)

            prevs = np.linspace(prev_range[0]/100, prev_range[1]/100, 60)
            ppvs, npvs = [], []
            for p in prevs:
                ppv, npv = predictive_values_from_sens_spec(d.sensitivity, d.specificity, p)
                ppvs.append(ppv*100); npvs.append(npv*100)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=prevs*100, y=ppvs, name="PPV", line=dict(color=ACC, width=2.5)))
            fig.add_trace(go.Scatter(x=prevs*100, y=npvs, name="NPV", line=dict(color=ACC2, width=2.5)))
            fig.add_hline(y=90, line_dash="dot", line_color=T_MUT, opacity=0.5, annotation_text="90%",
                          annotation_font_color=T_MUT)
            fig.update_layout(
                title=f"PPV & NPV across prevalence · {rdt_name}",
                xaxis_title="True prevalence (%)", yaxis_title="Predictive value (%)",
                height=290, hovermode="x unified",
                **PLOTLY_THEME, legend=dict(bgcolor=PLT_BG),
            )
            fig.update_yaxes(range=[0, 105])
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(sec("Operational impact at your site"), unsafe_allow_html=True)
            cols_op = st.columns(3)
            for i, prev_pct in enumerate([10, 20, 35]):
                prev_f = prev_pct / 100
                ppv_v, npv_v = predictive_values_from_sens_spec(d.sensitivity, d.specificity, prev_f)
                expected_pos = int(n_patients * prev_f)
                false_neg    = int(expected_pos * (1-d.sensitivity))
                false_pos    = int((n_patients - expected_pos) * (1-d.specificity))
                with cols_op[i]:
                    st.markdown(
                        f'<div class="m-card" style="text-align:left">'
                        f'<div class="lbl">Prevalence {prev_pct}%</div>'
                        f'<div style="margin-top:.5rem;font-size:.72rem;color:{T_SEC};font-family:IBM Plex Mono,monospace">'
                        f'PPV {ppv_v*100:.0f}% · NPV {npv_v*100:.0f}%<br>'
                        f'{expected_pos} expected cases/day<br>'
                        f'<span style="color:{ACC3}">~{false_neg} missed</span> · '
                        f'<span style="color:{ACC4}">~{false_pos} false alarms</span>'
                        f'</div></div>', unsafe_allow_html=True
                    )

            cats  = ["Sensitivity","Specificity","PPV @ 20%","NPV @ 20%","Accuracy"]
            ppv20, npv20 = predictive_values_from_sens_spec(d.sensitivity, d.specificity, 0.20)
            acc   = (tp+tn)/(tp+fp+fn+tn)*100
            vals  = [d.sensitivity*100, d.specificity*100, ppv20*100, npv20*100, acc]
            fig2  = go.Figure(go.Scatterpolar(
                r=vals+[vals[0]], theta=cats+[cats[0]],
                fill="toself", fillcolor=f"rgba(41,151,255,0.10)",
                line=dict(color=ACC, width=2), name=rdt_name,
            ))
            fig2.update_layout(
                polar=dict(
                    radialaxis=dict(range=[0,100], gridcolor=PLT_GRID, tickfont=dict(color=PLT_FONT)),
                    angularaxis=dict(tickfont=dict(color=PLT_FONT)),
                    bgcolor=PLT_BG,
                ),
                paper_bgcolor=PLT_PAPER,
                font=dict(color=PLT_FONT, family="IBM Plex Mono", size=10),
                title=dict(text=f"Diagnostic profile · {rdt_name}", font=dict(color=PLT_FONT)),
                height=320,
            )
            st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")



# PAGE : Cholera

elif page == "Cholera Outbreak Response":
    st.title("Cholera Outbreak Response Simulation")
    st.markdown(intro(
        "SEIRD model simulating cholera epidemic trajectory and projecting the impact "
        "of WASH interventions and oral cholera vaccine (OCV) deployment on case fatalities."
    ), unsafe_allow_html=True)

    from episia.models import SEIRDModel
    from episia.models.parameters import SEIRDParameters, ScenarioSet
    from episia.models.scenarios import ScenarioRunner

    col_p, col_r = st.columns([1, 2.3])
    with col_p:
        st.markdown(sec("Outbreak settings"), unsafe_allow_html=True)
        location = st.selectbox("Location", ["Niamey (Niger)", "N'Djamena (Chad)", "Tahoua (Niger)", "Maradi (Niger)"])
        N     = st.number_input("At-risk population", value=180_000, step=10_000)
        I0    = st.number_input("Initial cases",      value=12, min_value=1)
        E0    = st.number_input("Initial exposed",    value=40, min_value=0)
        t_end = st.slider("Simulation (days)", 30, 180, 90)

        st.markdown(sec("Disease parameters"), unsafe_allow_html=True)
        beta  = st.slider("β (transmission)",       0.10, 1.0,  0.55, 0.01)
        sigma = st.slider("σ (1/incubation)",        0.3,  2.0,  0.5,  0.05)
        gamma = st.slider("γ (1/infectious period)", 0.1,  0.5,  0.25, 0.01)
        mu    = st.slider("μ (case fatality rate)",  0.001, 0.05, 0.015, 0.001)

        st.markdown(sec("Interventions"), unsafe_allow_html=True)
        wash_eff = st.slider("WASH effectiveness (%)", 0, 80, 40)
        ocv_cov  = st.slider("OCV coverage (%)", 0, 90, 50)
        ocv_eff  = st.slider("OCV efficacy (%)", 50, 90, 76)

    with col_r:
        try:
            wash_b = beta * (1 - wash_eff/100)
            ocv_N  = int(N * (1 - ocv_cov/100 * ocv_eff/100))

            scenarios = ScenarioSet([
                ("No intervention", SEIRDParameters(N=N, I0=I0, E0=E0, beta=beta, sigma=sigma, gamma=gamma, mu=mu, t_span=(0,t_end))),
                ("WASH only",       SEIRDParameters(N=N, I0=I0, E0=E0, beta=wash_b, sigma=sigma, gamma=gamma, mu=mu*0.6, t_span=(0,t_end))),
                ("OCV only",        SEIRDParameters(N=ocv_N, I0=I0, E0=E0, beta=beta, sigma=sigma, gamma=gamma, mu=mu, t_span=(0,t_end))),
                ("WASH + OCV",      SEIRDParameters(N=ocv_N, I0=I0, E0=E0, beta=wash_b, sigma=sigma, gamma=gamma, mu=mu*0.6, t_span=(0,t_end))),
            ])

            colors = [ACC3, ACC4, ACC, ACC2]
            fig = go.Figure()
            deaths_by_sc = {}
            for (sname, params), color in zip(scenarios, colors):
                r = SEIRDModel(params).run()
                deaths = int(r.compartments.get("D",[0])[-1])
                deaths_by_sc[sname] = deaths
                fig.add_trace(go.Scatter(
                    x=r.t, y=r.compartments["I"],
                    name=f"{sname} ({deaths:,} deaths)",
                    line=dict(color=color, width=2.2)
                ))
            fig.update_layout(title=f"Cholera cases over time · {location}",
                               xaxis_title="Days", yaxis_title="Active cases",
                               height=320, hovermode="x unified", **PLOTLY_THEME,
                               legend=dict(bgcolor=PLT_BG, font_size=10))
            st.plotly_chart(fig, use_container_width=True)

            baseline_d = deaths_by_sc["No intervention"]
            combined_d = deaths_by_sc["WASH + OCV"]
            lives_saved = baseline_d - combined_d
            pct_reduction = (1 - combined_d/baseline_d)*100 if baseline_d > 0 else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(card(f"{baseline_d:,}", "Deaths (no action)", "baseline"), unsafe_allow_html=True)
            c2.markdown(card(f"{combined_d:,}", "Deaths (combined)",  "WASH + OCV"), unsafe_allow_html=True)
            c3.markdown(card(f"{lives_saved:,}", "Lives saved", "combined intervention",
                             delta=f"{pct_reduction:.0f}% reduction", delta_dir="up"), unsafe_allow_html=True)
            c4.markdown(card(f"{ocv_cov}%", "OCV coverage", f"efficacy {ocv_eff}%"), unsafe_allow_html=True)

            fig2 = go.Figure(go.Bar(
                x=list(deaths_by_sc.keys()),
                y=list(deaths_by_sc.values()),
                marker_color=colors,
                text=[f"{v:,}" for v in deaths_by_sc.values()],
                textposition="outside",
                textfont=dict(color=PLT_FONT),
            ))
            fig2.update_layout(
                title=f"Projected deaths · {lives_saved:,} lives saved with combined intervention",
                yaxis_title="Deaths", height=280, **PLOTLY_THEME, showlegend=False,
            )
            st.plotly_chart(fig2, use_container_width=True)
            st.success(
                f"Combined WASH + OCV reduces mortality by **{pct_reduction:.0f}%**  "
                f"saving **{lives_saved:,} lives** in {location} over {t_end} days."
            )
        except Exception as e:
            st.error(f"Error: {e}")



# PAGE : HIV Treatment Cascade

elif page == "HIV Treatment Cascade":
    st.title("HIV Treatment Cascade · 90-90-90 Analysis")
    st.markdown(intro(
        "UNAIDS 90-90-90 targets: 90% of PLHIV know their status, 90% of those on treatment, "
        "90% of those virally suppressed. This tool computes cascade attrition, "
        "estimates unmet need, and projects impact of closing each gap."
    ), unsafe_allow_html=True)

    col_p, col_r = st.columns([1, 2.4])

    with col_p:
        st.markdown(sec("Country / district"), unsafe_allow_html=True)
        country = st.selectbox("Setting", [
            "Burkina Faso (national)", "Ouagadougou district",
            "Ghana (national)", "Côte d'Ivoire (national)", "Custom entry"
        ])

        presets = {
            "Burkina Faso (national)": (110_000, 66, 79, 88),
            "Ouagadougou district":    (24_000,  72, 83, 91),
            "Ghana (national)":        (350_000, 79, 85, 93),
            "Côte d'Ivoire (national)":(430_000, 74, 81, 87),
            "Custom entry":            (50_000,  60, 70, 80),
        }
        plhiv_default, d1_def, d2_def, d3_def = presets[country]

        st.markdown(sec("Cascade inputs"), unsafe_allow_html=True)
        plhiv  = st.number_input("PLHIV (estimated)", value=plhiv_default, step=1_000)
        d1     = st.slider("% knowing status (1st 90)", 0, 100, d1_def)
        d2     = st.slider("% on ART (2nd 90)",         0, 100, d2_def)
        d3     = st.slider("% virally suppressed (3rd 90)", 0, 100, d3_def)
        year_c = st.selectbox("Reference year", [2024, 2023, 2022, 2021])

        st.markdown(sec("Targets"), unsafe_allow_html=True)
        target_1 = st.slider("Target: % knowing status", 50, 100, 90)
        target_2 = st.slider("Target: % on ART",         50, 100, 90)
        target_3 = st.slider("Target: % suppressed",     50, 100, 90)

    with col_r:
        n_know    = int(plhiv * d1/100)
        n_art     = int(n_know * d2/100)
        n_supp    = int(n_art  * d3/100)
        n_unknown = plhiv - n_know
        n_know_no_art = n_know - n_art
        n_art_unsup   = n_art - n_supp

        t_know = int(plhiv * target_1/100)
        t_art  = int(t_know * target_2/100)
        t_supp = int(t_art  * target_3/100)

        gap_know = t_know - n_know
        gap_art  = t_art  - n_art
        gap_supp = t_supp - n_supp
        overall  = n_supp / plhiv * 100

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(card(f"{plhiv:,}", "PLHIV", f"estimated {year_c}"), unsafe_allow_html=True)
        c2.markdown(card(f"{d1}%·{d2}%·{d3}%", "Cascade", "diagnosed·ART·suppressed"), unsafe_allow_html=True)
        c3.markdown(card(f"{overall:.1f}%", "Overall suppression", "of all PLHIV"), unsafe_allow_html=True)
        c4.markdown(card(f"{n_supp:,}", "Virally suppressed", "absolute number",
                         delta=f"{gap_supp:,} to target", delta_dir="up" if gap_supp > 0 else "down"),
                    unsafe_allow_html=True)

        stages  = ["PLHIV", "Know status", "On ART", "Virally suppressed"]
        values  = [plhiv, n_know, n_art, n_supp]
        targets_bar = [int(plhiv * target_1/100), t_know, t_art, t_supp]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Current", x=stages, y=values,
            marker_color=[ACC4, ACC, ACC2, ACC2],
            opacity=0.85,
            text=[f"{v:,}<br>{v/plhiv*100:.0f}%" for v in values],
            textposition="inside", textfont=dict(size=10, color=PLT_PAPER),
        ))
        fig.add_trace(go.Bar(
            name="Target", x=stages, y=targets_bar,
            marker_color=["rgba(0,0,0,0)"]*4,
            marker_line_color=[T_MUT]*4,
            marker_line_width=2,
            opacity=0.6,
        ))
        fig.add_trace(go.Scatter(
            x=stages, y=targets_bar, mode="markers",
            marker=dict(symbol="line-ew", size=20, color=T_MUT,
                        line=dict(width=2, color=T_MUT)),
            name="Target", showlegend=False,
        ))
        fig.update_layout(
            title=f"HIV Treatment Cascade · {country} ({year_c})",
            yaxis_title="Number of people",
            barmode="overlay", height=330,
            **PLOTLY_THEME,
            legend=dict(bgcolor=PLT_BG, font_size=10),
        )
        st.plotly_chart(fig, use_container_width=True)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown(sec("Cascade gaps"), unsafe_allow_html=True)
            gap_data = {
                "Unknown status":       n_unknown,
                "Know, not on ART":     n_know_no_art,
                "On ART, unsuppressed": n_art_unsup,
            }
            fig2 = go.Figure(go.Bar(
                x=list(gap_data.values()), y=list(gap_data.keys()),
                orientation="h",
                marker_color=[ACC3, ACC4, ACC],
                text=[f"{v:,}" for v in gap_data.values()],
                textposition="outside",
                textfont=dict(color=PLT_FONT),
            ))
            fig2.update_layout(
                title="Unmet need by cascade stage",
                xaxis_title="People", height=250,
                **PLOTLY_THEME, showlegend=False,
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col_g2:
            st.markdown(sec("Gap to target"), unsafe_allow_html=True)
            for label, gap, total, pct in [
                ("Knowing status", gap_know, n_know, d1),
                ("On ART",         gap_art,  n_art,  d2),
                ("Suppressed",     gap_supp, n_supp, d3),
            ]:
                color = ACC3 if gap > 0 else ACC2
                sign  = "+" if gap > 0 else ""
                st.markdown(
                    f'<div class="m-card" style="text-align:left;margin-bottom:.4rem">'
                    f'<div style="font-size:.68rem;color:{T_MUT};text-transform:uppercase;letter-spacing:.08em">{label}</div>'
                    f'<div style="font-family:IBM Plex Mono,monospace;font-size:1.1rem;color:{color};margin-top:.2rem">'
                    f'{sign}{gap:,} people</div>'
                    f'<div style="font-size:.62rem;color:{T_MUT}">current {pct}% → target</div>'
                    f'</div>', unsafe_allow_html=True
                )

        st.info(
            f"Reaching {target_1}-{target_2}-{target_3} targets in {country} would bring "
            f"**{t_supp:,}** people to viral suppression  "
            f"**{t_supp - n_supp:,} additional** compared to current ({n_supp:,})."
        )



# PAGE : Child Malnutrition MUAC

elif page == "Child Malnutrition · MUAC":
    st.title("Child Malnutrition Screening · MUAC Analysis")
    st.markdown(intro(
        "Mid-Upper Arm Circumference (MUAC) is the frontline screening tool for acute "
        "malnutrition in children 6–59 months. WHO thresholds: MUAC &lt;11.5cm = SAM, "
        "11.5–12.5cm = MAM, &gt;12.5cm = normal."
    ), unsafe_allow_html=True)

    col_p, col_r = st.columns([1, 2.4])

    with col_p:
        st.markdown(sec("Screening settings"), unsafe_allow_html=True)
        site_m     = st.text_input("Health district", value="Titao district, Nord region")
        pop_under5 = st.number_input("Population under 5", value=12_500, step=500)
        screening_cov = st.slider("Screening coverage (%)", 10, 100, 65)
        season     = st.selectbox("Season", ["Lean season (May–Sep)", "Harvest (Oct–Jan)", "Pre-lean (Feb–Apr)"])

        st.markdown(sec("MUAC distribution"), unsafe_allow_html=True)
        muac_mean = st.slider("Population mean MUAC (mm)", 100, 145, 128)
        muac_sd   = st.slider("Standard deviation (mm)", 5, 25, 13)

        st.markdown(sec("WHO thresholds"), unsafe_allow_html=True)
        sam_cutoff = st.slider("SAM cutoff (mm)", 100, 120, 115)
        mam_cutoff = st.slider("MAM upper bound (mm)", 115, 135, 125)

        st.markdown(sec("Program capacity"), unsafe_allow_html=True)
        itfc_capacity = st.number_input("ITFC beds (inpatient SAM)", value=25, min_value=5)
        otp_capacity  = st.number_input("OTP slots (outpatient SAM)", value=120, min_value=10)
        tsfp_capacity = st.number_input("TSFP slots (MAM)", value=300, min_value=20)

    with col_r:
        np.random.seed(77)
        n_screened = int(pop_under5 * screening_cov / 100)

        season_adj = {"Lean season (May–Sep)": -4, "Harvest (Oct–Jan)": +3, "Pre-lean (Feb–Apr)": -1}
        mean_adj = muac_mean + season_adj[season]

        muac_vals = np.random.normal(mean_adj, muac_sd, n_screened)
        muac_vals = np.clip(muac_vals, 80, 175)

        n_sam    = np.sum(muac_vals < sam_cutoff)
        n_mam    = np.sum((muac_vals >= sam_cutoff) & (muac_vals < mam_cutoff))
        n_normal = np.sum(muac_vals >= mam_cutoff)

        sam_prev = n_sam / n_screened * 100
        mam_prev = n_mam / n_screened * 100
        gam_prev = (n_sam + n_mam) / n_screened * 100

        gam_status = "Emergency" if gam_prev >= 15 else "Serious" if gam_prev >= 10 else "Acceptable"
        status_colors = {"Emergency": ACC3, "Serious": ACC4, "Acceptable": ACC2}
        sc = status_colors[gam_status]

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(card(f"{n_screened:,}", "Children screened", f"{screening_cov}% coverage"), unsafe_allow_html=True)
        c2.markdown(card(f"{gam_prev:.1f}%", "GAM prevalence", gam_status,
                         delta=f"SAM {sam_prev:.1f}% · MAM {mam_prev:.1f}%",
                         delta_dir="down" if gam_prev >= 10 else "up"), unsafe_allow_html=True)
        c3.markdown(card(f"{n_sam:,}", "SAM cases",  "MUAC < 115mm"), unsafe_allow_html=True)
        c4.markdown(card(f"{n_mam:,}", "MAM cases",  "115–125mm"), unsafe_allow_html=True)

        st.markdown(
            f'<div style="background:{BG2};border:1px solid {sc};border-left:4px solid {sc};'
            f'border-radius:8px;padding:.7rem 1rem;margin:.3rem 0;font-size:.82rem;color:{T_PRI}">'
            f'<strong style="color:{sc}">Nutrition situation: {gam_status}</strong> · '
            f'GAM {gam_prev:.1f}% (WHO: &lt;10% acceptable · 10–14.9% serious · ≥15% emergency)</div>',
            unsafe_allow_html=True
        )

        bins = np.arange(85, 175, 3)
        hist, edges = np.histogram(muac_vals, bins=bins)
        bar_colors = []
        for edge in edges[:-1]:
            if edge < sam_cutoff:      bar_colors.append(ACC3)
            elif edge < mam_cutoff:    bar_colors.append(ACC4)
            else:                      bar_colors.append(ACC2)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=edges[:-1], y=hist, name="MUAC distribution",
            marker_color=bar_colors, opacity=0.8, width=2.8,
        ))
        fig.add_vline(x=sam_cutoff, line_dash="dash", line_color=ACC3,
                      annotation_text=f"SAM {sam_cutoff}mm", annotation_font_color=ACC3)
        fig.add_vline(x=mam_cutoff, line_dash="dash", line_color=ACC4,
                      annotation_text=f"MAM {mam_cutoff}mm", annotation_font_color=ACC4)
        fig.update_layout(
            title=f"MUAC distribution · {site_m} · {season}",
            xaxis_title="MUAC (mm)", yaxis_title="Children",
            height=290, **PLOTLY_THEME, showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(sec("Therapeutic feeding program caseload vs. capacity"), unsafe_allow_html=True)
        col_cap1, col_cap2 = st.columns(2)

        with col_cap1:
            programs = ["ITFC (inpatient)", "OTP (outpatient)", "TSFP (MAM)"]
            caseload = [int(n_sam * 0.15), int(n_sam * 0.85), n_mam]
            capacity = [itfc_capacity, otp_capacity, tsfp_capacity]
            ratios   = [c/cap*100 for c, cap in zip(caseload, capacity)]
            ratio_colors = [ACC3 if r > 100 else ACC4 if r > 80 else ACC2 for r in ratios]

            fig2 = go.Figure()
            fig2.add_trace(go.Bar(name="Caseload", x=programs, y=caseload,
                                   marker_color=ratio_colors, opacity=0.85))
            fig2.add_trace(go.Bar(name="Capacity",  x=programs, y=capacity,
                                   marker_color=[T_MUT]*3, opacity=0.5))
            fig2.update_layout(
                title="Caseload vs. program capacity",
                yaxis_title="Children", barmode="group",
                height=270, **PLOTLY_THEME,
                legend=dict(bgcolor=PLT_BG, font_size=10),
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col_cap2:
            st.markdown(sec("Recommendations"), unsafe_allow_html=True)
            for prog, cas, cap in zip(programs, caseload, capacity):
                gap = cas - cap
                if gap > 0:
                    st.markdown(
                        f'<div class="al-epic"><strong>{prog}</strong>: '
                        f'caseload {cas} exceeds capacity {cap} by <strong>{gap} children</strong>. '
                        f'Scale up required.</div>', unsafe_allow_html=True
                    )
                elif cas / cap > 0.8:
                    st.markdown(
                        f'<div class="al-warn"><strong>{prog}</strong>: '
                        f'{cas}/{cap}  near saturation ({cas/cap*100:.0f}%). Monitor closely.</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div class="al-info"><strong>{prog}</strong>: '
                        f'{cas}/{cap}  adequate capacity ({cas/cap*100:.0f}%).</div>',
                        unsafe_allow_html=True
                    )
            monthly_cost = (int(n_sam*0.15)*85 + int(n_sam*0.85)*45 + n_mam*18)
            st.markdown(
                f'<div style="font-size:.72rem;color:{T_SEC};margin-top:.7rem;'
                f'font-family:IBM Plex Mono,monospace">Estimated monthly RUTF/CSB++ cost:<br>'
                f'<span style="font-size:1rem;color:{ACC}">${monthly_cost:,}</span></div>',
                unsafe_allow_html=True
            )

# PAGE : Sample Size Calculator

elif page == "Sample Size Calculator":
    st.title("Sample Size Calculator")
    st.markdown(intro(
        "Plan your epidemiological study with correct sample size estimates. "
        "Supports cohort studies (risk ratio), case-control (odds ratio), "
        "diagnostic test evaluations, and single proportion surveys  "
        "validated against OpenEpi and Fleiss formulas."
    ), unsafe_allow_html=True)

    from episia.stats.samplesize import (
        sample_size_risk_ratio, sample_size_odds_ratio,
        sample_size_sensitivity_specificity, sample_size_single_proportion
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "Cohort · Risk Ratio", "Case-Control · OR", "Diagnostic Test", "Single Proportion"
    ])

    with tab1:
        col_p, col_r = st.columns([1,2])
        with col_p:
            st.markdown(sec("Cohort study"), unsafe_allow_html=True)
            p0      = st.slider("Risk in unexposed (%)", 1, 50, 10) / 100
            rr_exp  = st.slider("Expected Risk Ratio", 1.1, 5.0, 2.5, 0.1)
            pw      = st.select_slider("Power", [0.70,0.80,0.85,0.90,0.95], value=0.80)
            al      = st.select_slider("Alpha (α)", [0.01,0.05,0.10], value=0.05)
            ratio_c = st.slider("Control:Case ratio", 1, 5, 1)
        with col_r:
            try:
                res = sample_size_risk_ratio(risk_unexposed=p0, risk_ratio=rr_exp, power=pw, alpha=al, r=ratio_c)
                n_cases = int(res.n_per_group) if res.n_per_group else int(res.n_cases or 0)
                n_ctrl  = int(n_cases * ratio_c)
                c1,c2,c3 = st.columns(3)
                c1.markdown(card(f"{n_cases:,}", "Cases needed",   ""), unsafe_allow_html=True)
                c2.markdown(card(f"{n_ctrl:,}",  "Controls needed",""), unsafe_allow_html=True)
                c3.markdown(card(f"{n_cases+n_ctrl:,}", "Total",   ""), unsafe_allow_html=True)

                rrs = np.linspace(1.1, 5.0, 30)
                ns  = []
                for rr_v in rrs:
                    try:
                        r_v = sample_size_risk_ratio(risk_unexposed=p0, risk_ratio=rr_v, power=pw, alpha=al)
                        ns.append(int(r_v.n_per_group or 0))
                    except:
                        ns.append(None)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=rrs, y=ns, line=dict(color=ACC, width=2.5),
                                          fill="tozeroy", fillcolor=f"rgba(41,151,255,0.07)"))
                fig.add_vline(x=rr_exp, line_dash="dash", line_color=ACC3,
                              annotation_text=f"RR={rr_exp}", annotation_font_color=ACC3)
                fig.update_layout(title="Required n vs. expected Risk Ratio",
                                   xaxis_title="Expected RR", yaxis_title="n per group",
                                   height=280, **PLOTLY_THEME)
                st.plotly_chart(fig, use_container_width=True)
                st.info(f"p₀={p0*100:.0f}%, RR={rr_exp}, α={al}, power={pw*100:.0f}% → **{n_cases:,} exposed** + **{n_ctrl:,} unexposed**.")
            except Exception as e:
                st.error(f"Error: {e}")

    with tab2:
        col_p, col_r = st.columns([1,2])
        with col_p:
            st.markdown(sec("Case-Control study"), unsafe_allow_html=True)
            p_ctrl = st.slider("Exposure in controls (%)", 5, 70, 30) / 100
            or_exp = st.slider("Expected Odds Ratio", 1.2, 6.0, 2.0, 0.1)
            pw2    = st.select_slider("Power", [0.70,0.80,0.85,0.90,0.95], value=0.80, key="pw2")
            al2    = st.select_slider("Alpha", [0.01,0.05,0.10], value=0.05, key="al2")
        with col_r:
            try:
                res2 = sample_size_odds_ratio(proportion_exposed_controls=p_ctrl, odds_ratio=or_exp, power=pw2, alpha=al2)
                n_c = int(res2.n_cases or 0)
                n_k = int(res2.n_controls or 0)
                c1,c2,c3 = st.columns(3)
                c1.markdown(card(f"{n_c:,}", "Cases",    ""), unsafe_allow_html=True)
                c2.markdown(card(f"{n_k:,}", "Controls", ""), unsafe_allow_html=True)
                c3.markdown(card(f"{n_c+n_k:,}", "Total",""), unsafe_allow_html=True)
                st.info(f"{n_c:,} cases + {n_k:,} controls to detect OR={or_exp} (power={pw2*100:.0f}%, α={al2}).")
            except Exception as e:
                st.error(f"Error: {e}")

    with tab3:
        col_p, col_r = st.columns([1,2])
        with col_p:
            st.markdown(sec("Diagnostic test evaluation"), unsafe_allow_html=True)
            exp_sens = st.slider("Expected sensitivity (%)", 50, 99, 85) / 100
            exp_spec = st.slider("Expected specificity (%)", 50, 99, 92) / 100
            prec     = st.slider("Precision (half-width CI %)", 3, 15, 7) / 100
            prev_d   = st.slider("Disease prevalence (%)", 1, 60, 20) / 100
        with col_r:
            try:
                res3 = sample_size_sensitivity_specificity(
                    expected_sens=exp_sens, expected_spec=exp_spec,
                    precision=prec, prevalence=prev_d)
                n_pos = int(res3.n_cases or 0)
                n_neg = int(res3.n_controls or 0)
                c1,c2,c3 = st.columns(3)
                c1.markdown(card(f"{n_pos:,}", "Disease+ subjects", ""), unsafe_allow_html=True)
                c2.markdown(card(f"{n_neg:,}", "Disease- subjects", ""), unsafe_allow_html=True)
                c3.markdown(card(f"{n_pos+n_neg:,}", "Total",        ""), unsafe_allow_html=True)
                st.info(f"Sens={exp_sens*100:.0f}%, Spec={exp_spec*100:.0f}%, precision ±{prec*100:.0f}%, prevalence {prev_d*100:.0f}%.")
            except Exception as e:
                st.error(f"Error: {e}")

    with tab4:
        col_p, col_r = st.columns([1,2])
        with col_p:
            st.markdown(sec("Single proportion survey"), unsafe_allow_html=True)
            exp_prop = st.slider("Expected proportion (%)", 1, 80, 30) / 100
            prec4    = st.slider("Precision ±(%)", 2, 15, 5) / 100
            al4      = st.select_slider("Alpha", [0.01,0.05,0.10], value=0.05, key="al4")
            deff     = st.slider("Design effect (cluster sampling)", 1.0, 3.0, 1.0, 0.1)
        with col_r:
            try:
                res4 = sample_size_single_proportion(
                    expected_proportion=exp_prop, precision=prec4, alpha=al4, design_effect=deff)
                n_req = int(res4.n_per_group or res4.n_total or 0)
                c1,c2 = st.columns(2)
                c1.markdown(card(f"{n_req:,}", "Required n", f"DEFF ×{deff}"), unsafe_allow_html=True)
                c2.markdown(card(f"±{prec4*100:.0f}%", "Precision", "95% CI half-width"), unsafe_allow_html=True)

                props = np.linspace(0.05, 0.70, 40)
                ns4   = []
                for pp in props:
                    try:
                        r = sample_size_single_proportion(expected_proportion=float(pp), precision=prec4, alpha=al4, design_effect=deff)
                        ns4.append(int(r.n_per_group or r.n_total or 0))
                    except:
                        ns4.append(None)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=props*100, y=ns4, line=dict(color=ACC, width=2.5),
                                          fill="tozeroy", fillcolor="rgba(41,151,255,0.07)"))
                fig.add_vline(x=exp_prop*100, line_dash="dash", line_color=ACC3)
                fig.update_layout(title="Required n vs. expected proportion",
                                   xaxis_title="Expected proportion (%)", yaxis_title="n required",
                                   height=270, **PLOTLY_THEME)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {e}")
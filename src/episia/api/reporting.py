"""
api/reporting.py - Report generation for Episia analyses.

Generates structured epidemiological reports in multiple formats:
    - Markdown  (.md)
    - HTML      (.html)   self-contained, print-ready
    - JSON      (.json)   machine-readable full export

Public classes
--------------
    EpiReport        builder: add sections, tables, figures, then export
    ReportSection    typed section (text, table, figure, metrics)

Public functions
----------------
    report_from_result()   one-line report from any EpiResult
    report_from_model()    full model run report with plots
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class ReportSection:
    kind:    str
    content: Any
    title:   Optional[str] = None
    level:   int = 2
    caption: Optional[str] = None


class EpiReport:
    """
    Structured epidemiological report builder.

    Example::

        report = EpiReport(title="Analyse SEIR", author="Dr. Ouedraogo")
        report.add_text("Introduction...", title="Introduction")
        report.add_metrics({"R0": 3.2, "Peak": 42500})
        report.add_table(df, title="Results")
        report.save_html("rapport.html")
        report.save_markdown("rapport.md")
    """

    def __init__(
        self,
        title: str = "Epidemiological report",
        author: Optional[str] = None,
        institution: Optional[str] = None,
        date: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.title       = title
        self.author      = author
        self.institution = institution
        self.date        = date or datetime.now().strftime("%d %B %Y")
        self.description = description
        self.sections: List[ReportSection] = []

    # Adders ─────

    def add_text(self, text: str, title: Optional[str] = None,
                 level: int = 2) -> "EpiReport":
        self.sections.append(ReportSection(
            kind="text", content=text, title=title, level=level))
        return self

    def add_metrics(self, metrics: Dict[str, Any],
                    title: Optional[str] = "Key indicators") -> "EpiReport":
        self.sections.append(ReportSection(
            kind="metrics", content=metrics, title=title))
        return self

    def add_table(self, data: Any, title: Optional[str] = None,
                  caption: Optional[str] = None,
                  max_rows: int = 100) -> "EpiReport":
        try:
            import pandas as pd
            if not isinstance(data, pd.DataFrame):
                data = pd.DataFrame(data)
            if len(data) > max_rows:
                caption = (caption or "") + f"\n*Truncated to {max_rows}/{len(data)} rows.*"
                data = data.head(max_rows)
        except ImportError:
            pass
        self.sections.append(ReportSection(
            kind="table", content=data, title=title, caption=caption))
        return self

    def add_result(self, result: Any,
                   title: Optional[str] = None) -> "EpiReport":
        repr_str = repr(result)
        self.sections.append(ReportSection(
            kind="text",
            content="```\n" + repr_str + "\n```",
            title=title or result.__class__.__name__,
        ))
        if hasattr(result, "to_dict"):
            d = result.to_dict()
            flat = {k: _fmt(v) for k, v in d.items()
                    if not isinstance(v, (dict, list))}
            if flat:
                self.sections.append(ReportSection(
                    kind="metrics", content=flat))
        return self

    def add_figure(self, figure: Any, title: Optional[str] = None,
                   caption: Optional[str] = None,
                   width: str = "100%") -> "EpiReport":
        html = _figure_to_html(figure, width)
        self.sections.append(ReportSection(
            kind="figure", content=html, title=title, caption=caption))
        return self

    def add_divider(self) -> "EpiReport":
        self.sections.append(ReportSection(kind="divider", content=None))
        return self

    # Markdown ────

    def to_markdown(self) -> str:
        lines = [f"# {self.title}\n"]
        if self.author:
            lines.append(f"**Author:** {self.author}  ")
        if self.institution:
            lines.append(f"**Institution:** {self.institution}  ")
        lines.append(f"**Date:** {self.date}\n")
        if self.description:
            lines.append(f"*{self.description}*\n")
        lines.append("---\n")

        for sec in self.sections:
            if sec.kind == "divider":
                lines.append("\n---\n"); continue
            if sec.title:
                lines.append(f"\n{'#' * min(sec.level, 4)} {sec.title}\n")
            if sec.kind == "text":
                lines.append(str(sec.content))
            elif sec.kind == "metrics":
                lines += ["| Indicator | Value |",
                          "|:-----------|-------:|"]
                for k, v in sec.content.items():
                    lines.append(f"| {k} | {_fmt(v)} |")
            elif sec.kind == "table":
                try:
                    import pandas as pd
                    if isinstance(sec.content, pd.DataFrame):
                        lines.append(sec.content.to_markdown(index=True))
                    else:
                        lines.append(str(sec.content))
                except ImportError:
                    lines.append(str(sec.content))
            elif sec.kind == "figure":
                lines.append("*[Figure — see HTML version]*")
            if sec.caption:
                lines.append(f"\n*{sec.caption}*")
            lines.append("")
        return "\n".join(lines)

    def save_markdown(self, path: Union[str, Path]) -> Path:
        path = Path(path)
        path.write_text(self.to_markdown(), encoding="utf-8")
        return path

    # HTML ────────

    def to_html(self) -> str:
        parts = []
        for sec in self.sections:
            if sec.kind == "divider":
                parts.append("<hr>"); continue
            if sec.title:
                tag = f"h{min(sec.level, 4)}"
                parts.append(f"<{tag}>{_esc(sec.title)}</{tag}>")
            if sec.kind == "text":
                content = str(sec.content)
                if content.startswith("```"):
                    inner = content.strip("`").strip()
                    code  = "\n".join(inner.split("\n")[1:])
                    parts.append(f"<pre><code>{_esc(code)}</code></pre>")
                else:
                    for para in content.split("\n\n"):
                        if para.strip():
                            parts.append(f"<p>{_esc(para.strip())}</p>")
            elif sec.kind == "metrics":
                rows = "".join(
                    f"<tr><td>{_esc(str(k))}</td>"
                    f"<td class='val'>{_esc(_fmt(v))}</td></tr>"
                    for k, v in sec.content.items()
                )
                parts.append(
                    f"<table class='metrics'><thead><tr>"
                    f"<th>Indicator</th><th>Value</th></tr></thead>"
                    f"<tbody>{rows}</tbody></table>"
                )
            elif sec.kind == "table":
                try:
                    import pandas as pd
                    if isinstance(sec.content, pd.DataFrame):
                        parts.append(sec.content.to_html(
                            classes="epi-table", border=0,
                            float_format=lambda x: f"{x:.4f}"))
                    else:
                        parts.append(f"<pre>{_esc(str(sec.content))}</pre>")
                except ImportError:
                    parts.append(f"<pre>{_esc(str(sec.content))}</pre>")
            elif sec.kind == "figure":
                parts.append(f'<div class="figure">{sec.content}</div>')
            if sec.caption:
                parts.append(f'<p class="caption">{_esc(sec.caption)}</p>')

        meta = ""
        if self.author:
            meta += f"<span><strong>Author:</strong> {_esc(self.author)}</span>"
        if self.institution:
            meta += f"<span><strong>Institution:</strong> {_esc(self.institution)}</span>"
        meta += f"<span><strong>Date:</strong> {_esc(self.date)}</span>"
        desc = f'<p class="desc">{_esc(self.description)}</p>' if self.description else ""

        return _HTML_TEMPLATE.format(
            title=_esc(self.title), meta=meta,
            description=desc, body="\n".join(parts),
        )

    def save_html(self, path: Union[str, Path]) -> Path:
        path = Path(path)
        path.write_text(self.to_html(), encoding="utf-8")
        return path

    # JSON ────────

    def to_json(self, indent: int = 2) -> str:
        export: Dict[str, Any] = {
            "title": self.title, "author": self.author,
            "institution": self.institution, "date": self.date,
            "sections": [],
        }
        for sec in self.sections:
            entry: Dict[str, Any] = {"kind": sec.kind, "title": sec.title}
            if sec.kind in ("text", "divider"):
                entry["content"] = str(sec.content) if sec.content else None
            elif sec.kind == "metrics":
                entry["content"] = {str(k): _fmt(v) for k, v in sec.content.items()}
            elif sec.kind == "table":
                try:
                    import pandas as pd
                    entry["content"] = (
                        sec.content.to_dict(orient="records")
                        if isinstance(sec.content, pd.DataFrame)
                        else str(sec.content)
                    )
                except ImportError:
                    entry["content"] = str(sec.content)
            elif sec.kind == "figure":
                entry["content"] = "[figure omitted]"
            if sec.caption:
                entry["caption"] = sec.caption
            export["sections"].append(entry)
        return json.dumps(export, ensure_ascii=False, indent=indent,
                          default=_json_default)

    def save_json(self, path: Union[str, Path]) -> Path:
        path = Path(path)
        path.write_text(self.to_json(), encoding="utf-8")
        return path

    def __repr__(self) -> str:
        return f"EpiReport('{self.title}', {len(self.sections)} sections)"


# Factory functions 

def report_from_result(
    result: Any,
    title: Optional[str] = None,
    author: Optional[str] = None,
    backend: str = "plotly",
    theme: str = "scientific",
) -> EpiReport:
    """One-line report from any EpiResult."""
    report = EpiReport(
        title=title or f"Report — {result.__class__.__name__}",
        author=author,
    )
    report.add_result(result, title="Results")
    try:
        fig = result.plot(backend=backend)
        report.add_figure(fig, title="Visualization")
    except Exception:
        pass
    return report


def report_from_model(
    model_result: Any,
    title: Optional[str] = None,
    author: Optional[str] = None,
    institution: Optional[str] = None,
    sensitivity_result: Optional[Any] = None,
    backend: str = "plotly",
    theme: str = "scientific",
) -> EpiReport:
    """Full model simulation report (SIR / SEIR / SEIRD)."""
    mtype  = model_result.model_type
    report = EpiReport(
        title=title or f"Model report — {mtype}",
        author=author, institution=institution,
    )

    report.add_text(
        f"Compartmental model simulation **{mtype}** "
        f"with the parameters below.",
        title="Introduction",
    )

    params = {k: _fmt(v) for k, v in model_result.parameters.items()
              if not isinstance(v, (list, dict))}
    report.add_metrics(params, title="Parameters")

    metrics: Dict[str, Any] = {}
    if model_result.r0 is not None:
        metrics["R₀"] = f"{model_result.r0:.3f}"
        hit = max(0.0, 1 - 1 / model_result.r0) if model_result.r0 > 1 else 0.0
        metrics["Herd immunity threshold"] = f"{hit:.1%}"
    if model_result.peak_infected is not None:
        metrics["Peak infectious"] = f"{model_result.peak_infected:,.0f}"
        metrics["Peak day"]      = f"{model_result.peak_time:.0f}"
    if model_result.final_size is not None:
        metrics["Final size"] = f"{model_result.final_size:.1%}"
        n = model_result.parameters.get("N", 1)
        metrics["Estimated total cases"] = f"{model_result.final_size * n:,.0f}"
    report.add_metrics(metrics, title="Epidemiological indicators")

    try:
        fig = model_result.plot(backend=backend)
        report.add_figure(fig, title="Model trajectories",
                          caption=f"Simulation {mtype} — S/E/I/R(/D) compartments.")
    except Exception:
        pass

    if sensitivity_result is not None:
        report.add_divider()
        report.add_text(
            f"Monte Carlo sensitivity analysis "
            f"({sensitivity_result.n_samples} samples).",
            title="Sensitivity analysis",
        )
        s = sensitivity_result.summary()
        sa_m: Dict[str, str] = {}
        for m, lbl in [("r0","R₀"), ("peak_infected","Peak infectious"),
                        ("final_size","Final size")]:
            if f"{m}_median" in s:
                sa_m[f"{lbl}  median"] = _fmt(s[f"{m}_median"])
                sa_m[f"{lbl}  90% CI"]  = (
                    f"[{_fmt(s[f'{m}_p5'])}, {_fmt(s[f'{m}_p95'])}]")
        report.add_metrics(sa_m)
        try:
            fig_sa = sensitivity_result.plot(compartment="I", backend=backend)
            report.add_figure(fig_sa, title="Uncertainty envelope",
                              caption="Percentiles 5–25–50–75–95.")
        except Exception:
            pass

    try:
        df = model_result.to_dataframe()
        idx = [0, len(df)//4, len(df)//2, 3*len(df)//4, len(df)-1]
        report.add_table(df.iloc[idx], title="Trajectory excerpt",
                         caption="Values at t=0, 25%, 50%, 75%, end.")
    except Exception:
        pass

    return report


# Helpers 

def _fmt(v: Any) -> str:
    if v is None: return ""
    if isinstance(v, float):
        return f"{v:,.1f}" if abs(v) >= 1000 else f"{v:.4f}"
    if isinstance(v, int):
        return f"{v:,}"
    return str(v)

def _esc(s: str) -> str:
    return (str(s).replace("&","&amp;").replace("<","&lt;")
            .replace(">","&gt;").replace('"',"&quot;"))

def _json_default(obj: Any) -> Any:
    import numpy as np
    if isinstance(obj, np.integer): return int(obj)
    if isinstance(obj, np.floating): return float(obj)
    if isinstance(obj, np.ndarray): return obj.tolist()
    return str(obj)

def _figure_to_html(figure: Any, width: str = "100%") -> str:
    try:
        import plotly.io as pio
        return pio.to_html(figure, full_html=False,
                           include_plotlyjs="cdn", default_width=width)
    except Exception:
        pass
    try:
        import io, base64
        buf = io.BytesIO()
        figure.savefig(buf, format="png", dpi=120, bbox_inches="tight")
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode()
        return (f'<img src="data:image/png;base64,{b64}" '
                f'style="width:{width};max-width:100%;" alt="figure">')
    except Exception:
        return "<p><em>[Figure not available]</em></p>"


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Episia - {title}</title>
  <style>
    :root {{
      --bg: #fbfbfd;
      --glass-bg: rgba(255, 255, 255, 0.75);
      --glass-border: rgba(255, 255, 255, 0.4);
      --text-main: #1d1d1f;
      --text-dim: #6e6e73;
      --accent: #0071e3;
      --accent-soft: rgba(0, 113, 227, 0.1);
      --card-shadow: 0 20px 40px rgba(0,0,0,0.04);
      --table-hover: rgba(0,0,0,0.02);
    }}
    [data-theme="dark"] {{
      --bg: #000000;
      --glass-bg: rgba(28, 28, 30, 0.7);
      --glass-border: rgba(255, 255, 255, 0.1);
      --text-main: #f5f5f7;
      --text-dim: #86868b;
      --accent: #2997ff;
      --accent-soft: rgba(41, 151, 255, 0.15);
      --card-shadow: 0 20px 40px rgba(0,0,0,0.4);
      --table-hover: rgba(255,255,255,0.05);
    }}
    *, *::before, *::after {{ box-sizing: border-box; transition: background-color 0.4s cubic-bezier(0.4, 0, 0.2, 1), color 0.3s ease; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", sans-serif;
      background-color: var(--bg);
      color: var(--text-main);
      margin: 0; padding: 0;
      display: flex; flex-direction: column; align-items: center;
      min-height: 100vh;
      -webkit-font-smoothing: antialiased;
    }}
    nav {{
      width: 100%; max-width: 900px;
      display: flex; justify-content: space-between; align-items: center;
      padding: 2rem; position: sticky; top: 0; z-index: 100;
      backdrop-filter: blur(10px);
    }}
    .theme-toggle {{
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      padding: 8px 16px; border-radius: 20px;
      cursor: pointer; color: var(--text-main);
      font-size: 0.85rem; font-weight: 500;
      display: flex; align-items: center; gap: 8px;
      box-shadow: var(--card-shadow);
    }}
    .theme-toggle:hover {{ transform: scale(1.05); }}
    .container {{ width: 100%; max-width: 850px; padding: 0 1.5rem 5rem; }}
    header h1 {{
      font-size: 3.2rem; font-weight: 700;
      letter-spacing: -0.04em; margin-bottom: 0.5rem; text-align: center;
    }}
    .meta {{
      display: flex; justify-content: center; gap: 2rem;
      color: var(--text-dim); font-size: 0.9rem; margin-bottom: 3rem;
    }}
    .glass-panel {{
      position: relative;
      background: var(--glass-bg);
      backdrop-filter: blur(25px) saturate(180%);
      -webkit-backdrop-filter: blur(25px) saturate(180%);
      border: 1px solid var(--glass-border);
      border-radius: 28px; padding: 4rem 3rem 3rem 3rem;
      box-shadow: var(--card-shadow);
    }}
    h2 {{ font-size: 1.6rem; margin-top: 2rem; font-weight: 600; letter-spacing: -0.02em; }}
    h3 {{ font-size: 1.2rem; margin-top: 1.5rem; font-weight: 600; }}
    p {{ line-height: 1.7; color: var(--text-main); }}
    table {{ width: 100%; border-collapse: collapse; margin: 2rem 0; }}
    th {{
      text-align: left; color: var(--text-dim);
      font-size: 0.75rem; text-transform: uppercase;
      letter-spacing: 0.1em; padding: 1rem;
      border-bottom: 1px solid var(--glass-border);
    }}
    td {{
      padding: 1.2rem 1rem;
      border-bottom: 1px solid var(--glass-border);
      font-size: 0.95rem;
    }}
    tr:hover td {{ background: var(--table-hover); }}
    .val {{
      font-family: "SF Mono", "Fira Code", monospace;
      font-weight: 600; color: var(--accent); text-align: right;
    }}
    table.metrics th {{ background: none; }}
    table.epi-table th {{ background: none; }}
    pre {{
      background: rgba(0,0,0,0.05); padding: 1.5rem;
      border-radius: 18px;
      font-family: "SF Mono", monospace; font-size: 0.85rem;
      overflow-x: auto; border: 1px solid var(--glass-border);
    }}
    [data-theme="dark"] pre {{ background: rgba(255,255,255,0.05); }}
    .figure {{ margin: 2rem 0; }}
    .caption {{ font-size: 0.85rem; color: var(--text-dim); font-style: italic; margin-top: 0.5rem; }}
    hr {{ border: none; border-top: 1px solid var(--glass-border); margin: 2rem 0; }}
    .copy-main-btn {{
      position: absolute; top: 20px; right: 24px;
      background: var(--glass-bg); border: 1px solid var(--glass-border);
      color: var(--text-main); padding: 8px 16px; border-radius: 20px;
      font-size: 0.8rem; font-weight: 600; cursor: pointer;
      backdrop-filter: blur(10px);
      box-shadow: 0 4px 6px rgba(0,0,0,0.05);
      display: flex; align-items: center; gap: 6px;
    }}
    .copy-main-btn:hover {{ color: var(--accent); border-color: var(--accent); }}
    footer {{ margin-top: 4rem; text-align: center; color: var(--text-dim); font-size: 0.85rem; }}
    @media (max-width: 600px) {{
      header h1 {{ font-size: 2.2rem; }}
      .glass-panel {{ padding: 3.5rem 1.5rem 1.5rem 1.5rem; }}
    }}
  </style>
</head>
<body>
  <nav>
    <div style="font-weight:700;font-size:1.2rem;letter-spacing:-1px;">
      Epit<span style="color:var(--accent)">oo</span>ls<span style="color:var(--accent)">.</span>
    </div>
    <button class="theme-toggle" id="theme-btn">
      <span id="theme-text">dark</span>
    </button>
  </nav>
  <div class="container">
    <header>
      <h1>{title}</h1>
      <div class="meta">{meta}</div>
    </header>
    <main class="glass-panel">
      <button class="copy-main-btn" id="copy-btn">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
      </button>
      <div id="content-to-copy">
        {description}
        <div style="margin-top:2rem">{body}</div>
      </div>
    </main>
    <footer>
      <p>© <span id="yr">2026</span> Episia  Xcept-Health</p>
    </footer>
  </div>
  <script>
    const btn = document.getElementById('theme-btn');
    const themeText = document.getElementById('theme-text');
    const html = document.documentElement;
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {{
      html.setAttribute('data-theme','dark'); themeText.innerText='light';
    }}
    btn.addEventListener('click', () => {{
      if (html.getAttribute('data-theme')==='light') {{
        html.setAttribute('data-theme','dark'); themeText.innerText='light';
      }} else {{
        html.setAttribute('data-theme','light'); themeText.innerText='dark';
      }}
    }});
    const y = new Date().getFullYear();
    if (y > 2026) document.getElementById('yr').innerText = '2026 - ' + y;
    document.getElementById('copy-btn').addEventListener('click', async () => {{
      try {{
        await navigator.clipboard.writeText(document.getElementById('content-to-copy').innerText.trim());
        document.getElementById('copy-btn').style.color = 'var(--accent)';
        setTimeout(() => document.getElementById('copy-btn').style.color = '', 2000);
      }} catch(e) {{ console.error(e); }}
    }});
  </script>
</body>
</html>"""


__all__ = [
    "EpiReport", "ReportSection",
    "report_from_result", "report_from_model",
]
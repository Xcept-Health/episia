"""
__main__.py - EpiTools quick reference.

Usage:
    python -m epitools
"""

import sys


# ─────────────────────────────────────────────────────────────────────────────
# ANSI colour helpers
# ─────────────────────────────────────────────────────────────────────────────

def _rgb(r, g, b, text):
    """True-colour ANSI escape  falls back to plain text on Windows < Win10."""
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"


def _bold(text):
    return f"\033[1m{text}\033[0m"


def _dim(text):
    return f"\033[2m{text}\033[0m"


def _supports_color():
    """Return True if the terminal supports ANSI colours."""
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # Enable VIRTUAL_TERMINAL_PROCESSING on Windows 10+
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


# ─────────────────────────────────────────────────────────────────────────────
# ASCII art title  gradient left → right across each row
# ─────────────────────────────────────────────────────────────────────────────

_LOGO = [
    " ███████╗██████╗ ██╗████████╗ ██████╗  ██████╗ ██╗     ███████╗",
    " ██╔════╝██╔══██╗██║╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██╔════╝",
    " █████╗  ██████╔╝██║   ██║   ██║   ██║██║   ██║██║     ███████╗",
    " ██╔══╝  ██╔═══╝ ██║   ██║   ██║   ██║██║   ██║██║     ╚════██║",
    " ███████╗██║     ██║   ██║   ╚██████╔╝╚██████╔╝███████╗███████║",
    " ╚══════╝╚═╝     ╚═╝   ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚══════╝",
]

# Gradient stops : teal → cyan → blue → violet → magenta
_GRADIENT = [
    (0,  210, 190),   # teal
    (0,  180, 255),   # sky blue
    (60, 130, 255),   # electric blue
    (140, 80, 255),   # violet
    (200, 50, 220),   # magenta
    (240, 80, 160),   # rose
]


def _lerp_color(stops, t):
    """Interpolate between colour stops at position t ∈ [0, 1]."""
    if t <= 0:
        return stops[0]
    if t >= 1:
        return stops[-1]
    n = len(stops) - 1
    i = int(t * n)
    i = min(i, n - 1)
    local_t = (t * n) - i
    r1, g1, b1 = stops[i]
    r2, g2, b2 = stops[i + 1]
    return (
        int(r1 + (r2 - r1) * local_t),
        int(g1 + (g2 - g1) * local_t),
        int(b1 + (b2 - b1) * local_t),
    )


def _render_logo(color: bool) -> str:
    if not color:
        return "\n".join(_LOGO)

    lines = []
    max_len = max(len(row) for row in _LOGO)
    for row in _LOGO:
        rendered = ""
        for i, ch in enumerate(row):
            t = i / max(max_len - 1, 1)
            r, g, b = _lerp_color(_GRADIENT, t)
            rendered += _rgb(r, g, b, ch)
        lines.append(rendered)
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Version & metadata
# ─────────────────────────────────────────────────────────────────────────────

def _get_version():
    try:
        from epitools import __version__
        return __version__
    except ImportError:
        pass
    try:
        import importlib.metadata
        return importlib.metadata.version("epitools")
    except Exception:
        return "0.1.0"


def _get_python_version():
    v = sys.version_info
    return f"{v.major}.{v.minor}.{v.micro}"


# ─────────────────────────────────────────────────────────────────────────────
# Module catalogue
# ─────────────────────────────────────────────────────────────────────────────

_MODULES = [
    (
        "epitools.models",
        "Compartmental epidemic models",
        [
            "SIRModel(params).run()          → ModelResult",
            "SEIRModel(params).run()         → ModelResult",
            "SEIRDModel(params).run()        → ModelResult",
            "ModelCalibrator(...).fit()      → CalibrationResult",
            "SensitivityAnalysis(...).run()  → SensitivityResult",
            "ScenarioRunner(Model).run()     → ScenarioResults",
        ],
    ),
    (
        "epitools.stats",
        "Biostatistics & epidemiological measures",
        [
            "risk_ratio(a, b, c, d)          → AssociationResult",
            "odds_ratio(a, b, c, d)          → AssociationResult",
            "proportion_ci(k, n)             → ProportionResult",
            "diagnostic_test_2x2(tp,fp,fn,tn)→ DiagnosticResult",
            "roc_analysis(y_true, y_score)   → ROCResult",
            "sample_size_risk_ratio(...)     → SampleSizeResult",
            "mantel_haenszel(strata)         → StratifiedResult",
        ],
    ),
    (
        "epitools.viz",
        "Visualization  Plotly (interactive) & Matplotlib (publication)",
        [
            "plot_epicurve(result)           → Figure",
            "plot_roc(result)                → Figure",
            "plot_forest(result)             → Figure",
            "plot_incidence(result)          → Figure",
            "plot_doubling(result)           → Figure",
            "plot_meta_forest(estimates,...) → Figure",
            "set_theme('scientific'|'dark'|'minimal'|'colorblind')",
        ],
    ),
    (
        "epitools.data",
        "Surveillance data management",
        [
            "SurveillanceDataset.from_csv()  → dataset",
            "dataset.aggregate(freq='W')     → DataFrame",
            "dataset.attack_rate(population) → float",
            "dataset.endemic_channel()       → Dict",
            "AlertEngine(dataset).run()      → List[Alert]",
        ],
    ),
    (
        "epitools.api",
        "Reporting & unified interface",
        [
            "EpiReport(...).add_metrics(...).save_html()",
            "report_from_model(result)       → EpiReport",
            "epi.seir(N, I0, E0, beta, ...)  → SEIRModel",
            "epi.risk_ratio(a, b, c, d)      → AssociationResult",
            "epi.report(result)              → EpiReport",
        ],
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Printer
# ─────────────────────────────────────────────────────────────────────────────

def _section(title, color, c_rgb):
    if color:
        r, g, b = c_rgb
        return _bold(_rgb(r, g, b, f"  {title}"))
    return f"  {title}"


def _print_doc(color: bool):
    version   = _get_version()
    py_ver    = _get_python_version()
    W         = 68

    # ── Logo ──
    print()
    print(_render_logo(color))
    print()

    # ── Tagline ──
    tagline = "Open-source epidemiology & biostatistics for Python"
    sub     = f"v{version}  ·  Python {py_ver}  ·  Xcept-Health  ·  MIT"
    if color:
        print(_rgb(160, 200, 255, f"  {tagline}"))
        print(_dim(f"  {sub}"))
    else:
        print(f"  {tagline}")
        print(f"  {sub}")

    print()
    print("  " + "─" * (W - 2))

    # ── Modules ──
    grad_steps = [
        (0,  210, 190),
        (60, 130, 255),
        (140, 80, 255),
        (240, 80, 160),
        (0,  210, 120),
    ]

    for idx, (mod, desc, functions) in enumerate(_MODULES):
        t   = idx / max(len(_MODULES) - 1, 1)
        c   = _lerp_color(grad_steps, t)
        print()
        print(_section(mod, color, c))
        if color:
            print(_dim(f"    {desc}"))
        else:
            print(f"    {desc}")
        for fn in functions:
            if color:
                r, g, b = c
                # Function name in colour, rest dimmed
                parts = fn.split("→")
                if len(parts) == 2:
                    left  = parts[0]
                    right = "→" + parts[1]
                    print(f"    {_rgb(r,g,b, left)}{_dim(right)}")
                else:
                    print(f"    {_rgb(r, g, b, fn)}")
            else:
                print(f"    {fn}")

    print()
    print("  " + "─" * (W - 2))

    # ── Quick start ──
    print()
    if color:
        print(_bold(_rgb(0, 210, 190, "  Quick start")))
    else:
        print("  Quick start")

    snippet = """\
    from epitools import epi

    # Run a SEIR model
    model  = epi.seir(N=1_000_000, I0=10, E0=50,
                      beta=0.35, sigma=1/5.2, gamma=1/14)
    result = model.run()
    print(result)
    result.plot().show()

    # Compute a risk ratio
    rr = epi.risk_ratio(a=40, b=10, c=20, d=30)
    print(rr)

    # Generate a report
    report = epi.report(result, title="SEIR  Burkina Faso")
    report.save_html("rapport.html")"""

    if color:
        print(_dim(snippet))
    else:
        print(snippet)

    # ── Footer ──
    print()
    print("  " + "─" * (W - 2))
    footer = "  GitHub : https://github.com/Xcept-Health/epitools"
    if color:
        print(_dim(footer))
    else:
        print(footer)
    print()


# ─────────────────────────────────────────────────────────────────────────────

def main():
    color = _supports_color()
    _print_doc(color)


if __name__ == "__main__":
    main()
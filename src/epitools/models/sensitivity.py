"""
models/sensitivity.py - Monte Carlo sensitivity analysis for compartmental models.

Samples parameter distributions, runs N model instances, and aggregates
trajectories into percentile envelopes + summary statistics.

Public classes
--------------
    SensitivityAnalysis    configure distributions and run sampling
    SensitivityResult      percentile envelopes, summaries, plots

Supported distributions
-----------------------
    ("uniform",   low, high)
    ("normal",    mean, std)
    ("lognormal", mean, sigma)        # mean/std of the underlying normal
    ("triangular", low, mode, high)
    ("beta_dist",  alpha, beta)       # scipy beta, scaled to [0,1]
    ("fixed",     value)              # pin a parameter, no sampling

Performance
-----------
    Uses concurrent.futures.ProcessPoolExecutor by default.
    Falls back to sequential execution if n_jobs=1 or pickling fails.
"""

from __future__ import annotations

import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Type

import numpy as np


def _cprint(text: str, color: tuple) -> None:
    """Print text in RGB colour."""
    r, g, b = color
    print(f"\033[38;2;{r};{g};{b}m{text}\033[0m")


# ─────────────────────────────────────────────────────────────────────────────
# Sampler
# ─────────────────────────────────────────────────────────────────────────────

def _sample_param(spec: Tuple, rng: np.random.Generator) -> float:
    """Draw one sample from a distribution spec."""
    kind = spec[0]

    if kind == "fixed":
        return float(spec[1])

    elif kind == "uniform":
        low, high = float(spec[1]), float(spec[2])
        return float(rng.uniform(low, high))

    elif kind == "normal":
        mean, std = float(spec[1]), float(spec[2])
        return float(rng.normal(mean, std))

    elif kind == "lognormal":
        mean, sigma = float(spec[1]), float(spec[2])
        return float(rng.lognormal(mean, sigma))

    elif kind == "triangular":
        low, mode, high = float(spec[1]), float(spec[2]), float(spec[3])
        return float(rng.triangular(low, mode, high))

    elif kind == "beta_dist":
        alpha, beta = float(spec[1]), float(spec[2])
        from scipy.stats import beta as scipy_beta
        return float(scipy_beta.rvs(alpha, beta, random_state=int(rng.integers(0, 2**31))))

    else:
        raise ValueError(
            f"Unknown distribution '{kind}'. "
            f"Choose: uniform, normal, lognormal, triangular, beta_dist, fixed."
        )


def _draw_samples(
    distributions: Dict[str, Tuple],
    n_samples: int,
    seed: Optional[int],
) -> List[Dict[str, float]]:
    """Draw n_samples parameter dicts from the given distributions."""
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(n_samples):
        draw = {k: _sample_param(spec, rng) for k, spec in distributions.items()}
        samples.append(draw)
    return samples


# ─────────────────────────────────────────────────────────────────────────────
# Worker (module-level for pickling with ProcessPoolExecutor)
# ─────────────────────────────────────────────────────────────────────────────

def _run_one(args):
    """
    Run a single model instance.

    Module-level for multiprocessing pickling on Windows (spawn).
    Robust to t_span arriving as list (JSON serialization).
    """
    model_class, param_class, fixed_params, sample, t_eval_len = args
    try:
        all_params = {**fixed_params, **sample}

        # t_span peut arriver en liste depuis sérialisation JSON
        if "t_span" in all_params and not isinstance(all_params["t_span"], tuple):
            all_params["t_span"] = tuple(all_params["t_span"])

        params = param_class(**all_params)
        model  = model_class(params)

        t_span = params.t_span
        t_eval = np.linspace(float(t_span[0]), float(t_span[1]), int(t_eval_len))
        result = model.run(t_eval=t_eval)

        return {
            "t":             np.asarray(result.t, dtype=float),
            "compartments":  {k: np.asarray(v, dtype=float)
                              for k, v in result.compartments.items()},
            "r0":            float(result.r0) if result.r0 is not None else None,
            "peak_infected": float(result.peak_infected) if result.peak_infected is not None else None,
            "peak_time":     float(result.peak_time) if result.peak_time is not None else None,
            "final_size":    float(result.final_size) if result.final_size is not None else None,
            "params":        sample,
        }
    except Exception as e:
        import traceback
        return {
            "error":  f"{type(e).__name__}: {e}",
            "detail": traceback.format_exc(),
            "params": sample,
        }


# ─────────────────────────────────────────────────────────────────────────────
# SensitivityResult
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SensitivityResult:
    """
    Aggregated result of a Monte Carlo sensitivity analysis.

    Attributes:
        t:              Common time array.
        envelopes:      Dict compartment → {'p5','p25','p50','p75','p95'} arrays.
        metrics:        DataFrame-ready summary of scalar metrics across runs.
        n_samples:      Number of successful runs.
        n_failed:       Number of failed runs.
        param_samples:  List of sampled parameter dicts.
        compartment_names: Compartments present in results.
    """
    t:                 np.ndarray
    envelopes:         Dict[str, Dict[str, np.ndarray]]
    metrics:           Dict[str, np.ndarray]      # r0, peak_infected, …
    n_samples:         int
    n_failed:          int
    param_samples:     List[Dict[str, float]]
    compartment_names: List[str]

    # ── Summary ──────────────────────────────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        """
        Return a dict of summary statistics for each scalar metric.

        Returns:
            Dict with keys like 'r0_median', 'r0_p5', 'peak_infected_p95', etc.
        """
        out: Dict[str, Any] = {
            "n_samples": self.n_samples,
            "n_failed":  self.n_failed,
        }
        for metric, values in self.metrics.items():
            if len(values) == 0:
                continue
            out[f"{metric}_median"] = float(np.median(values))
            out[f"{metric}_mean"]   = float(np.mean(values))
            out[f"{metric}_p5"]     = float(np.percentile(values, 5))
            out[f"{metric}_p95"]    = float(np.percentile(values, 95))
            out[f"{metric}_std"]    = float(np.std(values))
        return out

    def to_dataframe(self):
        """
        Return a pandas DataFrame with one row per successful run.

        Columns: sampled parameters + r0, peak_infected, peak_time, final_size.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required. pip install pandas")

        rows = []
        n = self.n_samples
        for i in range(n):
            row = {k: v[i] if len(v) == n else np.nan
                   for k, v in self.metrics.items()}
            if i < len(self.param_samples):
                row.update(self.param_samples[i])
            rows.append(row)
        return pd.DataFrame(rows)

    # ── Plots ─────────────────────────────────────────────────────────────────

    def plot(
        self,
        compartment: str = "I",
        show_samples: bool = False,
        n_sample_traces: int = 50,
        backend: str = "plotly",
        theme: str = "scientific",
        title: Optional[str] = None,
    ) -> Any:
        """
        Plot percentile envelope for a compartment.

        Args:
            compartment:      Compartment name (default 'I').
            show_samples:     Overlay individual sample trajectories.
            n_sample_traces:  How many individual traces to show (max).
            backend:          'plotly' or 'matplotlib'.
            theme:            Theme name.
            title:            Figure title (auto if None).

        Returns:
            Figure object.
        """
        if compartment not in self.envelopes:
            raise ValueError(
                f"Compartment '{compartment}' not in results. "
                f"Available: {self.compartment_names}"
            )

        env   = self.envelopes[compartment]
        t     = self.t
        title = title or (
            f"Sensitivity Analysis  {compartment}  "
            f"(n={self.n_samples})"
        )

        from ..viz.themes.registry import get_palette
        pal = get_palette(theme)
        col = pal[0]

        if backend == "plotly":
            return self._plot_plotly(
                t, env, compartment, col, title,
                show_samples, n_sample_traces, theme,
            )
        else:
            return self._plot_mpl(
                t, env, compartment, col, title,
                show_samples, n_sample_traces, theme,
            )

    def _plot_plotly(self, t, env, comp, col, title,
                     show_samples, n_traces, theme):
        import plotly.graph_objects as go
        from ..viz.plotters.plotly_plotter import _layout, _FONT_COLOR
        from ..viz.plotters import PlotConfig

        def rgba(hex_col, alpha):
            h = hex_col.lstrip("#")
            r,g,b = int(h[:2],16), int(h[2:4],16), int(h[4:],16)
            return f"rgba({r},{g},{b},{alpha})"

        fig = go.Figure()

        # p5–p95 band
        fig.add_trace(go.Scatter(
            x=list(t) + list(t[::-1]),
            y=list(env["p95"]) + list(env["p5"][::-1]),
            fill="toself",
            fillcolor=rgba(col, 0.12),
            line=dict(color="rgba(0,0,0,0)"),
            name="5e–95e percentile",
            hoverinfo="skip",
        ))
        # p25–p75 band
        fig.add_trace(go.Scatter(
            x=list(t) + list(t[::-1]),
            y=list(env["p75"]) + list(env["p25"][::-1]),
            fill="toself",
            fillcolor=rgba(col, 0.25),
            line=dict(color="rgba(0,0,0,0)"),
            name="25e–75e percentile",
            hoverinfo="skip",
        ))
        # Median
        fig.add_trace(go.Scatter(
            x=list(t), y=list(env["p50"]),
            mode="lines",
            line=dict(color=col, width=2.5),
            name="Médiane",
        ))

        # Individual traces
        if show_samples and "all_trajectories" in self.envelopes.get(comp + "_raw", {}):
            pass  # stored separately if needed

        config = PlotConfig(
            title=title, theme=theme,
            xlabel="Jours", ylabel=f"Individus ({comp})",
        )
        from ..viz.plotters.plotly_plotter import _layout
        fig.update_layout(_layout(config))
        return fig

    def _plot_mpl(self, t, env, comp, col, title,
                  show_samples, n_traces, theme):
        import matplotlib.pyplot as plt
        from ..viz.themes.registry import apply_mpl_theme
        apply_mpl_theme(theme)

        fig, ax = plt.subplots(figsize=(11, 5), facecolor="white")

        ax.fill_between(t, env["p5"], env["p95"], alpha=0.12,
                        color=col, label="5e–95e percentile")
        ax.fill_between(t, env["p25"], env["p75"], alpha=0.28,
                        color=col, label="25e–75e percentile")
        ax.plot(t, env["p50"], color=col, linewidth=2.5,
                label="Médiane")

        ax.set_xlabel("Jours", fontsize=11)
        ax.set_ylabel(f"Individus ({comp})", fontsize=11)
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        return fig

    def plot_metric_distribution(
        self,
        metric: str = "r0",
        backend: str = "plotly",
        theme: str = "scientific",
    ) -> Any:
        """
        Histogram of a scalar metric across all runs.

        Args:
            metric:  One of 'r0', 'peak_infected', 'peak_time', 'final_size'.
            backend: 'plotly' or 'matplotlib'.
            theme:   Theme name.

        Returns:
            Figure object.
        """
        if metric not in self.metrics:
            raise ValueError(
                f"Metric '{metric}' not found. "
                f"Available: {list(self.metrics.keys())}"
            )

        values = self.metrics[metric]
        label_map = {
            "r0":            "R₀",
            "peak_infected": "Pic infectieux",
            "peak_time":     "Jour du pic",
            "final_size":    "Taille finale (fraction)",
        }
        label  = label_map.get(metric, metric)
        median = float(np.median(values))
        p5     = float(np.percentile(values, 5))
        p95    = float(np.percentile(values, 95))
        title  = f"Distribution  {label}  (médiane={median:.3f})"

        from ..viz.themes.registry import get_palette
        pal = get_palette(theme)

        if backend == "plotly":
            import plotly.graph_objects as go
            from ..viz.plotters import PlotConfig
            from ..viz.plotters.plotly_plotter import _layout

            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=list(values),
                nbinsx=40,
                marker_color=pal[0],
                opacity=0.75,
                name=label,
            ))
            fig.add_vline(x=median, line=dict(color=pal[1], width=2, dash="dash"),
                          annotation_text=f"Médiane {median:.3f}",
                          annotation_position="top right")
            fig.add_vrect(x0=p5, x1=p95,
                          fillcolor=pal[0], opacity=0.08,
                          line_width=0,
                          annotation_text="5e–95e", annotation_position="top left")
            config = PlotConfig(title=title, theme=theme,
                                xlabel=label, ylabel="Fréquence")
            fig.update_layout(_layout(config))
            return fig

        else:
            import matplotlib.pyplot as plt
            from ..viz.themes.registry import apply_mpl_theme
            apply_mpl_theme(theme)

            fig, ax = plt.subplots(figsize=(8, 4), facecolor="white")
            ax.hist(values, bins=40, color=pal[0], alpha=0.75, edgecolor="white")
            ax.axvline(median, color=pal[1], linewidth=2, linestyle="--",
                       label=f"Médiane {median:.3f}")
            ax.axvspan(p5, p95, alpha=0.10, color=pal[0], label="5e–95e percentile")
            ax.set_xlabel(label, fontsize=11)
            ax.set_ylabel("Fréquence", fontsize=11)
            ax.set_title(title, fontsize=13, fontweight="bold")
            ax.legend(fontsize=10)
            ax.spines[["top", "right"]].set_visible(False)
            fig.tight_layout()
            return fig

    def __repr__(self) -> str:
        s = self.summary()
        lines = [
            f"SensitivityResult  n={self.n_samples} ({self.n_failed} failed)",
        ]
        for m in ["r0", "peak_infected", "final_size"]:
            if f"{m}_median" in s:
                lines.append(
                    f"  {m:20s}: median={s[f'{m}_median']:.3f}  "
                    f"[{s[f'{m}_p5']:.3f}, {s[f'{m}_p95']:.3f}]"
                )
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# SensitivityAnalysis
# ─────────────────────────────────────────────────────────────────────────────

class SensitivityAnalysis:
    """
    Monte Carlo sensitivity analysis for compartmental epidemic models.

    Example::

        from epitools.models.sensitivity import SensitivityAnalysis
        from epitools.models import SEIRModel
        from epitools.models.parameters import SEIRParameters

        sa = SensitivityAnalysis(
            model_class=SEIRModel,
            param_class=SEIRParameters,
            fixed=dict(N=1_000_000, I0=10, E0=50, t_span=(0, 365)),
            distributions={
                'beta':  ('uniform', 0.25, 0.50),
                'sigma': ('normal',  1/5.2, 0.02),
                'gamma': ('uniform', 1/21,  1/7),
            },
            n_samples=500,
            seed=42,
        )

        result = sa.run()
        print(result)
        result.plot(compartment='I').show()
        result.plot_metric_distribution('r0').show()
        result.to_dataframe()
    """

    def __init__(
        self,
        model_class,
        param_class,
        fixed: Dict[str, Any],
        distributions: Dict[str, Tuple],
        n_samples: int = 200,
        seed: Optional[int] = 42,
        n_jobs: int = 1,
        t_eval_points: int = 500,
    ):
        """
        Args:
            model_class:    CompartmentalModel subclass.
            param_class:    Matching parameters class.
            fixed:          Parameters held constant across all runs.
            distributions:  Parameters to sample; values are distribution specs.
                            E.g. {'beta': ('uniform', 0.2, 0.5)}.
            n_samples:      Number of Monte Carlo draws.
            seed:           Random seed for reproducibility.
            n_jobs:         Parallel workers (1 = sequential, -1 = all CPUs).
            t_eval_points:  Number of time points per trajectory.
        """
        self.model_class    = model_class
        self.param_class    = param_class
        self.fixed          = fixed
        self.distributions  = distributions
        self.n_samples      = n_samples
        self.seed           = seed
        self.n_jobs         = n_jobs
        self.t_eval_points  = t_eval_points

    # ── run ──────────────────────────────────────────────────────────────────

    def run(self, verbose: bool = True) -> SensitivityResult:
        """
        Draw samples, run all models, and return aggregated SensitivityResult.

        Args:
            verbose: Print progress summary.

        Returns:
            SensitivityResult.
        """
        if verbose:
            print(f"Sampling {self.n_samples} parameter sets…")

        samples = _draw_samples(self.distributions, self.n_samples, self.seed)

        # Validate one sample first to catch config errors early
        self._validate_one(samples[0])

        raw_results = self._execute_with_progress(samples, verbose)

        n_ok   = sum(1 for r in raw_results if "error" not in r)
        n_fail = len(raw_results) - n_ok

        if n_fail > 0 and verbose:
            errors = [r for r in raw_results if "error" in r][:3]
            for r in errors:
                _cprint(f"  [erreur] {r['error']}", (255, 80, 80))
                if "detail" in r and n_ok == 0:
                    print(r["detail"][:600])

        return self._aggregate(raw_results, samples)

    # ── internal ─────────────────────────────────────────────────────────────

    def _validate_one(self, sample: Dict[str, float]) -> None:
        """Instantiate one model to catch parameter errors before full run."""
        try:
            all_params = {**self.fixed, **sample}
            self.param_class(**all_params)
        except Exception as e:
            raise ValueError(
                f"Parameter validation failed for sample {sample}: {e}"
            )

    # ── Progress helpers ─────────────────────────────────────────────────────

    def _execute_with_progress(
        self, samples: List[Dict], verbose: bool
    ) -> List[Dict]:
        """Run all models with a coloured gradient progress bar."""
        n = len(samples)

        if not verbose:
            return self._execute(samples)

        # Gradient colours teal → violet → rose
        _GRAD = [
            (0, 210, 190), (0, 180, 255),
            (100, 120, 255), (200, 60, 220), (240, 80, 160),
        ]

        def _lerp(a, b, t):
            return int(a + (b - a) * t)

        def _grad_color(pos, total):
            t = pos / max(total - 1, 1)
            n_stops = len(_GRAD) - 1
            i = min(int(t * n_stops), n_stops - 1)
            lt = t * n_stops - i
            r = _lerp(_GRAD[i][0], _GRAD[i+1][0], lt)
            g = _lerp(_GRAD[i][1], _GRAD[i+1][1], lt)
            b = _lerp(_GRAD[i][2], _GRAD[i+1][2], lt)
            return r, g, b

        def _rgb(r, g, b, text):
            return f"\033[38;2;{r};{g};{b}m{text}\033[0m"

        def _bold(text):
            return f"\033[1m{text}\033[0m"

        bar_width = 36
        label     = "EpiTools · Monte Carlo"

        def _draw(done, total, n_ok, n_fail):
            frac   = done / max(total, 1)
            filled = int(frac * bar_width)
            bar    = ""
            for i in range(bar_width):
                r, g, b = _grad_color(i, bar_width)
                char = "█" if i < filled else "░"
                bar += _rgb(r, g, b, char)

            r0, g0, b0 = _grad_color(filled, bar_width)
            pct  = _rgb(r0, g0, b0, f"{frac*100:5.1f}%")
            stat = f"  {done}/{total}"
            if n_fail:
                stat += f"  \033[38;2;255;80;80m✗ {n_fail}\033[0m"

            line = f"  {_bold(label)}  {bar} {pct}{stat}"
            print(f"\r{line}", end="", flush=True)

        results = []
        n_ok = n_fail = 0

        args_list = [
            (self.model_class, self.param_class,
             self.fixed, s, self.t_eval_points)
            for s in samples
        ]

        print()  # newline before bar
        for i, args in enumerate(args_list):
            r = _run_one(args)
            results.append(r)
            if "error" in r:
                n_fail += 1
            else:
                n_ok += 1
            _draw(i + 1, n, n_ok, n_fail)

        r0, g0, b0 = _grad_color(bar_width - 1, bar_width)
        done_text  = _rgb(r0, g0, b0, "✓ done")
        print(f"  {done_text}  {n_ok}/{n} OK\n", flush=True)

        return results

    def _execute(self, samples: List[Dict]) -> List[Dict]:
        """Run all models  sequential (n_jobs=1) or parallel."""
        args_list = [
            (self.model_class, self.param_class,
             self.fixed, s, self.t_eval_points)
            for s in samples
        ]

        if self.n_jobs == 1:
            return [_run_one(a) for a in args_list]

        # Parallel  fallback to sequential on error
        try:
            workers = (
                self.n_jobs if self.n_jobs > 0
                else __import__("os").cpu_count()
            )
            results = [None] * len(args_list)
            with ProcessPoolExecutor(max_workers=workers) as ex:
                future_to_idx = {
                    ex.submit(_run_one, a): i
                    for i, a in enumerate(args_list)
                }
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        results[idx] = future.result()
                    except Exception as e:
                        results[idx] = {"error": str(e),
                                        "params": samples[idx]}
            return results
        except Exception:
            warnings.warn(
                "Parallel execution failed, falling back to sequential.",
                RuntimeWarning,
            )
            return [_run_one(a) for a in args_list]

    def _aggregate(
        self,
        raw: List[Dict],
        samples: List[Dict],
    ) -> SensitivityResult:
        """Build SensitivityResult from list of raw run dicts."""
        good    = [r for r in raw if "error" not in r]
        n_fail  = len(raw) - len(good)

        if not good:
            raise RuntimeError(
                f"All {len(raw)} model runs failed. "
                f"Check your parameter distributions and fixed params."
            )

        # Common time array  use first successful run's t
        t_ref = good[0]["t"]

        # Interpolate all trajectories onto t_ref
        comp_names = list(good[0]["compartments"].keys())
        all_traj: Dict[str, List[np.ndarray]] = {c: [] for c in comp_names}

        for run in good:
            t_run = run["t"]
            for c in comp_names:
                interp = np.interp(t_ref, t_run, run["compartments"][c])
                all_traj[c].append(interp)

        # Percentile envelopes
        percentiles = [5, 25, 50, 75, 95]
        envelopes: Dict[str, Dict[str, np.ndarray]] = {}
        for c in comp_names:
            stack = np.vstack(all_traj[c])   # (n_good, n_timepoints)
            envelopes[c] = {
                f"p{p}": np.percentile(stack, p, axis=0)
                for p in percentiles
            }

        # Scalar metrics
        metrics: Dict[str, np.ndarray] = {
            "r0":            np.array([r["r0"]            for r in good
                                       if r.get("r0") is not None]),
            "peak_infected": np.array([r["peak_infected"] for r in good
                                       if r.get("peak_infected") is not None]),
            "peak_time":     np.array([r["peak_time"]     for r in good
                                       if r.get("peak_time") is not None]),
            "final_size":    np.array([r["final_size"]    for r in good
                                       if r.get("final_size") is not None]),
        }

        # Param samples that succeeded
        good_param_samples = [r["params"] for r in good]

        return SensitivityResult(
            t=t_ref,
            envelopes=envelopes,
            metrics=metrics,
            n_samples=len(good),
            n_failed=n_fail,
            param_samples=good_param_samples,
            compartment_names=comp_names,
        )


__all__ = ["SensitivityAnalysis", "SensitivityResult"]
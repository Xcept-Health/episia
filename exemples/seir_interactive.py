"""
seir_interactive.py  SEIR visualization avec contrôles temps réel.

Script autonome (matplotlib). Aucune dépendance externe hormis numpy et matplotlib.

Usage
-----
    python seir_interactive.py

Contrôles
---------
    Sliders    : N, I0, E0, beta, sigma, gamma, mu (SEIRD), durée
    Boutons    : SIR / SEIR / SEIRD, Reset, Animate (play frame par frame)
    Clavier    : [Espace] play/pause  [R] reset  [S] sauvegarder PNG
"""

import sys
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Slider, Button, RadioButtons
from matplotlib.animation import FuncAnimation
from scipy.integrate import solve_ivp

matplotlib.use("TkAgg")   # fenêtre native ; remplace par "Qt5Agg" si TkAgg absent


# ─────────────────────────────────────────────────────────────────────────────
# ODE systems
# ─────────────────────────────────────────────────────────────────────────────

def sir_ode(t, y, N, beta, gamma):
    S, I, R = y
    foi = beta * S * I / N
    return [-foi, foi - gamma * I, gamma * I]


def seir_ode(t, y, N, beta, sigma, gamma):
    S, E, I, R = y
    foi = beta * S * I / N
    return [-foi, foi - sigma * E, sigma * E - gamma * I, gamma * I]


def seird_ode(t, y, N, beta, sigma, gamma, mu):
    S, E, I, R, D = y
    foi = beta * S * I / N
    return [-foi, foi - sigma * E, sigma * E - (gamma + mu) * I,
            gamma * I, mu * I]


def run_model(model, N, I0, E0, beta, sigma, gamma, mu, t_end):
    """Solve ODE and return (t, compartment_arrays) dict."""
    t_span = (0.0, t_end)
    t_eval = np.linspace(0, t_end, max(500, int(t_end * 5)))
    N = float(N)
    S0 = N - I0 - E0
    R0_init = 0.0
    D0 = 0.0

    try:
        if model == "SIR":
            y0  = [S0, I0, R0_init]
            sol = solve_ivp(sir_ode, t_span, y0, t_eval=t_eval,
                            args=(N, beta, gamma), rtol=1e-6, atol=1e-8)
            if not sol.success:
                return None
            S, I, R = np.clip(sol.y, 0, None)
            return dict(t=sol.t, S=S, I=I, R=R)

        elif model == "SEIR":
            y0  = [S0, E0, I0, R0_init]
            sol = solve_ivp(seir_ode, t_span, y0, t_eval=t_eval,
                            args=(N, beta, sigma, gamma), rtol=1e-6, atol=1e-8)
            if not sol.success:
                return None
            S, E, I, R = np.clip(sol.y, 0, None)
            return dict(t=sol.t, S=S, E=E, I=I, R=R)

        else:  # SEIRD
            y0  = [S0, E0, I0, R0_init, D0]
            sol = solve_ivp(seird_ode, t_span, y0, t_eval=t_eval,
                            args=(N, beta, sigma, gamma, mu), rtol=1e-6, atol=1e-8)
            if not sol.success:
                return None
            S, E, I, R, D = np.clip(sol.y, 0, None)
            return dict(t=sol.t, S=S, E=E, I=I, R=R, D=D)

    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Colour palette
# ─────────────────────────────────────────────────────────────────────────────

COLORS = {
    "S": "#1f77b4",   # blue
    "E": "#ff7f0e",   # orange
    "I": "#d62728",   # red
    "R": "#2ca02c",   # green
    "D": "#7f7f7f",   # grey
}

LABELS = {"S": "Susceptible", "E": "Exposed",
          "I": "Infectious",  "R": "Recovered", "D": "Deaths"}


# ─────────────────────────────────────────────────────────────────────────────
# App state
# ─────────────────────────────────────────────────────────────────────────────

class SEIRApp:
    def __init__(self):
        self.model    = "SEIR"
        self.animating = False
        self.anim_obj  = None
        self._data     = None

        self._build_figure()
        self._connect_events()
        self._update()

    # ── Figure layout ──────────────────────────────────────────────────────

    def _build_figure(self):
        self.fig = plt.figure(figsize=(15, 8), facecolor="#f5f5f5")
        self.fig.canvas.manager.set_window_title("EpiTools  SEIR Interactive")

        gs = gridspec.GridSpec(
            2, 2,
            left=0.30, right=0.97,
            top=0.93,  bottom=0.08,
            hspace=0.38, wspace=0.28,
        )

        # Main trajectory plot
        self.ax_main  = self.fig.add_subplot(gs[0, :])
        # Phase portrait S vs I
        self.ax_phase = self.fig.add_subplot(gs[1, 0])
        # Daily new infections
        self.ax_daily = self.fig.add_subplot(gs[1, 1])

        self.ax_main.set_facecolor("white")
        self.ax_phase.set_facecolor("white")
        self.ax_daily.set_facecolor("white")

        self._build_sliders()
        self._build_buttons()
        self._build_annotation_box()

    def _build_sliders(self):
        """Left panel  parameter sliders."""
        slider_color = "#e8e8f0"
        left   = 0.04
        width  = 0.18
        height = 0.025

        specs = [
            # (label, valmin, valmax, valinit, valfmt, attr)
            ("N (pop.)",    1_000,  5_000_000, 1_000_000, "%d",    "sl_N"),
            ("I₀",          1,      10_000,    10,         "%d",    "sl_I0"),
            ("E₀",          0,      10_000,    50,         "%d",    "sl_E0"),
            ("β (transm.)", 0.01,   1.5,       0.35,       "%.3f",  "sl_beta"),
            ("σ (1/incub)", 0.01,   1.0,       1/5.2,      "%.3f",  "sl_sigma"),
            ("γ (1/infect)",0.01,   1.0,       1/14,       "%.3f",  "sl_gamma"),
            ("μ (mortalité)",0.00,  0.30,      0.01,       "%.3f",  "sl_mu"),
            ("Durée (jours)",30,    730,       365,         "%d",    "sl_tend"),
        ]

        n = len(specs)
        tops = np.linspace(0.92, 0.30, n)

        self.sliders = {}
        for (label, vmin, vmax, vinit, fmt, attr), top in zip(specs, tops):
            ax_s = self.fig.add_axes([left, top, width, height],
                                     facecolor=slider_color)
            sl = Slider(ax_s, label, vmin, vmax, valinit=vinit,
                        valfmt=fmt, color="#6a89cc")
            sl.label.set_fontsize(8)
            sl.valtext.set_fontsize(8)
            sl.on_changed(self._on_slider)
            setattr(self, attr, sl)
            self.sliders[attr] = sl

        # Reset button
        ax_reset = self.fig.add_axes([left, 0.22, width, 0.035])
        self.btn_reset = Button(ax_reset, "Reset", color="#dde3f0",
                                hovercolor="#bbc8e8")
        self.btn_reset.label.set_fontsize(9)
        self.btn_reset.on_clicked(self._on_reset)

        # Animate button
        ax_anim = self.fig.add_axes([left, 0.16, width, 0.035])
        self.btn_anim = Button(ax_anim, "Animate", color="#d0eddb",
                               hovercolor="#a8dab5")
        self.btn_anim.label.set_fontsize(9)
        self.btn_anim.on_clicked(self._on_animate)

        # Save button
        ax_save = self.fig.add_axes([left, 0.10, width, 0.035])
        self.btn_save = Button(ax_save, "Sauvegarder PNG", color="#fde8cc",
                               hovercolor="#fbd0a0")
        self.btn_save.label.set_fontsize(9)
        self.btn_save.on_clicked(self._on_save)

    def _build_buttons(self):
        """Model selector."""
        ax_radio = self.fig.add_axes([0.04, 0.03, 0.18, 0.07],
                                     facecolor="#f0f0f8")
        self.radio = RadioButtons(ax_radio, ("SIR", "SEIR", "SEIRD"),
                                  active=1, activecolor="#6a89cc")
        for label in self.radio.labels:
            label.set_fontsize(9)
        self.radio.on_clicked(self._on_model_change)

    def _build_annotation_box(self):
        """Text box  key metrics."""
        self.info_text = self.fig.text(
            0.04, 0.26, "",
            fontsize=8.5,
            family="monospace",
            verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                      edgecolor="#cccccc", alpha=0.9),
        )

    # ── Callbacks ──────────────────────────────────────────────────────────

    def _on_slider(self, _val):
        self._stop_animation()
        self._update()

    def _on_model_change(self, label):
        self.model = label
        self._stop_animation()
        self._update()

    def _on_reset(self, _event):
        self._stop_animation()
        defaults = {
            "sl_N": 1_000_000, "sl_I0": 10,   "sl_E0": 50,
            "sl_beta": 0.35,   "sl_sigma": 1/5.2, "sl_gamma": 1/14,
            "sl_mu": 0.01,     "sl_tend": 365,
        }
        for attr, val in defaults.items():
            getattr(self, attr).set_val(val)

    def _on_animate(self, _event):
        if self.animating:
            self._stop_animation()
        else:
            self._start_animation()

    def _on_save(self, _event):
        fname = "seir_snapshot.png"
        self.fig.savefig(fname, dpi=150, bbox_inches="tight",
                         facecolor=self.fig.get_facecolor())
        print(f"Saved → {fname}")

    # ── Params accessors ───────────────────────────────────────────────────

    def _params(self):
        return dict(
            N     = int(self.sl_N.val),
            I0    = max(1, int(self.sl_I0.val)),
            E0    = int(self.sl_E0.val),
            beta  = self.sl_beta.val,
            sigma = self.sl_sigma.val,
            gamma = self.sl_gamma.val,
            mu    = self.sl_mu.val,
            t_end = int(self.sl_tend.val),
        )

    # ── Core update ────────────────────────────────────────────────────────

    def _update(self, frame=None):
        p = self._params()
        data = run_model(self.model, **p)
        if data is None:
            return
        self._data = data
        self._draw_all(data, p, frame=frame)
        self.fig.canvas.draw_idle()

    def _draw_all(self, data, p, frame=None):
        t = data["t"]
        N = float(p["N"])

        # Animate frame slice
        if frame is not None and self.animating:
            n_total = len(t)
            n_frames = 120
            idx = max(2, int((frame + 1) / n_frames * n_total))
            t_plot = {k: v[:idx] for k, v in data.items()}
        else:
            t_plot = data
            idx = len(t)

        t_arr = t_plot["t"]

        # ── Main plot ──
        self.ax_main.clear()
        self.ax_main.set_facecolor("white")
        compartments = [c for c in ["S", "E", "I", "R", "D"]
                        if c in t_plot]
        for c in compartments:
            self.ax_main.plot(t_arr, t_plot[c],
                              color=COLORS[c], linewidth=2.2,
                              label=LABELS[c])
        self.ax_main.set_xlim(0, p["t_end"])
        self.ax_main.set_ylim(0, N * 1.05)
        self.ax_main.set_xlabel("Jours", fontsize=10)
        self.ax_main.set_ylabel("Individus", fontsize=10)
        self.ax_main.set_title(
            f"Modèle {self.model}    N={N:,.0f}",
            fontsize=12, fontweight="bold"
        )
        self.ax_main.legend(loc="center right", fontsize=9,
                            framealpha=0.85)
        self.ax_main.grid(True, alpha=0.3, linestyle="--")
        self.ax_main.spines[["top", "right"]].set_visible(False)

        # ── Phase portrait ──
        self.ax_phase.clear()
        self.ax_phase.set_facecolor("white")
        if "S" in t_plot and "I" in t_plot:
            sc = t_plot["S"] / N
            ic = t_plot["I"] / N
            # Colour gradient along time
            n_seg = len(sc) - 1
            if n_seg > 1:
                for j in range(n_seg):
                    alpha = 0.4 + 0.6 * j / n_seg
                    self.ax_phase.plot(sc[j:j+2], ic[j:j+2],
                                       color=COLORS["I"], alpha=alpha,
                                       linewidth=1.5)
            self.ax_phase.plot(sc[0], ic[0], "o", color="#333333",
                               markersize=7, label="t=0", zorder=5)
            if len(sc) > 1:
                self.ax_phase.plot(sc[-1], ic[-1], "s",
                                   color=COLORS["R"], markersize=7,
                                   label=f"t={t_arr[-1]:.0f}", zorder=5)
        self.ax_phase.set_xlabel("S / N", fontsize=9)
        self.ax_phase.set_ylabel("I / N", fontsize=9)
        self.ax_phase.set_title("Portrait de phase  S vs I", fontsize=10,
                                fontweight="bold")
        self.ax_phase.legend(fontsize=8)
        self.ax_phase.grid(True, alpha=0.3, linestyle="--")
        self.ax_phase.spines[["top", "right"]].set_visible(False)

        # ── Daily incidence ──
        self.ax_daily.clear()
        self.ax_daily.set_facecolor("white")
        if "R" in t_plot and len(t_arr) > 1:
            # Proxy for daily incidence: dR/dt + dD/dt
            recovered = t_plot["R"]
            deaths    = t_plot.get("D", np.zeros_like(recovered))
            removed   = recovered + deaths
            dt        = np.diff(t_arr)
            daily     = np.diff(removed) / dt
            daily     = np.clip(daily, 0, None)
            self.ax_daily.fill_between(t_arr[1:], daily, alpha=0.4,
                                       color=COLORS["I"])
            self.ax_daily.plot(t_arr[1:], daily, color=COLORS["I"],
                               linewidth=1.5)
        self.ax_daily.set_xlabel("Jours", fontsize=9)
        self.ax_daily.set_ylabel("Cas / jour", fontsize=9)
        self.ax_daily.set_title("Incidence journalière", fontsize=10,
                                fontweight="bold")
        self.ax_daily.grid(True, alpha=0.3, linestyle="--")
        self.ax_daily.spines[["top", "right"]].set_visible(False)

        # ── Metrics box ──
        r0 = p["beta"] / (p["gamma"] + (p["mu"] if self.model == "SEIRD"
                                          else 0))
        hit = max(0.0, 1 - 1 / r0) if r0 > 1 else 0.0
        peak_I = float(data["I"].max())
        peak_t = float(data["t"][np.argmax(data["I"])])
        final_R = float(data["R"][-1]) / N
        total_D = float(data.get("D", np.zeros(1))[-1])

        lines = [
            f"R₀        = {r0:.2f}",
            f"Seuil IH  = {hit:.1%}",
            f"Pic infect. = {peak_I:,.0f}",
            f"Pic (jour)  = {peak_t:.0f}",
            f"Taille finale = {final_R:.1%}",
        ]
        if self.model == "SEIRD":
            cfr = p["mu"] / (p["gamma"] + p["mu"])
            lines += [
                f"CFR       = {cfr:.1%}",
                f"Décès tot.  = {total_D:,.0f}",
            ]
        if self.model in ("SEIR", "SEIRD"):
            lines.append(f"Incubation  = {1/p['sigma']:.1f}j")
        lines.append(f"Infectieux  = {1/p['gamma']:.1f}j")

        self.info_text.set_text("\n".join(lines))

    # ── Animation ──────────────────────────────────────────────────────────

    def _start_animation(self):
        self.animating = True
        self.btn_anim.label.set_text("Stop")
        self.btn_anim.color = "#f5c6c6"

        n_frames = 120
        self.anim_obj = FuncAnimation(
            self.fig,
            self._update,
            frames=range(n_frames),
            interval=30,
            repeat=False,
        )
        self.fig.canvas.draw_idle()

    def _stop_animation(self):
        if self.anim_obj is not None:
            self.anim_obj.event_source.stop()
            self.anim_obj = None
        self.animating = False
        self.btn_anim.label.set_text("Animate")
        self.btn_anim.color = "#d0eddb"

    # ── Keyboard ───────────────────────────────────────────────────────────

    def _connect_events(self):
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)

    def _on_key(self, event):
        if event.key == " ":
            self._on_animate(None)
        elif event.key == "r":
            self._on_reset(None)
        elif event.key == "s":
            self._on_save(None)

    # ── Run ────────────────────────────────────────────────────────────────

    def show(self):
        plt.show()


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("EpiTools  SEIR Interactive")
    print("Sliders : N, I0, E0, β, σ, γ, μ, durée")
    print("Touches : [Espace] play/pause  [R] reset  [S] sauvegarder")
    app = SEIRApp()
    app.show()
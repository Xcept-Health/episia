"""
seir_interactive.py - SEIR interactive visualization powered by Episia.

Usage
-----
    python seir_interactive.py

Controls
--------
    Sliders : N, I0, E0, beta, sigma, gamma, mu, duration
    Buttons : SIR / SEIR / SEIRD, Reset, Animate, Save PNG
    Keys    : [Space] play/pause   [R] reset   [S] save PNG
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Slider, Button, RadioButtons
from matplotlib.animation import FuncAnimation

matplotlib.use("TkAgg")  # replace with "Qt5Agg" if TkAgg is unavailable

from episia.models import SIRModel, SEIRModel, SEIRDModel
from episia.models.parameters import SIRParameters, SEIRParameters, SEIRDParameters


#  Episia model runner 

def run_model(model_name, N, I0, E0, beta, sigma, gamma, mu, t_end):
    """Run the selected compartmental model via Episia and return a data dict."""
    try:
        if model_name == "SIR":
            params = SIRParameters(
                N=N, I0=I0,
                beta=beta, gamma=gamma,
                t_span=(0, t_end),
            )
            result = SIRModel(params).run()
            return dict(t=result.t,
                        S=result.compartments["S"],
                        I=result.compartments["I"],
                        R=result.compartments["R"])

        elif model_name == "SEIR":
            params = SEIRParameters(
                N=N, I0=I0, E0=E0,
                beta=beta, sigma=sigma, gamma=gamma,
                t_span=(0, t_end),
            )
            result = SEIRModel(params).run()
            return dict(t=result.t,
                        S=result.compartments["S"],
                        E=result.compartments["E"],
                        I=result.compartments["I"],
                        R=result.compartments["R"])

        else:  # SEIRD
            params = SEIRDParameters(
                N=N, I0=I0, E0=E0,
                beta=beta, sigma=sigma, gamma=gamma, mu=mu,
                t_span=(0, t_end),
            )
            result = SEIRDModel(params).run()
            return dict(t=result.t,
                        S=result.compartments["S"],
                        E=result.compartments["E"],
                        I=result.compartments["I"],
                        R=result.compartments["R"],
                        D=result.compartments["D"])

    except Exception as e:
        print(f"Model error: {e}")
        return None


#  Colour palette (Episia teal → violet) 

COLORS = {
    "S": "#1D9E75",   # teal     - susceptible
    "E": "#EF9F27",   # amber    - exposed
    "I": "#E24B4A",   # red      - infectious
    "R": "#378ADD",   # blue     - recovered
    "D": "#888780",   # grey     - deaths
}

LABELS = {
    "S": "Susceptible",
    "E": "Exposed",
    "I": "Infectious",
    "R": "Recovered",
    "D": "Deaths",
}


#  App 

class SEIRApp:

    def __init__(self):
        self.model     = "SEIR"
        self.animating = False
        self.anim_obj  = None
        self._data     = None

        self._build_figure()
        self._connect_events()
        self._update()

    #  Figure layout 

    def _build_figure(self):
        self.fig = plt.figure(figsize=(15, 8), facecolor="#f8f8fc")
        self.fig.canvas.manager.set_window_title("Episia - SEIR Interactive")

        gs = gridspec.GridSpec(
            2, 2,
            left=0.30, right=0.97,
            top=0.93,  bottom=0.08,
            hspace=0.38, wspace=0.28,
        )

        self.ax_main  = self.fig.add_subplot(gs[0, :])
        self.ax_phase = self.fig.add_subplot(gs[1, 0])
        self.ax_daily = self.fig.add_subplot(gs[1, 1])

        for ax in (self.ax_main, self.ax_phase, self.ax_daily):
            ax.set_facecolor("white")

        self._build_sliders()
        self._build_buttons()
        self._build_annotation_box()

    def _build_sliders(self):
        slider_color = "#e8e8f0"
        left, width, height = 0.04, 0.18, 0.025

        specs = [
            ("N (pop.)",       1_000,  5_000_000, 1_000_000, "%d",   "sl_N"),
            ("I₀",             1,      10_000,    10,         "%d",   "sl_I0"),
            ("E₀",             0,      10_000,    50,         "%d",   "sl_E0"),
            ("β (transm.)",    0.01,   1.5,       0.35,       "%.3f", "sl_beta"),
            ("σ (1/incub.)",   0.01,   1.0,       1/5.2,      "%.3f", "sl_sigma"),
            ("γ (1/infect.)",  0.01,   1.0,       1/14,       "%.3f", "sl_gamma"),
            ("μ (mortality)",  0.00,   0.30,      0.01,       "%.3f", "sl_mu"),
            ("Duration (days)",30,     730,       365,        "%d",   "sl_tend"),
        ]

        tops = np.linspace(0.92, 0.30, len(specs))
        self.sliders = {}

        for (label, vmin, vmax, vinit, fmt, attr), top in zip(specs, tops):
            ax_s = self.fig.add_axes([left, top, width, height],
                                     facecolor=slider_color)
            sl = Slider(ax_s, label, vmin, vmax, valinit=vinit,
                        valfmt=fmt, color="#1D9E75")
            sl.label.set_fontsize(8)
            sl.valtext.set_fontsize(8)
            sl.on_changed(self._on_slider)
            setattr(self, attr, sl)
            self.sliders[attr] = sl

        # Reset
        ax_reset = self.fig.add_axes([left, 0.22, width, 0.035])
        self.btn_reset = Button(ax_reset, "Reset",
                                color="#dde3f0", hovercolor="#bbc8e8")
        self.btn_reset.label.set_fontsize(9)
        self.btn_reset.on_clicked(self._on_reset)

        # Animate
        ax_anim = self.fig.add_axes([left, 0.16, width, 0.035])
        self.btn_anim = Button(ax_anim, "Animate",
                               color="#d0f0e8", hovercolor="#a8dab5")
        self.btn_anim.label.set_fontsize(9)
        self.btn_anim.on_clicked(self._on_animate)

        # Save
        ax_save = self.fig.add_axes([left, 0.10, width, 0.035])
        self.btn_save = Button(ax_save, "Save PNG",
                               color="#fde8cc", hovercolor="#fbd0a0")
        self.btn_save.label.set_fontsize(9)
        self.btn_save.on_clicked(self._on_save)

    def _build_buttons(self):
        ax_radio = self.fig.add_axes([0.04, 0.03, 0.18, 0.07],
                                     facecolor="#f0f0f8")
        self.radio = RadioButtons(ax_radio, ("SIR", "SEIR", "SEIRD"),
                                  active=1, activecolor="#1D9E75")
        for lbl in self.radio.labels:
            lbl.set_fontsize(9)
        self.radio.on_clicked(self._on_model_change)

    def _build_annotation_box(self):
        self.info_text = self.fig.text(
            0.04, 0.26, "",
            fontsize=8.5,
            family="monospace",
            verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                      edgecolor="#cccccc", alpha=0.9),
        )

    #  Callbacks 

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
            "sl_N": 1_000_000, "sl_I0": 10,    "sl_E0": 50,
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
        fname = "episia_snapshot.png"
        self.fig.savefig(fname, dpi=150, bbox_inches="tight",
                         facecolor=self.fig.get_facecolor())
        print(f"Saved → {fname}")

    #  Params 

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

    #  Core update 

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

        # Frame slice for animation
        if frame is not None and self.animating:
            n_frames = 120
            idx = max(2, int((frame + 1) / n_frames * len(t)))
            t_plot = {k: v[:idx] for k, v in data.items()}
        else:
            t_plot = data

        t_arr = t_plot["t"]

        # Main trajectory 
        self.ax_main.clear()
        self.ax_main.set_facecolor("white")
        for c in [k for k in ["S", "E", "I", "R", "D"] if k in t_plot]:
            self.ax_main.plot(t_arr, t_plot[c],
                              color=COLORS[c], linewidth=2.2,
                              label=LABELS[c])
        self.ax_main.set_xlim(0, p["t_end"])
        self.ax_main.set_ylim(0, N * 1.05)
        self.ax_main.set_xlabel("Days", fontsize=10)
        self.ax_main.set_ylabel("Individuals", fontsize=10)
        self.ax_main.set_title(
            f"{self.model} Model  -  N = {N:,.0f}",
            fontsize=12, fontweight="bold",
        )
        self.ax_main.legend(loc="center right", fontsize=9, framealpha=0.85)
        self.ax_main.grid(True, alpha=0.3, linestyle="--")
        self.ax_main.spines[["top", "right"]].set_visible(False)

        # Phase portrait S vs I 
        self.ax_phase.clear()
        self.ax_phase.set_facecolor("white")
        if "S" in t_plot and "I" in t_plot:
            sc = t_plot["S"] / N
            ic = t_plot["I"] / N
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
        self.ax_phase.set_title("Phase portrait - S vs I", fontsize=10,
                                fontweight="bold")
        self.ax_phase.legend(fontsize=8)
        self.ax_phase.grid(True, alpha=0.3, linestyle="--")
        self.ax_phase.spines[["top", "right"]].set_visible(False)

        # Daily incidence 
        self.ax_daily.clear()
        self.ax_daily.set_facecolor("white")
        if "R" in t_plot and len(t_arr) > 1:
            recovered = t_plot["R"]
            deaths    = t_plot.get("D", np.zeros_like(recovered))
            removed   = recovered + deaths
            dt        = np.diff(t_arr)
            daily     = np.clip(np.diff(removed) / dt, 0, None)
            self.ax_daily.fill_between(t_arr[1:], daily,
                                       alpha=0.35, color=COLORS["I"])
            self.ax_daily.plot(t_arr[1:], daily,
                               color=COLORS["I"], linewidth=1.5)
        self.ax_daily.set_xlabel("Days", fontsize=9)
        self.ax_daily.set_ylabel("Cases / day", fontsize=9)
        self.ax_daily.set_title("Daily incidence", fontsize=10,
                                fontweight="bold")
        self.ax_daily.grid(True, alpha=0.3, linestyle="--")
        self.ax_daily.spines[["top", "right"]].set_visible(False)

        # Metrics box 
        denom = p["gamma"] + (p["mu"] if self.model == "SEIRD" else 0)
        r0    = p["beta"] / denom if denom > 0 else 0
        hit   = max(0.0, 1 - 1 / r0) if r0 > 1 else 0.0
        peak_I = float(data["I"].max())
        peak_t = float(data["t"][np.argmax(data["I"])])
        final_R = float(data["R"][-1]) / N
        total_D = float(data.get("D", np.zeros(1))[-1])

        lines = [
            f"R₀            = {r0:.2f}",
            f"Herd immunity = {hit:.1%}",
            f"Peak infected = {peak_I:,.0f}",
            f"Peak (day)    = {peak_t:.0f}",
            f"Final size    = {final_R:.1%}",
        ]
        if self.model == "SEIRD":
            cfr = p["mu"] / (p["gamma"] + p["mu"])
            lines += [
                f"CFR           = {cfr:.1%}",
                f"Total deaths  = {total_D:,.0f}",
            ]
        if self.model in ("SEIR", "SEIRD"):
            lines.append(f"Incubation    = {1/p['sigma']:.1f} days")
        lines.append(f"Infectious    = {1/p['gamma']:.1f} days")

        self.info_text.set_text("\n".join(lines))

    #  Animation 

    def _start_animation(self):
        self.animating = True
        self.btn_anim.label.set_text("Stop")
        self.btn_anim.color = "#f5c6c6"
        self.anim_obj = FuncAnimation(
            self.fig, self._update,
            frames=range(120), interval=30, repeat=False,
        )
        self.fig.canvas.draw_idle()

    def _stop_animation(self):
        if self.anim_obj is not None:
            self.anim_obj.event_source.stop()
            self.anim_obj = None
        self.animating = False
        self.btn_anim.label.set_text("Animate")
        self.btn_anim.color = "#d0f0e8"

    #  Keyboard 

    def _connect_events(self):
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)

    def _on_key(self, event):
        if event.key == " ":
            self._on_animate(None)
        elif event.key == "r":
            self._on_reset(None)
        elif event.key == "s":
            self._on_save(None)

    #  Run 

    def show(self):
        plt.show()


#  Entry point 

if __name__ == "__main__":
    print("Episia - SEIR Interactive")
    print("Sliders : N, I0, E0, β, σ, γ, μ, duration")
    print("Keys    : [Space] play/pause   [R] reset   [S] save PNG")
    SEIRApp().show()
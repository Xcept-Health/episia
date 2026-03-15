"""
viz/plotters/base_plotter.py - Abstract base class for all EpiTools plotters.

Defines the contract every rendering backend (Plotly, Matplotlib, Browser)
must satisfy. Also declares the AnimationConfig dataclass used to request
animations wherever they make sense (epidemic curves, model simulations,
time-series, ROC sweep).

Design principles:
    - Backends are interchangeable: same call, different engine.
    - Animations are opt-in via AnimationConfig; backends that do not
      support a given animation type raise UnsupportedAnimationError.
    - Every plot method returns a native figure object so callers can
      post-process (add annotations, save, embed in a dashboard…).
    - Themes are resolved here so backends only handle rendering.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union



# Animation support

class AnimationType(Enum):
    """
    Animation types supported across backends.

    FRAME_BY_FRAME   discrete frames (e.g. day-by-day epidemic curve buildup).
    CONTINUOUS       smooth interpolated transition (e.g. model trajectory).
    SLIDER           interactive parameter slider (Plotly only).
    PLAY_PAUSE       auto-play with play/pause button (Plotly / Browser).
    LOOP             continuous loop, no controls (Matplotlib FuncAnimation).
    """
    FRAME_BY_FRAME = "frame_by_frame"
    CONTINUOUS     = "continuous"
    SLIDER         = "slider"
    PLAY_PAUSE     = "play_pause"
    LOOP           = "loop"


@dataclass
class AnimationConfig:
    """
    Configuration for animated plots.

    Attributes:
        enabled:       Whether animation is active.
        anim_type:     AnimationType  how frames are driven.
        duration_ms:   Total animation duration in milliseconds.
        frame_ms:      Duration of each frame in milliseconds.
        transition_ms: Transition time between frames (Plotly).
        loop:          Whether the animation loops automatically.
        show_controls: Show play/pause/slider controls in the output.
        easing:        CSS/Plotly easing function for transitions.
        fps:           Frames per second (Matplotlib backend).
    """
    enabled:       bool          = False
    anim_type:     AnimationType = AnimationType.PLAY_PAUSE
    duration_ms:   int           = 3000
    frame_ms:      int           = 50
    transition_ms: int           = 30
    loop:          bool          = True
    show_controls: bool          = True
    easing:        str           = "cubic-in-out"
    fps:           int           = 25

    @classmethod
    def default(cls) -> "AnimationConfig":
        """Return a sensible default config (disabled)."""
        return cls(enabled=False)

    @classmethod
    def smooth(cls, duration_ms: int = 4000) -> "AnimationConfig":
        """Smooth continuous animation  good for model trajectories."""
        return cls(
            enabled=True,
            anim_type=AnimationType.CONTINUOUS,
            duration_ms=duration_ms,
            frame_ms=40,
            transition_ms=20,
            loop=True,
            easing="cubic-in-out",
        )

    @classmethod
    def frame_buildup(cls, n_frames: int, total_ms: int = 5000) -> "AnimationConfig":
        """Frame-by-frame buildup  good for epidemic curves / time-series."""
        frame_ms = max(20, total_ms // max(n_frames, 1))
        return cls(
            enabled=True,
            anim_type=AnimationType.FRAME_BY_FRAME,
            duration_ms=total_ms,
            frame_ms=frame_ms,
            transition_ms=10,
            loop=False,
            easing="linear",
        )

    @classmethod
    def interactive_slider(cls) -> "AnimationConfig":
        """Interactive parameter slider  Plotly only."""
        return cls(
            enabled=True,
            anim_type=AnimationType.SLIDER,
            show_controls=True,
        )


class UnsupportedAnimationError(NotImplementedError):
    """Raised when a backend does not support the requested animation type."""
    pass



# Plot configuration

@dataclass
class PlotConfig:
    """
    Unified plot configuration passed to every plot method.

    Attributes:
        title:        Figure title.
        subtitle:     Optional subtitle (rendered below title).
        xlabel:       X-axis label.
        ylabel:       Y-axis label.
        width:        Figure width in pixels (Plotly) or inches (Matplotlib).
        height:       Figure height in pixels (Plotly) or inches (Matplotlib).
        theme:        Theme name  'scientific', 'minimal', 'dark', 'colorblind'.
        palette:      List of hex color strings to use in sequence.
        show_grid:    Whether to show grid lines.
        show_legend:  Whether to show the legend.
        font_size:    Base font size.
        confidence:   Confidence level for CI bands (e.g. 0.95).
        animation:    AnimationConfig object.
        extra:        Backend-specific kwargs forwarded as-is.
    """
    title:       str                      = ""
    subtitle:    str                      = ""
    xlabel:      str                      = ""
    ylabel:      str                      = ""
    width:       int                      = 800
    height:      int                      = 500
    theme:       str                      = "scientific"
    palette:     Optional[List[str]]      = None
    show_grid:   bool                     = True
    show_legend: bool                     = True
    font_size:   int                      = 13
    confidence:  float                    = 0.95
    animation:   AnimationConfig          = field(default_factory=AnimationConfig.default)
    extra:       Dict[str, Any]           = field(default_factory=dict)

    @classmethod
    def minimal(cls, title: str = "", **kwargs) -> "PlotConfig":
        return cls(title=title, theme="minimal", show_grid=False, **kwargs)

    @classmethod
    def dark(cls, title: str = "", **kwargs) -> "PlotConfig":
        return cls(title=title, theme="dark", **kwargs)

    @classmethod
    def publication(cls, title: str = "", **kwargs) -> "PlotConfig":
        """Suitable for paper figures  no grid, serif fonts, high contrast."""
        return cls(
            title=title,
            theme="scientific",
            show_grid=False,
            font_size=11,
            width=700,
            height=450,
            **kwargs,
        )



# Output type

class OutputFormat(Enum):
    """Output format when saving or exporting a figure."""
    PNG    = "png"
    SVG    = "svg"
    PDF    = "pdf"
    HTML   = "html"
    JSON   = "json"   # Plotly only  serialised figure dict
    GIF    = "gif"    # Animated  Matplotlib only
    MP4    = "mp4"    # Animated  requires ffmpeg



# Abstract base plotter

class BasePlotter(ABC):
    """
    Abstract base class for EpiTools rendering backends.

    Subclasses implement each plot_* method for their engine.
    The constructor accepts a PlotConfig that sets defaults for
    every figure produced by this instance.

    Usage::

        plotter = PlotlyPlotter(config=PlotConfig(theme="dark"))
        fig = plotter.plot_epicurve(result, config=PlotConfig(title="Ebola 2014"))
    """

    #: Human-readable backend name used in error messages.
    BACKEND_NAME: str = "base"

    #: AnimationTypes this backend can handle.
    SUPPORTED_ANIMATIONS: Tuple[AnimationType, ...] = ()

    def __init__(self, config: Optional[PlotConfig] = None):
        self.default_config = config or PlotConfig()

    #  helpers

    def _resolve_config(self, override: Optional[PlotConfig]) -> PlotConfig:
        """Merge per-call override with instance defaults."""
        if override is None:
            return self.default_config
        # override wins for every non-default field
        return override

    def _check_animation(self, config: PlotConfig) -> None:
        """
        Raise UnsupportedAnimationError if the requested animation type
        is not supported by this backend.
        """
        if not config.animation.enabled:
            return
        atype = config.animation.anim_type
        if atype not in self.SUPPORTED_ANIMATIONS:
            raise UnsupportedAnimationError(
                f"Backend '{self.BACKEND_NAME}' does not support "
                f"AnimationType.{atype.value}. "
                f"Supported: {[a.value for a in self.SUPPORTED_ANIMATIONS]}"
            )

    #  abstract plot methods

    @abstractmethod
    def plot_epicurve(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        Plot an epidemic curve (cases over time).

        Supports animations:
            FRAME_BY_FRAME  bars build up day by day.
            PLAY_PAUSE      auto-play buildup with controls.

        Args:
            result: TimeSeriesResult from stats.time_series.
            config: Per-call PlotConfig.

        Returns:
            Native figure object.
        """
        ...

    @abstractmethod
    def plot_model(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        Plot compartmental model trajectories (SIR / SEIR / SEIRD).

        Supports animations:
            CONTINUOUS   smooth line drawing from t=0 to t=end.
            PLAY_PAUSE   play/pause controls over time axis.
            SLIDER       interactive time slider (Plotly only).

        Args:
            result: ModelResult from models.sir / seir / seird.
            config: Per-call PlotConfig.

        Returns:
            Native figure object.
        """
        ...

    @abstractmethod
    def plot_roc(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        Plot ROC curve with AUC annotation.

        Supports animations:
            CONTINUOUS  threshold sweeps from 0 to 1, tracing the curve.

        Args:
            result: ROCResult from stats.diagnostic.
            config: Per-call PlotConfig.

        Returns:
            Native figure object.
        """
        ...

    @abstractmethod
    def plot_forest(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        Plot forest plot for stratified or regression results.

        Supports animations:
            FRAME_BY_FRAME  strata / variables appear one by one.

        Args:
            result: StratifiedResult or RegressionResult.
            config: Per-call PlotConfig.

        Returns:
            Native figure object.
        """
        ...

    @abstractmethod
    def plot_association(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        Plot a single association measure (RR / OR / RD) with CI.

        No animation  static by design.

        Args:
            result: AssociationResult.
            config: Per-call PlotConfig.

        Returns:
            Native figure object.
        """
        ...

    @abstractmethod
    def plot_diagnostic(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        Plot diagnostic test performance dashboard
        (confusion matrix + metrics bar chart).

        Supports animations:
            FRAME_BY_FRAME  metrics bars fill in sequence.

        Args:
            result: DiagnosticResult.
            config: Per-call PlotConfig.

        Returns:
            Native figure object.
        """
        ...

    @abstractmethod
    def plot_contingency(
        self,
        result: Any,
        config: Optional[PlotConfig] = None,
    ) -> Any:
        """
        Plot 2x2 contingency table with annotated cells and risk summary.

        No animation  static by design.

        Args:
            result: Table2x2 or AssociationResult with table metadata.
            config: Per-call PlotConfig.

        Returns:
            Native figure object.
        """
        ...

    #  optional: save

    def save(
        self,
        fig: Any,
        path: str,
        fmt: OutputFormat = OutputFormat.PNG,
        dpi: int = 150,
    ) -> str:
        """
        Save a figure to disk.

        Default implementation raises NotImplementedError.
        Subclasses override as needed.

        Args:
            fig:  Native figure object returned by a plot_* method.
            path: Destination file path (extension appended if missing).
            fmt:  OutputFormat enum value.
            dpi:  Resolution for raster formats.

        Returns:
            Absolute path to the saved file.
        """
        raise NotImplementedError(
            f"Backend '{self.BACKEND_NAME}' does not implement save()."
        )

    #  repr

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"theme={self.default_config.theme!r}, "
            f"backend={self.BACKEND_NAME!r})"
        )



# Exports


__all__ = [
    "AnimationType",
    "AnimationConfig",
    "UnsupportedAnimationError",
    "PlotConfig",
    "OutputFormat",
    "BasePlotter",
]
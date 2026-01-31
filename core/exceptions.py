"""
This module defines custom exception classes for specific error
conditions in epidemiological analysis.
"""


class EpiToolsError(Exception):
    """Base exception for all EpiTools errors."""
    
    def __init__(self, message: str = "An error occurred in EpiTools"):
        self.message = message
        super().__init__(self.message)


class ValidationError(EpiToolsError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str = "Data validation failed"):
        super().__init__(message)


class ConvergenceError(EpiToolsError):
    """Raised when numerical algorithm fails to converge."""
    
    def __init__(self, message: str = "Algorithm failed to converge"):
        super().__init__(message)


class ConfigurationError(EpiToolsError):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str = "Invalid configuration"):
        super().__init__(message)


class DataError(EpiToolsError):
    """Raised when data is invalid or insufficient."""
    
    def __init__(self, message: str = "Invalid or insufficient data"):
        super().__init__(message)


class ModelError(EpiToolsError):
    """Raised when model fitting or evaluation fails."""
    
    def __init__(self, message: str = "Model error occurred"):
        super().__init__(message)


class StatisticalError(EpiToolsError):
    """Raised when statistical assumptions are violated."""
    
    def __init__(self, message: str = "Statistical assumption violated"):
        super().__init__(message)


class DimensionError(EpiToolsError):
    """Raised when array dimensions are incompatible."""
    
    def __init__(self, message: str = "Dimension mismatch"):
        super().__init__(message)


class ParameterError(EpiToolsError):
    """Raised when function parameters are invalid."""
    
    def __init__(self, message: str = "Invalid parameter value"):
        super().__init__(message)


class ComputationError(EpiToolsError):
    """Raised when numerical computation fails."""
    
    def __init__(self, message: str = "Numerical computation failed"):
        super().__init__(message)


class FileError(EpiToolsError):
    """Raised when file operations fail."""
    
    def __init__(self, message: str = "File operation failed"):
        super().__init__(message)


class PlotError(EpiToolsError):
    """Raised when plotting fails."""
    
    def __init__(self, message: str = "Plotting failed"):
        super().__init__(message)


class WarningManager:
    """
    Manager for warnings in EpiTools.
    
    Provides consistent warning formatting and filtering.
    """
    
    @staticmethod
    def warn(
        message: str,
        warning_type: type = UserWarning,
        stacklevel: int = 2
    ) -> None:
        """
        Issue a warning with consistent formatting.
        
        Args:
            message: Warning message
            warning_type: Type of warning
            stacklevel: Stack level for warning origin
        """
        import warnings
        warnings.warn(f"[EpiTools] {message}", warning_type, stacklevel)
    
    @staticmethod
    def filter_warnings(action: str = "default") -> None:
        """
        Set warning filters for EpiTools.
        
        Args:
            action: 'default', 'ignore', or 'error'
        """
        import warnings
        
        if action == "ignore":
            warnings.filterwarnings("ignore", module="epitools")
        elif action == "error":
            warnings.filterwarnings("error", module="epitools")
        elif action == "default":
            # Default filters
            warnings.filterwarnings("once", category=DeprecationWarning, module="epitools")
            warnings.filterwarnings("always", category=RuntimeWarning, module="epitools")
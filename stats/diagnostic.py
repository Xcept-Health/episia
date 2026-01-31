"""
This module provides functions for calculating diagnostic test
performance measures: sensitivity, specificity, predictive values,
likelihood ratios, and ROC curve analysis.
"""

import numpy as np
from typing import Union, Tuple, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
import warnings
from scipy import stats
from sklearn.metrics import roc_curve, auc, precision_recall_curve


class DiagnosticMeasure(Enum):
    """Diagnostic performance measures."""
    SENSITIVITY = "sensitivity"
    SPECIFICITY = "specificity"
    PPV = "ppv"
    NPV = "npv"
    LR_POSITIVE = "lr_positive"
    LR_NEGATIVE = "lr_negative"
    ACCURACY = "accuracy"
    YOUDEN = "youden"


@dataclass
class DiagnosticResult:
    """Rich result object for diagnostic test calculations."""
    tp: int
    fp: int
    fn: int
    tn: int
    
    sensitivity: float
    specificity: float
    ppv: float
    npv: float
    lr_positive: float
    lr_negative: float
    accuracy: float
    youden: float
    
    prevalence: Optional[float] = None
    
    def __repr__(self) -> str:
        return f"Sens: {self.sensitivity:.3f}, Spec: {self.specificity:.3f}, Acc: {self.accuracy:.3f}"
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        return {
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "tn": self.tn,
            "sensitivity": self.sensitivity,
            "specificity": self.specificity,
            "ppv": self.ppv,
            "npv": self.npv,
            "lr_positive": self.lr_positive,
            "lr_negative": self.lr_negative,
            "accuracy": self.accuracy,
            "youden": self.youden,
            "prevalence": self.prevalence
        }
    
    def summary(self) -> str:
        """Generate text summary."""
        return (f"Diagnostic Test Performance:\n"
               f"  Sensitivity: {self.sensitivity:.3f} (95% CI: {self._sens_ci()})\n"
               f"  Specificity: {self.specificity:.3f} (95% CI: {self._spec_ci()})\n"
               f"  PPV: {self.ppv:.3f}, NPV: {self.npv:.3f}\n"
               f"  LR+: {self.lr_positive:.3f}, LR-: {self.lr_negative:.3f}\n"
               f"  Accuracy: {self.accuracy:.3f}, Youden: {self.youden:.3f}")
    
    def _sens_ci(self, confidence: float = 0.95) -> str:
        """Calculate sensitivity CI."""
        from .descriptive import proportion_ci
        ci = proportion_ci(self.tp, self.tp + self.fn, confidence=confidence)
        return f"{ci.ci_lower:.3f}-{ci.ci_upper:.3f}"
    
    def _spec_ci(self, confidence: float = 0.95) -> str:
        """Calculate specificity CI."""
        from .descriptive import proportion_ci
        ci = proportion_ci(self.tn, self.tn + self.fp, confidence=confidence)
        return f"{ci.ci_lower:.3f}-{ci.ci_upper:.3f}"


@dataclass
class ROCResult:
    """Result object for ROC curve analysis."""
    fpr: np.ndarray
    tpr: np.ndarray
    thresholds: np.ndarray
    auc: float
    optimal_threshold: float
    optimal_point: Dict[str, float]
    
    def __repr__(self) -> str:
        return f"AUC: {self.auc:.3f}, Optimal threshold: {self.optimal_threshold:.3f}"
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        return {
            "auc": self.auc,
            "optimal_threshold": self.optimal_threshold,
            "optimal_sensitivity": self.optimal_point.get("sensitivity"),
            "optimal_specificity": self.optimal_point.get("specificity"),
            "optimal_youden": self.optimal_point.get("youden")
        }


def diagnostic_test_2x2(
    tp: int,
    fp: int,
    fn: int,
    tn: int,
    prevalence: Optional[float] = None
) -> DiagnosticResult:
    """
    Calculate diagnostic test performance from 2x2 table.
    
    Args:
        tp: True positives
        fp: False positives
        fn: False negatives
        tn: True negatives
        prevalence: Disease prevalence (for PPV/NPV if different from sample)
        
    Returns:
        DiagnosticResult object
        
    Example:
        >>> result = diagnostic_test_2x2(80, 20, 10, 90)
        >>> print(result.sensitivity)
        0.8889
    """
    # Input validation
    for value, name in [(tp, "tp"), (fp, "fp"), (fn, "fn"), (tn, "tn")]:
        if value < 0:
            raise ValueError(f"{name} must be non-negative")
    
    # Total calculations
    total = tp + fp + fn + tn
    if total == 0:
        raise ValueError("All values cannot be zero")
    
    # Sample prevalence
    sample_prevalence = (tp + fn) / total if total > 0 else 0
    
    # Use provided prevalence or sample prevalence
    prev = prevalence if prevalence is not None else sample_prevalence
    
    # Core diagnostic measures
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    
    # Predictive values
    if prevalence is not None:
        # Use Bayes' theorem with provided prevalence
        ppv = (sensitivity * prev) / (sensitivity * prev + (1 - specificity) * (1 - prev))
        npv = (specificity * (1 - prev)) / (specificity * (1 - prev) + (1 - sensitivity) * prev)
    else:
        # Use sample values
        ppv = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        npv = tn / (tn + fn) if (tn + fn) > 0 else 0.0
    
    # Likelihood ratios
    lr_positive = sensitivity / (1 - specificity) if specificity < 1 else float('inf')
    lr_negative = (1 - sensitivity) / specificity if specificity > 0 else float('inf')
    
    # Overall accuracy
    accuracy = (tp + tn) / total
    
    # Youden's J statistic
    youden = sensitivity + specificity - 1
    
    return DiagnosticResult(
        tp=tp, fp=fp, fn=fn, tn=tn,
        sensitivity=sensitivity,
        specificity=specificity,
        ppv=ppv,
        npv=npv,
        lr_positive=lr_positive,
        lr_negative=lr_negative,
        accuracy=accuracy,
        youden=youden,
        prevalence=prev
    )


def diagnostic_from_data(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    threshold: float = 0.5
) -> DiagnosticResult:
    """
    Calculate diagnostic measures from true labels and predicted scores.
    
    Args:
        y_true: True binary labels (0 or 1)
        y_pred: Predicted scores or probabilities
        threshold: Classification threshold
        
    Returns:
        DiagnosticResult object
    """
    # Convert to binary predictions
    y_pred_binary = (y_pred >= threshold).astype(int)
    
    # Calculate confusion matrix
    tp = np.sum((y_true == 1) & (y_pred_binary == 1))
    fp = np.sum((y_true == 0) & (y_pred_binary == 1))
    fn = np.sum((y_true == 1) & (y_pred_binary == 0))
    tn = np.sum((y_true == 0) & (y_pred_binary == 0))
    
    return diagnostic_test_2x2(tp, fp, fn, tn)


def roc_analysis(
    y_true: np.ndarray,
    y_score: np.ndarray,
    method: str = "youden",
    **kwargs
) -> ROCResult:
    """
    Perform ROC curve analysis.
    
    Args:
        y_true: True binary labels
        y_score: Predicted scores or probabilities
        method: Method for optimal threshold selection:
               'youden' (default), 'closest_topleft', 'max_accuracy'
        
    Returns:
        ROCResult object
    """
    # Calculate ROC curve
    fpr, tpr, thresholds = roc_curve(y_true, y_score, **kwargs)
    roc_auc = auc(fpr, tpr)
    
    # Calculate optimal threshold based on method
    if method == "youden":
        # Youden's J statistic: max(sens + spec - 1)
        youden_index = tpr + (1 - fpr) - 1
        optimal_idx = np.argmax(youden_index)
        optimal_threshold = thresholds[optimal_idx]
        
        optimal_point = {
            "sensitivity": tpr[optimal_idx],
            "specificity": 1 - fpr[optimal_idx],
            "youden": youden_index[optimal_idx]
        }
    
    elif method == "closest_topleft":
        # Point closest to top-left corner (0,1)
        distances = (fpr)**2 + (1 - tpr)**2
        optimal_idx = np.argmin(distances)
        optimal_threshold = thresholds[optimal_idx]
        
        optimal_point = {
            "sensitivity": tpr[optimal_idx],
            "specificity": 1 - fpr[optimal_idx],
            "distance": np.sqrt(distances[optimal_idx])
        }
    
    elif method == "max_accuracy":
        # Maximum accuracy
        accuracy = (tpr * np.sum(y_true) + (1 - fpr) * np.sum(1 - y_true)) / len(y_true)
        optimal_idx = np.argmax(accuracy)
        optimal_threshold = thresholds[optimal_idx]
        
        optimal_point = {
            "sensitivity": tpr[optimal_idx],
            "specificity": 1 - fpr[optimal_idx],
            "accuracy": accuracy[optimal_idx]
        }
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return ROCResult(
        fpr=fpr,
        tpr=tpr,
        thresholds=thresholds,
        auc=roc_auc,
        optimal_threshold=optimal_threshold,
        optimal_point=optimal_point
    )


def likelihood_ratio_ci(
    lr: float,
    tp: int,
    fp: int,
    fn: int,
    tn: int,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate confidence interval for likelihood ratio.
    
    Args:
        lr: Likelihood ratio (positive or negative)
        tp, fp, fn, tn: 2x2 table counts
        confidence: Confidence level
        
    Returns:
        Tuple of (lower, upper) CI bounds
    """
    if lr <= 0:
        return 0.0, 0.0
    
    # Log transformation for CI
    log_lr = np.log(lr)
    
    if lr == float('inf'):
        # Handle infinite LR
        return float('inf'), float('inf')
    
    # Standard error on log scale
    if lr > 1:  # Positive LR
        var_log_lr = (1/tp - 1/(tp + fn) + 1/fp - 1/(fp + tn))
    else:  # Negative LR
        var_log_lr = (1/fn - 1/(tp + fn) + 1/tn - 1/(fp + tn))
    
    se_log_lr = np.sqrt(max(var_log_lr, 0))
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    
    log_ci_lower = log_lr - z * se_log_lr
    log_ci_upper = log_lr + z * se_log_lr
    
    return np.exp(log_ci_lower), np.exp(log_ci_upper)


def predictive_values_from_sens_spec(
    sensitivity: float,
    specificity: float,
    prevalence: float
) -> Tuple[float, float]:
    """
    Calculate PPV and NPV from sensitivity, specificity, and prevalence.
    
    Args:
        sensitivity: Test sensitivity
        specificity: Test specificity
        prevalence: Disease prevalence
        
    Returns:
        Tuple of (PPV, NPV)
    """
    # Input validation
    for value, name in [(sensitivity, "sensitivity"), 
                       (specificity, "specificity"),
                       (prevalence, "prevalence")]:
        if not 0 <= value <= 1:
            raise ValueError(f"{name} must be between 0 and 1")
    
    # Bayes' theorem
    ppv = (sensitivity * prevalence) / (sensitivity * prevalence + (1 - specificity) * (1 - prevalence))
    npv = (specificity * (1 - prevalence)) / (specificity * (1 - prevalence) + (1 - sensitivity) * prevalence)
    
    return ppv, npv


def fagan_nomogram(
    pre_test_prob: float,
    lr: float
) -> float:
    """
    Calculate post-test probability using Fagan's nomogram method.
    
    Args:
        pre_test_prob: Pre-test probability (0-1)
        lr: Likelihood ratio (positive or negative)
        
    Returns:
        Post-test probability
    """
    if not 0 <= pre_test_prob <= 1:
        raise ValueError("pre_test_prob must be between 0 and 1")
    if lr <= 0:
        raise ValueError("lr must be positive")
    
    if lr == float('inf'):
        return 1.0
    elif lr == 0:
        return 0.0
    
    # Convert probability to odds
    pre_test_odds = pre_test_prob / (1 - pre_test_prob)
    
    # Apply likelihood ratio
    post_test_odds = pre_test_odds * lr
    
    # Convert back to probability
    post_test_prob = post_test_odds / (1 + post_test_odds)
    
    return post_test_prob


def diagnostic_accuracy_ci(
    accuracy: float,
    n: int,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate confidence interval for diagnostic accuracy.
    
    Args:
        accuracy: Observed accuracy
        n: Total sample size
        confidence: Confidence level
        
    Returns:
        Tuple of (lower, upper) CI bounds
    """
    from .descriptive import proportion_ci
    ci = proportion_ci(int(accuracy * n), n, confidence=confidence)
    return ci.ci_lower, ci.ci_upper


def compare_diagnostic_tests(
    test1: DiagnosticResult,
    test2: DiagnosticResult,
    paired: bool = False,
    n: Optional[int] = None
) -> Dict[str, float]:
    """
    Compare two diagnostic tests.
    
    Args:
        test1: First test results
        test2: Second test results
        paired: Whether tests were applied to same subjects
        n: Number of subjects (required if paired=True)
        
    Returns:
        Dictionary with comparison statistics
    """
    # Compare sensitivities
    sens_diff = test1.sensitivity - test2.sensitivity
    
    # Compare specificities
    spec_diff = test1.specificity - test2.specificity
    
    # Compare AUCs if available
    auc_diff = None
    if hasattr(test1, 'auc') and hasattr(test2, 'auc'):
        auc_diff = test1.auc - test2.auc
    
    result = {
        "sensitivity_difference": sens_diff,
        "specificity_difference": spec_diff,
        "ppv_difference": test1.ppv - test2.ppv,
        "npv_difference": test1.npv - test2.npv,
        "accuracy_difference": test1.accuracy - test2.accuracy,
        "youden_difference": test1.youden - test2.youden
    }
    
    if auc_diff is not None:
        result["auc_difference"] = auc_diff
    
    if paired and n is not None:
        # Calculate McNemar's test for paired proportions
        from .contingency import Table2x2
        # This would require the full 2x2 comparison table
        # Simplified version for now
        pass
    
    return result


def optimal_threshold_grid_search(
    y_true: np.ndarray,
    y_score: np.ndarray,
    criteria: List[str] = ["youden", "accuracy", "f1"],
    thresholds: Optional[np.ndarray] = None
) -> Dict[str, Dict]:
    """
    Find optimal threshold using multiple criteria.
    
    Args:
        y_true: True labels
        y_score: Predicted scores
        criteria: List of criteria to optimize
        thresholds: Specific thresholds to test (optional)
        
    Returns:
        Dictionary with optimal thresholds for each criterion
    """
    if thresholds is None:
        thresholds = np.unique(y_score)
        thresholds = np.sort(thresholds)
    
    results = {}
    
    for criterion in criteria:
        best_value = -np.inf
        best_threshold = 0.5
        
        for threshold in thresholds:
            pred = (y_score >= threshold).astype(int)
            
            if criterion == "youden":
                tn = np.sum((y_true == 0) & (pred == 0))
                fp = np.sum((y_true == 0) & (pred == 1))
                tp = np.sum((y_true == 1) & (pred == 1))
                fn = np.sum((y_true == 1) & (pred == 0))
                
                sens = tp / (tp + fn) if (tp + fn) > 0 else 0
                spec = tn / (tn + fp) if (tn + fp) > 0 else 0
                value = sens + spec - 1
            
            elif criterion == "accuracy":
                accuracy = np.mean(pred == y_true)
                value = accuracy
            
            elif criterion == "f1":
                tp = np.sum((y_true == 1) & (pred == 1))
                fp = np.sum((y_true == 0) & (pred == 1))
                fn = np.sum((y_true == 1) & (pred == 0))
                
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                
                if precision + recall > 0:
                    value = 2 * precision * recall / (precision + recall)
                else:
                    value = 0
            
            else:
                continue
            
            if value > best_value:
                best_value = value
                best_threshold = threshold
        
        results[criterion] = {
            "threshold": best_threshold,
            "value": best_value
        }
    
    return results


# ==================== MODULE EXPORTS ====================

__all__ = [
    'DiagnosticMeasure',
    'DiagnosticResult',
    'ROCResult',
    'diagnostic_test_2x2',
    'diagnostic_from_data',
    'roc_analysis',
    'likelihood_ratio_ci',
    'predictive_values_from_sens_spec',
    'fagan_nomogram',
    'diagnostic_accuracy_ci',
    'compare_diagnostic_tests',
    'optimal_threshold_grid_search'
]
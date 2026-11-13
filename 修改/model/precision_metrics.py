"""Contest NRMSE: RMSE(error) / max(RMS(reference), 1e-8).

Aggregate squared errors, reference energy and element counts before calling
this function for a layer. Do not average individual sample NRMSE values.
This module uses only the Python 3.6 standard library.
"""
import math
from numbers import Integral

REFERENCE_RMS_FLOOR = 1e-8


def nrmse_from_sums(error_sum_sq, reference_sum_sq, elements):
    """Return a dimensionless ratio; multiply by 100 for percent."""
    if isinstance(elements, bool) or not isinstance(elements, Integral) or elements <= 0:
        raise ValueError("elements must be a positive integer")
    error_sum_sq, reference_sum_sq = float(error_sum_sq), float(reference_sum_sq)
    if not all(math.isfinite(v) and v >= 0 for v in (error_sum_sq, reference_sum_sq)):
        raise ValueError("squared-error and reference-energy sums must be finite and nonnegative")
    error_rms = math.sqrt(error_sum_sq / elements)
    reference_rms = math.sqrt(reference_sum_sq / elements)
    return error_rms / max(reference_rms, REFERENCE_RMS_FLOOR)

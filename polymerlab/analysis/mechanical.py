"""
Mechanical Testing Analysis Engine
Algorithmic implementation based on ASTM D638 and ISO 527 tensile test principles.

IMPORTANT SCIENTIFIC LIMITATIONS:
1. Crosshead vs. Extensometer: Modulus computed from crosshead displacement without an
   extensometer includes machine frame and grip compliance, which systematically underestimates
   the true Young's modulus. Extensometer data is required for certified compliance.
2. Toe Region: Standard ASTM D638 Section 10.3 toe compensation extrapolates linear elastic
   slope to zero load. When enabled, reported strains (yield strain, strain at UTS, and elongation at break)
   follow the corrected convention: ε_corrected = ε_raw - ε_toe.
3. Viscoelasticity: Polymers are time- and temperature-dependent viscoelastic materials.
   Static modulus from standard tensile tests should not be conflated with dynamic storage modulus (E').
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class MechanicalAnalysisResult:
    youngs_modulus_mpa: float
    youngs_modulus_gpa: float
    r_squared_elastic: float
    toe_strain_offset: float
    yield_strength_mpa: Optional[float]
    yield_strain: Optional[float]  # Toe-corrected if compensation enabled
    yield_method: str  # "0.2% Offset Yield", "Local Yield Peak", or "Fracture Before Yield (Brittle)"
    ultimate_tensile_strength_mpa: float
    strain_at_uts: float  # Toe-corrected if compensation enabled
    elongation_at_break_pct: float  # Toe-corrected if compensation enabled
    strain_at_break: float  # Toe-corrected if compensation enabled
    tensile_toughness_mj_m3: float
    modulus_of_resilience_mj_m3: float
    failure_behavior: str  # "Brittle Fracture", "Ductile with Necking", "Highly Ductile / Cold Drawing", "Flexible / Elastomeric"

    # Coordinates for visualization
    elastic_fit_strain: np.ndarray
    elastic_fit_stress: np.ndarray
    offset_line_strain: Optional[np.ndarray]
    offset_line_stress: Optional[np.ndarray]

    # Raw measured strain coordinates (uncorrected for toe offset)
    raw_yield_strain: Optional[float] = None
    raw_strain_at_uts: Optional[float] = None
    raw_strain_at_break: Optional[float] = None
    raw_elongation_at_break_pct: Optional[float] = None


def validate_strain_monotonicity(strain: np.ndarray, tolerance: float = 1e-5) -> None:
    """
    Validates that experimental strain values are monotonically non-decreasing.
    Preserves original test time sequence and detects unloading, slip, or reversal.
    
    Parameters:
    - strain: 1D array of strain values
    - tolerance: Permissible minor numerical resolution chatter (default: 1e-5)
    
    Raises:
    - ValueError: if strain contains significant non-monotonic reversal.
    """
    if len(strain) < 2:
        return

    diffs = np.diff(strain)
    violations = np.where(diffs < -tolerance)[0]
    if len(violations) > 0:
        first_idx = int(violations[0])
        decrease = abs(float(diffs[first_idx]))
        prev_val = float(strain[first_idx])
        curr_val = float(strain[first_idx + 1])
        raise ValueError(
            f"Non-monotonic strain sequence detected at data point {first_idx + 2} "
            f"(strain decreased from {prev_val:.6f} to {curr_val:.6f}, drop of {decrease:.6f}). "
            "Tensile property extraction requires continuous monotonic loading. "
            "Data containing unloading cycles, crosshead return, or extensometer slippage must be trimmed."
        )


def compute_engineering_stress_strain(
    force_n: np.ndarray,
    displacement_mm: np.ndarray,
    gauge_length_mm: float,
    width_mm: float,
    thickness_mm: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes engineering strain and stress from raw test bench measurements.
    
    Formulae:
    - Engineering Stress: σ = F / A₀ = F / (w * t) [MPa = N/mm²]
    - Engineering Strain: ε = ΔL / L₀ [dimensionless ratio]
    """
    force_n = np.asarray(force_n, dtype=float)
    displacement_mm = np.asarray(displacement_mm, dtype=float)

    if len(force_n) != len(displacement_mm):
        raise ValueError("Force and displacement arrays must have identical lengths.")
    if len(force_n) == 0:
        raise ValueError("Force and displacement arrays cannot be empty.")
    if gauge_length_mm <= 0:
        raise ValueError("Gauge length must be strictly positive.")
    if width_mm <= 0 or thickness_mm <= 0:
        raise ValueError("Specimen cross-sectional dimensions must be strictly positive.")

    cross_section_area_mm2 = width_mm * thickness_mm
    stress_mpa = force_n / cross_section_area_mm2
    strain = displacement_mm / gauge_length_mm
    return strain, stress_mpa


def _find_exact_offset_intersection(
    strain: np.ndarray,
    stress_mpa: np.ndarray,
    e_modulus: float,
    offset_strain: float,
    start_index: int = 0,
) -> Optional[Tuple[float, float]]:
    """
    Analytically computes the exact intersection point between the experimental stress-strain
    curve and the parallel 0.2% offset line: σ_offset(ε) = E * (ε - ε_offset).
    Solves linear segment equations analytically to avoid discretization errors.
    """
    if e_modulus <= 0:
        return None

    n = len(strain)
    for i in range(max(0, start_index), n - 1):
        e1, e2 = strain[i], strain[i + 1]
        s1, s2 = stress_mpa[i], stress_mpa[i + 1]

        # Ignore non-increasing or degenerate strain steps
        de = e2 - e1
        if abs(de) < 1e-12:
            continue

        # Segment slope: m = (s2 - s1) / (e2 - e1)
        m = (s2 - s1) / de

        # Parallel lines have no unique intersection
        if abs(e_modulus - m) < 1e-9:
            continue

        # Analytical solution for intersection:
        # s1 + m * (e_star - e1) = E * (e_star - offset_strain)
        # e_star * (E - m) = s1 - m * e1 + E * offset_strain
        e_star = (s1 - m * e1 + e_modulus * offset_strain) / (e_modulus - m)

        # Check if intersection lies inside the segment [min(e1, e2), max(e1, e2)]
        seg_min = min(e1, e2)
        seg_max = max(e1, e2)
        if seg_min <= e_star <= seg_max and e_star >= offset_strain:
            s_star = e_modulus * (e_star - offset_strain)
            if s_star >= 0:
                return float(e_star), float(s_star)

    return None


def detect_rupture_point(strain: np.ndarray, stress_mpa: np.ndarray, uts_mpa: float) -> int:
    """
    Identifies true physical rupture point prior to catastrophic load drop and sensor slack.
    """
    n = len(strain)
    if n <= 5:
        return n - 1

    # Search backwards for sharp fracture drop to near zero
    uts_threshold = uts_mpa * 0.15  # Load dropped below 15% of UTS
    for i in range(n - 1, int(n * 0.5), -1):
        if stress_mpa[i] < uts_threshold:
            # Check if there is a sharp cliff preceding this point
            prev_stress = stress_mpa[max(0, i - 1)]
            if prev_stress > uts_threshold * 2.0:
                return max(0, i - 1)

    return n - 1


def analyze_stress_strain(
    strain: np.ndarray,
    stress_mpa: np.ndarray,
    elastic_strain_min: float = 0.0005,  # 0.05%
    elastic_strain_max: float = 0.0025,  # 0.25%
    offset_strain: float = 0.002,         # 0.2% offset
    apply_toe_compensation: bool = True,
) -> MechanicalAnalysisResult:
    """
    Extracts fundamental mechanical tensile properties.
    
    Parameters:
    - strain: Engineering strain (dimensionless ratio, e.g. 0.01 for 1%)
    - stress_mpa: Engineering stress in MPa
    - elastic_strain_min: Lower bound for linear regression (ISO 527: 0.05%)
    - elastic_strain_max: Upper bound for linear regression (ISO 527: 0.25%)
    - offset_strain: Offset strain for yield calculation (ASTM D638: 0.2% / 0.002)
    - apply_toe_compensation: Adjust strain origin using ASTM D638 Section 10.3 convention
    """
    strain = np.asarray(strain, dtype=float)
    stress_mpa = np.asarray(stress_mpa, dtype=float)

    if len(strain) < 5 or len(stress_mpa) < 5:
        raise ValueError("Insufficient data points for mechanical analysis (minimum 5 required).")

    # Clean zero-variance strain edge case
    if np.max(strain) - np.min(strain) < 1e-7:
        raise ValueError("Strain data has zero variance. Crosshead displacement was not recorded.")

    # Validate monotonicity to preserve temporal causality (rejection of unloading data)
    validate_strain_monotonicity(strain, tolerance=1e-5)

    # Detect true rupture point before potential machine return slack
    raw_uts = float(np.max(stress_mpa))
    rupture_idx = detect_rupture_point(strain, stress_mpa, raw_uts)
    active_strain = strain[:rupture_idx + 1]
    active_stress = stress_mpa[:rupture_idx + 1]
    uts_idx = int(np.argmax(active_stress))
    uts_mpa = float(active_stress[uts_idx])
    raw_strain_uts = float(active_strain[uts_idx])

    # 1. Young's Modulus calculation (ISO 527 / ASTM D638)
    elastic_mask = (active_strain >= elastic_strain_min) & (active_strain <= elastic_strain_max)
    if np.sum(elastic_mask) >= 3:
        elastic_strain = active_strain[elastic_mask]
        elastic_stress = active_stress[elastic_mask]
    else:
        # Fallback: scan early curve for best linear region without crossing peak stress
        peak_limit = max(3, uts_idx if uts_idx >= 3 else len(active_strain))
        n_early = max(3, min(peak_limit, max(4, int(len(active_strain) * 0.08))))
        elastic_strain = active_strain[:n_early]
        elastic_stress = active_stress[:n_early]

    # Linear fit: σ = E * ε + σ₀
    if len(elastic_strain) >= 2 and (np.max(elastic_strain) - np.min(elastic_strain)) > 1e-9:
        poly = np.polyfit(elastic_strain, elastic_stress, 1)
        e_modulus_mpa = float(poly[0])
        intercept = float(poly[1])
    else:
        # Fallback to secant slope
        e_modulus_mpa = float((active_stress[min(5, len(active_stress)-1)] - active_stress[0]) / max(1e-6, active_strain[min(5, len(active_strain)-1)]))
        intercept = 0.0

    if e_modulus_mpa <= 0:
        # Physical safeguard against negative slope due to initial slack
        e_modulus_mpa = float(max(10.0, np.max(active_stress) / max(0.01, active_strain[int(len(active_strain)*0.2)])))
        intercept = 0.0

    e_modulus_gpa = e_modulus_mpa / 1000.0

    # R-squared of elastic fit
    pred_stress = poly[0] * elastic_strain + poly[1] if 'poly' in locals() else elastic_stress
    ss_tot = np.sum((elastic_stress - np.mean(elastic_stress)) ** 2)
    ss_res = np.sum((elastic_stress - pred_stress) ** 2)
    r_squared = float(1.0 - (ss_res / ss_tot)) if ss_tot > 1e-12 else 0.99
    r_squared = max(0.0, min(1.0, r_squared))

    # Toe compensation (ASTM D638 Section 10.3): ε_toe = -σ₀ / E
    toe_strain_offset = 0.0
    if apply_toe_compensation and e_modulus_mpa > 0 and intercept < 0:
        toe_strain_offset = float(-intercept / e_modulus_mpa)
        if toe_strain_offset > 0.05:  # Cap unreasonable toe offsets
            toe_strain_offset = 0.0

    # 2. Yield Strength & Detection
    # True yield peak in ductile polymers requires:
    # 1. Strain > elastic_strain_max
    # 2. Significant stress drop (> 1.5% of peak) to distinguish from ADC noise
    yield_strength_mpa: Optional[float] = None
    raw_yield_strain: Optional[float] = None
    yield_method = "None"

    # Search for physical upper yield peak
    search_start = np.searchsorted(active_strain, elastic_strain_max)
    search_end = min(len(active_strain) - 2, max(search_start + 5, uts_idx + 1))

    candidate_peaks = []
    for i in range(search_start, search_end):
        s_curr = active_stress[i]
        # Check local peak with sustained drop
        if s_curr >= active_stress[i - 1] and s_curr >= active_stress[i + 1]:
            # Sustained drop check: next 3 points must drop by at least 1.5%
            forward_window = active_stress[i+1:min(i + 5, len(active_stress))]
            if len(forward_window) > 0 and (np.min(forward_window) <= s_curr * 0.985):
                candidate_peaks.append(i)

    if candidate_peaks:
        peak_idx = candidate_peaks[0]
        yield_strength_mpa = float(active_stress[peak_idx])
        raw_yield_strain = float(active_strain[peak_idx])
        yield_method = "Local Yield Peak"
    else:
        # Standard 0.2% Offset Method
        # Search starting past the linear elastic region
        start_idx = np.searchsorted(active_strain, elastic_strain_min)
        exact_intersection = _find_exact_offset_intersection(
            strain=active_strain,
            stress_mpa=active_stress,
            e_modulus=e_modulus_mpa,
            offset_strain=offset_strain + toe_strain_offset,
            start_index=start_idx,
        )

        if exact_intersection:
            raw_yield_strain = exact_intersection[0]
            yield_strength_mpa = exact_intersection[1]
            yield_method = "0.2% Offset Yield"
        else:
            # Material fractured elastically before reaching 0.2% offset line
            yield_strength_mpa = uts_mpa
            raw_yield_strain = raw_strain_uts
            yield_method = "Fracture Before Yield (Brittle)"

    # 3. Raw uncorrected coordinates
    raw_strain_break = float(active_strain[-1])
    raw_elongation_at_break_pct = float(raw_strain_break * 100.0)

    # 4. Standard Reported Strain Parameters (Corrected for Toe Offset per ASTM D638 Section 10.3)
    if apply_toe_compensation and toe_strain_offset > 0.0:
        strain_at_uts = max(0.0, float(raw_strain_uts - toe_strain_offset))
        yield_strain = max(0.0, float(raw_yield_strain - toe_strain_offset)) if raw_yield_strain is not None else None
        strain_at_break = max(0.0, float(raw_strain_break - toe_strain_offset))
        elongation_at_break_pct = float(strain_at_break * 100.0)
    else:
        strain_at_uts = raw_strain_uts
        yield_strain = raw_yield_strain
        strain_at_break = raw_strain_break
        elongation_at_break_pct = raw_elongation_at_break_pct

    # 5. Tensile Toughness (Modulus of Toughness)
    # Area under the active curve up to rupture
    if hasattr(np, "trapezoid"):
        toughness_val = np.trapezoid(active_stress, active_strain)
    else:
        toughness_val = getattr(np, "trapz")(active_stress, active_strain)
    toughness_mj_m3 = max(0.0, float(toughness_val))

    # 6. Modulus of Resilience
    if yield_strength_mpa and e_modulus_mpa > 0:
        resilience_mj_m3 = float((yield_strength_mpa ** 2) / (2.0 * e_modulus_mpa))
    else:
        resilience_mj_m3 = 0.0

    # 7. Scientifically Grounded Failure Classification
    has_yielded = (yield_method in ["0.2% Offset Yield", "Local Yield Peak"]) and (raw_strain_break > (raw_yield_strain or 0.0) * 1.2)

    if elongation_at_break_pct <= 6.0:
        failure_behavior = "Brittle Fracture"
    elif e_modulus_mpa < 300.0 and elongation_at_break_pct >= 100.0:
        failure_behavior = "Flexible / Elastomeric"
    elif elongation_at_break_pct >= 100.0 and has_yielded:
        failure_behavior = "Highly Ductile / Cold Drawing"
    elif has_yielded:
        failure_behavior = "Ductile with Necking"
    else:
        failure_behavior = "Quasi-Brittle / Low Ductility"

    # Elastic tangent line for plotting (on measured strain coordinates)
    max_fit_strain = min(max(active_strain) * 0.35, max(0.015, raw_strain_uts * 0.8))
    fit_x = np.linspace(toe_strain_offset, max_fit_strain + toe_strain_offset, 100)
    fit_y = e_modulus_mpa * (fit_x - toe_strain_offset)

    # 0.2% offset line for plotting (on measured strain coordinates)
    eff_offset = offset_strain + toe_strain_offset
    if eff_offset < max(active_strain):
        off_x = np.linspace(eff_offset, min(max(active_strain), max_fit_strain + eff_offset), 100)
        off_y = e_modulus_mpa * (off_x - eff_offset)
    else:
        off_x = None
        off_y = None

    return MechanicalAnalysisResult(
        youngs_modulus_mpa=round(e_modulus_mpa, 2),
        youngs_modulus_gpa=round(e_modulus_gpa, 3),
        r_squared_elastic=round(r_squared, 4),
        toe_strain_offset=round(toe_strain_offset, 5),
        yield_strength_mpa=round(yield_strength_mpa, 2) if yield_strength_mpa else None,
        yield_strain=round(yield_strain, 4) if yield_strain else None,
        yield_method=yield_method,
        ultimate_tensile_strength_mpa=round(uts_mpa, 2),
        strain_at_uts=round(strain_at_uts, 4),
        elongation_at_break_pct=round(elongation_at_break_pct, 2),
        strain_at_break=round(strain_at_break, 4),
        tensile_toughness_mj_m3=round(toughness_mj_m3, 2),
        modulus_of_resilience_mj_m3=round(resilience_mj_m3, 3),
        failure_behavior=failure_behavior,
        elastic_fit_strain=fit_x,
        elastic_fit_stress=fit_y,
        offset_line_strain=off_x,
        offset_line_stress=off_y,
        raw_yield_strain=round(raw_yield_strain, 4) if raw_yield_strain is not None else None,
        raw_strain_at_uts=round(raw_strain_uts, 4),
        raw_strain_at_break=round(raw_strain_break, 4),
        raw_elongation_at_break_pct=round(raw_elongation_at_break_pct, 2),
    )

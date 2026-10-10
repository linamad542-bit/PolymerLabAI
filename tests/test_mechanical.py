"""
Automated tests for Mechanical Analysis Engine, Edge Cases, and Benchmark Provenance
"""

import os
import numpy as np
import pytest
from polymerlab.analysis.mechanical import (
    analyze_stress_strain,
    compute_engineering_stress_strain,
    detect_rupture_point,
    _find_exact_offset_intersection,
)
from polymerlab.analysis.validation import validate_mechanical_csv


def test_engineering_stress_strain_conversion():
    # 50 mm gauge length, 10 mm width, 4 mm thickness -> Area = 40 mm²
    force = np.array([0.0, 400.0, 800.0])
    disp = np.array([0.0, 0.5, 1.0])
    strain, stress = compute_engineering_stress_strain(
        force_n=force,
        displacement_mm=disp,
        gauge_length_mm=50.0,
        width_mm=10.0,
        thickness_mm=4.0,
    )

    # Stress = 400 / 40 = 10 MPa, 800 / 40 = 20 MPa
    np.testing.assert_allclose(stress, [0.0, 10.0, 20.0])
    # Strain = 0.5 / 50 = 0.01, 1.0 / 50 = 0.02
    np.testing.assert_allclose(strain, [0.0, 0.01, 0.02])


def test_invalid_specimen_geometry():
    with pytest.raises(ValueError):
        compute_engineering_stress_strain(np.array([10.0]), np.array([0.1]), 0.0, 10.0, 4.0)
    with pytest.raises(ValueError):
        compute_engineering_stress_strain(np.array([10.0]), np.array([0.1]), 50.0, -1.0, 4.0)
    with pytest.raises(ValueError):
        compute_engineering_stress_strain(np.array([10.0, 20.0]), np.array([0.1]), 50.0, 10.0, 4.0)


def test_linear_elastic_modulus_extraction():
    # Synthetic linear elastic material with E = 2000 MPa
    known_e = 2000.0
    strain = np.linspace(0.0, 0.02, 21)  # up to 2% strain
    stress = known_e * strain

    result = analyze_stress_strain(strain, stress)
    assert abs(result.youngs_modulus_mpa - known_e) < 5.0
    assert abs(result.youngs_modulus_gpa - 2.0) < 0.01
    assert result.r_squared_elastic > 0.99


def test_toughness_integration():
    # Linear ramp up to strain = 0.1 and stress = 20 MPa
    # Area of triangle = 0.5 * 0.1 * 20 = 1.0 MJ/m³
    strain = np.linspace(0.0, 0.1, 100)
    stress = 200.0 * strain  # At 0.1, stress = 20.0

    result = analyze_stress_strain(strain, stress)
    assert abs(result.tensile_toughness_mj_m3 - 1.0) < 0.05


def test_brittle_material_analysis():
    # PMMA-like brittle response: fails at 3.5% strain, high modulus (3000 MPa)
    strain = np.linspace(0.0, 0.035, 36)
    stress = 3000.0 * strain * (1.0 - 0.2 * (strain / 0.035))  # slight curvature
    result = analyze_stress_strain(strain, stress)

    assert result.elongation_at_break_pct < 5.0
    assert result.failure_behavior == "Brittle Fracture"
    assert result.ultimate_tensile_strength_mpa > 70.0


def test_ductile_material_analysis():
    # PP-like ductile material with yield peak and large elongation (150%)
    strain_elastic = np.linspace(0.0, 0.005, 15)
    strain_plastic = np.linspace(0.006, 1.5, 95)
    strain = np.concatenate([strain_elastic, strain_plastic])
    stress = 35.0 * (strain / 0.08) * np.exp(1.0 - (strain / 0.08)) + 15.0 * strain
    result = analyze_stress_strain(strain, stress)

    assert result.elongation_at_break_pct > 100.0
    assert result.failure_behavior == "Highly Ductile / Cold Drawing"
    assert result.yield_strength_mpa is not None


def test_noise_jitter_does_not_trigger_false_yield_peak():
    # Material with high stiffness that has small noise fluctuations in the elastic range
    # Jitter must NOT trigger a false yield peak at 0.1% strain!
    strain = np.linspace(0.0, 0.05, 51)
    base_stress = 1000.0 * strain
    # Add small high-frequency sensor noise (0.1 MPa) in elastic regime
    noise = np.array([0.05 if i % 2 == 0 else -0.05 for i in range(len(strain))])
    noisy_stress = base_stress + noise

    result = analyze_stress_strain(strain, noisy_stress, elastic_strain_min=0.0005, elastic_strain_max=0.0025)
    # The yield method should NOT be a false local peak in the noise zone (at strain < 0.005)
    if result.yield_strain is not None:
        assert result.yield_strain > 0.005, f"False yield peak triggered at early strain: {result.yield_strain}"


def test_exact_offset_intersection_analytical():
    # Construct exact bilinear curve:
    # Elastic branch: E = 1000 MPa from strain 0 to 0.01 (stress reaches 10 MPa)
    # Plastic branch: slope m = 100 MPa from strain 0.01 to 0.05
    # Curve equation in plastic region: σ(ε) = 10 + 100 * (ε - 0.01) = 100 * ε + 9
    # Offset line: σ_off(ε) = 1000 * (ε - 0.002) = 1000 * ε - 2
    # Setting equal: 100 * ε + 9 = 1000 * ε - 2 -> 900 * ε = 11 -> ε* = 11 / 900 ≈ 0.012222
    # Expected σ* = 1000 * (11/900 - 2/1000) = 1000 * (11/900 - 1.8/900) = 1000 * (9.2 / 900) = 10.222 MPa
    strain = np.linspace(0.0, 0.04, 41)
    stress = np.where(strain <= 0.01, 1000.0 * strain, 10.0 + 100.0 * (strain - 0.01))

    pt = _find_exact_offset_intersection(strain, stress, e_modulus=1000.0, offset_strain=0.002)
    assert pt is not None
    e_star, s_star = pt
    assert abs(e_star - (11.0 / 900.0)) < 1e-4
    assert abs(s_star - 10.222) < 0.05


def test_post_fracture_catastrophic_drop_detection():
    # Test machine recording points after sample snapped (stress drops to 0.2 MPa)
    strain = np.array([0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.052, 0.054])
    stress = np.array([0.0, 15.0, 30.0, 45.0, 50.0, 52.0, 0.2, 0.0])  # Catastrophic drop after 0.05

    rupture_idx = detect_rupture_point(strain, stress, uts_mpa=52.0)
    # The rupture index should be 5 (strain = 0.05), NOT index 7 (strain = 0.054 at 0 MPa)
    assert rupture_idx == 5
    assert strain[rupture_idx] == 0.05


def test_zero_variance_strain_raises_value_error():
    # Stuck extensometer where strain does not change
    strain = np.array([0.01, 0.01, 0.01, 0.01, 0.01, 0.01])
    stress = np.array([0.0, 5.0, 10.0, 15.0, 20.0, 25.0])
    with pytest.raises(ValueError, match="zero variance"):
        analyze_stress_strain(strain, stress)


def test_toe_compensation_calculation():
    # Strain curve with toe offset of 0.001
    # For strain >= 0.001, σ = 1000 * (strain - 0.001) = 1000 * strain - 1.0 (intercept = -1.0)
    strain = np.linspace(0.0, 0.02, 21)
    stress = np.maximum(0.0, 1000.0 * (strain - 0.001))

    result = analyze_stress_strain(strain, stress, apply_toe_compensation=True)
    assert result.toe_strain_offset > 0.0
    # Raw break strain must equal actual last strain (0.02)
    assert abs(result.raw_strain_at_break - 0.02) < 1e-5
    # Corrected break strain must equal raw - toe_offset (within 4-decimal precision)
    expected_corrected = 0.02 - result.toe_strain_offset
    assert abs(result.strain_at_break - expected_corrected) < 1e-4
    assert abs(result.elongation_at_break_pct - (expected_corrected * 100.0)) < 1e-2


def test_toe_compensation_enabled_vs_disabled():
    # Curve with distinct toe region
    strain = np.linspace(0.0, 0.03, 31)
    # Quadratic toe up to 0.004, then linear elastic
    stress = np.where(strain < 0.004, 250000.0 * (strain ** 2), 1000.0 * (strain - 0.002))
    
    res_enabled = analyze_stress_strain(strain, stress, apply_toe_compensation=True)
    res_disabled = analyze_stress_strain(strain, stress, apply_toe_compensation=False)

    # When enabled, toe offset > 0
    assert res_enabled.toe_strain_offset > 0.0
    # When disabled, toe offset == 0
    assert res_disabled.toe_strain_offset == 0.0

    # Raw values are identical in both runs
    assert res_enabled.raw_strain_at_break == res_disabled.raw_strain_at_break
    assert res_enabled.raw_strain_at_uts == res_disabled.raw_strain_at_uts

    # Corrected values when enabled are strictly less than raw values
    assert res_enabled.strain_at_break < res_disabled.strain_at_break
    assert res_enabled.strain_at_uts <= res_disabled.strain_at_uts
    assert abs(res_enabled.strain_at_break - (res_enabled.raw_strain_at_break - res_enabled.toe_strain_offset)) < 1e-4

    # When disabled, reported values strictly match raw measured values
    assert res_disabled.strain_at_break == res_disabled.raw_strain_at_break
    assert res_disabled.elongation_at_break_pct == res_disabled.raw_elongation_at_break_pct


def test_non_monotonic_unloading_raises_error():
    # Specimen loaded to strain 0.04, then unloaded to 0.02 (cyclic or unloader)
    strain_loading = np.linspace(0.0, 0.04, 20)
    strain_unloading = np.linspace(0.038, 0.02, 10)  # Reversal!
    strain = np.concatenate([strain_loading, strain_unloading])
    stress = np.concatenate([1000.0 * strain_loading, 1000.0 * strain_unloading])

    with pytest.raises(ValueError, match="Non-monotonic strain sequence detected"):
        analyze_stress_strain(strain, stress)


def test_negligible_jitter_allowed_monotonic():
    from polymerlab.analysis.mechanical import validate_strain_monotonicity
    # Minor discretization noise under 1e-5 tolerance is accepted
    strain = np.array([0.0, 0.001000, 0.0009999, 0.002000, 0.003000])
    # Should not raise
    validate_strain_monotonicity(strain, tolerance=1e-5)


def test_post_fracture_data_points_handling():
    # Catastrophic failure at strain 0.04 (stress drops from 60 MPa to 0.1 MPa)
    strain = np.array([0.0, 0.01, 0.02, 0.03, 0.04, 0.042, 0.045, 0.050])
    stress = np.array([0.0, 15.0, 30.0, 48.0, 60.0, 0.5, 0.1, 0.0])

    res = analyze_stress_strain(strain, stress, apply_toe_compensation=False)
    # The rupture detection should truncate post-break zero-stress points
    assert abs(res.raw_strain_at_break - 0.04) < 1e-5
    assert abs(res.strain_at_break - 0.04) < 1e-5
    assert abs(res.ultimate_tensile_strength_mpa - 60.0) < 1e-5


def test_bundled_sample_pp_csv():
    pp_path = os.path.join("data", "sample_tensile_pp.csv")
    with open(pp_path, "rb") as f:
        val = validate_mechanical_csv(f.read())
    assert val.is_valid
    res = analyze_stress_strain(val.df[val.strain_col].values, val.df[val.stress_col].values)
    assert res.youngs_modulus_mpa > 1000.0
    assert res.ultimate_tensile_strength_mpa > 30.0


def test_bundled_sample_pmma_csv():
    pmma_path = os.path.join("data", "sample_tensile_pmma.csv")
    with open(pmma_path, "rb") as f:
        val = validate_mechanical_csv(f.read())
    assert val.is_valid
    res = analyze_stress_strain(val.df[val.strain_col].values, val.df[val.stress_col].values)
    assert res.youngs_modulus_mpa > 2500.0
    assert res.failure_behavior == "Brittle Fracture"


def test_bundled_datasets_provenance_flagged_in_files():
    # All sample files must contain prominent synthetic provenance disclosures
    for fname in ["sample_tensile_pp.csv", "sample_tensile_pmma.csv", "sample_raw_load_displacement.csv"]:
        fpath = os.path.join("data", fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        assert "PROVENANCE: Idealized synthetic dataset" in content, f"Missing provenance disclosure in {fname}"
        assert "Not acquired from certified physical laboratory test bench" in content

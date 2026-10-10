"""
Automated tests for CSV Validation, Unit Conversions, and Edge Cases
"""

import numpy as np
import pytest
from polymerlab.analysis.validation import (
    validate_mechanical_csv,
    convert_stress_to_mpa,
    convert_strain_to_ratio,
    convert_force_to_n,
    convert_displacement_to_mm,
    extract_unit_from_header,
)


def test_valid_stress_strain_csv():
    csv_content = """Strain [-],Stress (MPa)
0.00,0.0
0.01,15.2
0.02,28.4
0.03,38.1
0.04,44.5
0.05,48.2
0.06,50.1
0.07,51.0
0.08,51.2
0.09,50.8
0.10,50.0
"""
    result = validate_mechanical_csv(csv_content)
    assert result.is_valid
    assert result.data_format == "STRESS_STRAIN"
    assert result.strain_col == "Strain [-]"
    assert result.stress_col == "Stress (MPa)"
    assert len(result.df) == 11


def test_valid_force_displacement_csv():
    csv_content = """Displacement (mm),Force (N)
0.0,0.0
0.5,120.0
1.0,240.0
1.5,350.0
2.0,450.0
2.5,530.0
3.0,590.0
3.5,630.0
4.0,650.0
4.5,655.0
5.0,650.0
"""
    result = validate_mechanical_csv(csv_content)
    assert result.is_valid
    assert result.data_format == "FORCE_DISPLACEMENT"
    assert len(result.df) == 11


def test_invalid_short_csv():
    csv_content = """Strain,Stress
0.0,0.0
0.01,10.0
"""
    result = validate_mechanical_csv(csv_content)
    assert not result.is_valid
    assert any("at least 10" in err for err in result.errors)


def test_empty_csv():
    result = validate_mechanical_csv("")
    assert not result.is_valid
    assert len(result.errors) > 0


def test_percentage_strain_detection():
    csv_content = """Strain (%),Stress (MPa)
0.0,0.0
5.0,15.2
10.0,28.4
15.0,38.1
20.0,44.5
25.0,48.2
30.0,50.1
35.0,51.0
40.0,51.2
45.0,50.8
50.0,50.0
"""
    result = validate_mechanical_csv(csv_content)
    assert result.is_valid
    assert result.strain_is_percentage
    assert result.detected_strain_unit == "%"


def test_stress_unit_conversions():
    # 2.5 GPa = 2500 MPa
    np.testing.assert_allclose(convert_stress_to_mpa(np.array([2.5]), "gpa"), [2500.0])
    # 50,000 kPa = 50 MPa
    np.testing.assert_allclose(convert_stress_to_mpa(np.array([50000.0]), "kpa"), [50.0])
    # 30,000,000 Pa = 30 MPa
    np.testing.assert_allclose(convert_stress_to_mpa(np.array([30000000.0]), "pa"), [30.0])
    # 10,000 psi = 68.94757 MPa
    np.testing.assert_allclose(convert_stress_to_mpa(np.array([10000.0]), "psi"), [68.94757], rtol=1e-4)
    # 5.0 ksi = 34.473785 MPa
    np.testing.assert_allclose(convert_stress_to_mpa(np.array([5.0]), "ksi"), [34.473785], rtol=1e-4)


def test_strain_unit_conversions():
    # 50% = 0.50 ratio
    np.testing.assert_allclose(convert_strain_to_ratio(np.array([50.0]), "%"), [0.50])
    # 10,000 microstrain = 0.01 ratio
    np.testing.assert_allclose(convert_strain_to_ratio(np.array([10000.0]), "microstrain"), [0.01])
    # 0.25 mm/mm = 0.25 ratio
    np.testing.assert_allclose(convert_strain_to_ratio(np.array([0.25]), "mm/mm"), [0.25])


def test_force_and_displacement_conversions():
    # 5.0 kN = 5000 N
    np.testing.assert_allclose(convert_force_to_n(np.array([5.0]), "kn"), [5000.0])
    # 100 lbf = 444.8222 N
    np.testing.assert_allclose(convert_force_to_n(np.array([100.0]), "lbf"), [444.8222], rtol=1e-4)
    # 2.0 inches = 50.8 mm
    np.testing.assert_allclose(convert_displacement_to_mm(np.array([2.0]), "in"), [50.8])
    # 0.05 meters = 50.0 mm
    np.testing.assert_allclose(convert_displacement_to_mm(np.array([0.05]), "m"), [50.0])


def test_extract_unit_from_header():
    assert extract_unit_from_header("Stress (MPa)", "stress") == "mpa"
    assert extract_unit_from_header("Engineering Stress [GPa]", "stress") == "gpa"
    assert extract_unit_from_header("Tensile Stress [psi]", "stress") == "psi"
    assert extract_unit_from_header("Strain (%)", "strain") == "%"
    assert extract_unit_from_header("Strain [mm/mm]", "strain") == "ratio"
    assert extract_unit_from_header("Load [kN]", "force") == "kn"
    assert extract_unit_from_header("Extension (in)", "displacement") == "in"


def test_high_ductility_strain_not_falsely_divided():
    # Polymer with high elongation (LDPE at 3.5 ratio = 350% strain)
    # Header explicitly has [-], so it must NOT be marked as percentage
    csv_content = """Strain [-],Stress (MPa)
0.0,0.0
0.2,5.0
0.5,10.0
1.0,12.0
1.5,13.0
2.0,14.0
2.5,15.0
3.0,16.0
3.5,17.0
4.0,18.0
"""
    result = validate_mechanical_csv(csv_content)
    assert result.is_valid
    assert not result.strain_is_percentage
    assert result.detected_strain_unit == "ratio"


def test_anti_synonym_collision_avoided():
    # If file contains "Strain Rate (1/s)" and "Strain [-]", it must pick "Strain [-]"
    csv_content = """Strain Rate (1/s),Strain [-],Stress (MPa)
0.01,0.00,0.0
0.01,0.01,10.0
0.01,0.02,20.0
0.01,0.03,30.0
0.01,0.04,40.0
0.01,0.05,45.0
0.01,0.06,48.0
0.01,0.07,49.0
0.01,0.08,50.0
0.01,0.09,50.0
0.01,0.10,49.0
"""
    result = validate_mechanical_csv(csv_content)
    assert result.is_valid
    assert result.strain_col == "Strain [-]"


def test_csv_with_comment_metadata_preamble():
    # Raw UTM export files often have comment header rows
    csv_content = """# Test Type: Tensile ASTM D638
# Machine: Universal Testing Machine UTM-50kN
# Date: 2026-10-09
# Crosshead Speed: 50 mm/min
Strain [-],Stress (MPa)
0.00,0.0
0.01,12.0
0.02,24.0
0.03,34.0
0.04,42.0
0.05,48.0
0.06,51.0
0.07,52.5
0.08,53.0
0.09,52.8
0.10,52.0
"""
    result = validate_mechanical_csv(csv_content)
    assert result.is_valid
    assert len(result.df) == 11
    assert result.strain_col == "Strain [-]"

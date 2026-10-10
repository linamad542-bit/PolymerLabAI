"""
Mechanical Testing Lab Page - Tensile Stress-Strain Analysis (ASTM D638 / ISO 527-1 Methodology)
"""

import os
import json
import streamlit as st
import pandas as pd
import numpy as np

from polymerlab.analysis.mechanical import (
    analyze_stress_strain,
    compute_engineering_stress_strain,
)
from polymerlab.analysis.validation import (
    validate_mechanical_csv,
    convert_stress_to_mpa,
    convert_strain_to_ratio,
    convert_force_to_n,
    convert_displacement_to_mm,
)
from polymerlab.visualization.plots import create_stress_strain_plot


def render_mechanical_testing() -> None:
    st.title("📈 Mechanical Testing Laboratory")
    st.caption("Standard Tensile Properties Extraction (Based on ASTM D638 / ISO 527-1 Methodology • Screening & Analysis)")

    # Data Source Selection
    st.subheader("1. Data Ingestion & Sample Datasets")

    data_source_mode = st.radio(
        "Select Data Source:",
        ["Upload CSV File", "Load Synthetic Demonstration Dataset"],
        horizontal=True,
    )

    csv_bytes = None
    file_name = "test_specimen.csv"

    if data_source_mode == "Upload CSV File":
        uploaded_file = st.file_uploader(
            "Upload Tensile Testing CSV (ASTM D638 / ISO 527 formatted):",
            type=["csv", "txt"],
            help="File should contain Strain & Stress columns, or Displacement (mm) & Force (N) columns.",
        )
        if uploaded_file is not None:
            csv_bytes = uploaded_file.getvalue()
            file_name = uploaded_file.name
        else:
            st.info("Upload a CSV file or switch to 'Load Synthetic Demonstration Dataset' above to test immediately.")
            return

    else:
        st.caption(
            "ℹ️ **Provenance Notice**: Bundled sample datasets are **idealized synthetic datasets** "
            "generated algorithmically for software verification and demonstration. "
            "They are not physical experimental measurements from an external load cell."
        )

        sample_choice = st.selectbox(
            "Choose a synthetic demonstration dataset:",
            [
                "Polypropylene (PP) - Ductile with Yield Necking & Cold Drawing (Synthetic)",
                "PMMA (Acrylic) - High-Stiffness Brittle Fracture (Synthetic)",
                "UTM Raw Load-Displacement (Force in N & Displacement in mm) (Synthetic)",
            ],
        )

        sample_path_map = {
            "Polypropylene (PP) - Ductile with Yield Necking & Cold Drawing (Synthetic)": "data/sample_tensile_pp.csv",
            "PMMA (Acrylic) - High-Stiffness Brittle Fracture (Synthetic)": "data/sample_tensile_pmma.csv",
            "UTM Raw Load-Displacement (Force in N & Displacement in mm) (Synthetic)": "data/sample_raw_load_displacement.csv",
        }

        path = sample_path_map[sample_choice]
        if os.path.exists(path):
            with open(path, "rb") as f:
                csv_bytes = f.read()
            file_name = os.path.basename(path)
            st.success(f"Loaded dataset: `{file_name}`")
        else:
            st.error(f"Sample file `{path}` not found.")
            return

    # 2. Validation & Preprocessing
    val_result = validate_mechanical_csv(csv_bytes, filename=file_name)

    # Show Warnings
    for w in val_result.warnings:
        st.warning(f"⚠️ Validation Warning: {w}")

    if not val_result.is_valid:
        st.error("❌ CSV Validation Failed:")
        for err in val_result.errors:
            st.write(f"- {err}")
        return

    df = val_result.df
    st.success(f"✅ Data validated successfully ({len(df)} data points, detected as {val_result.data_format}).")

    st.markdown("---")
    st.subheader("2. Test Configuration & Specimen Geometry")

    strain_array = None
    stress_array = None

    if val_result.data_format == "FORCE_DISPLACEMENT":
        st.info("Input data is in machine coordinates [Displacement, Force]. Specimen dimensions are required for stress & strain:")
        dim_col1, dim_col2, dim_col3 = st.columns(3)
        with dim_col1:
            gauge_length = st.number_input("Gauge Length (L₀) [mm]:", min_value=1.0, value=50.0, step=1.0, help="ASTM D638 Type I standard is 50.0 mm")
        with dim_col2:
            width = st.number_input("Specimen Width (w) [mm]:", min_value=0.1, value=10.0, step=0.5, help="Narrow section width")
        with dim_col3:
            thickness = st.number_input("Specimen Thickness (t) [mm]:", min_value=0.1, value=4.0, step=0.2, help="Specimen depth/thickness")

        # Convert force and displacement units if necessary
        raw_disp = df[val_result.displacement_col].values
        raw_force = df[val_result.force_col].values

        disp_vals = convert_displacement_to_mm(raw_disp, val_result.detected_displacement_unit)
        force_vals = convert_force_to_n(raw_force, val_result.detected_force_unit)

        strain_array, stress_array = compute_engineering_stress_strain(
            force_n=force_vals,
            displacement_mm=disp_vals,
            gauge_length_mm=gauge_length,
            width_mm=width,
            thickness_mm=thickness,
        )

    else:
        # STRESS_STRAIN format
        raw_stress = df[val_result.stress_col].values
        stress_array = convert_stress_to_mpa(raw_stress, val_result.detected_stress_unit)

        raw_strain = df[val_result.strain_col].values

        is_pct = st.checkbox(
            "Strain column is in percent (%)",
            value=val_result.strain_is_percentage,
            help="Check if values represent percentages (e.g. 10 for 10% elongation) rather than dimensionless strain.",
        )
        if is_pct:
            strain_array = convert_strain_to_ratio(raw_strain, "%")
        else:
            strain_array = convert_strain_to_ratio(raw_strain, val_result.detected_strain_unit)

    # 3. ASTM D638 Analysis Execution
    st.markdown("---")
    st.subheader("3. Mechanical Analysis & Curve Evaluation")

    c_opt1, c_opt2, c_opt3, c_opt4 = st.columns(4)
    with c_opt1:
        elastic_min = st.number_input("Modulus Min Strain (ε₁):", value=0.0005, step=0.0002, format="%.4f", help="ISO 527 lower limit: 0.05% (0.0005)")
    with c_opt2:
        elastic_max = st.number_input("Modulus Max Strain (ε₂):", value=0.0025, step=0.0002, format="%.4f", help="ISO 527 upper limit: 0.25% (0.0025)")
    with c_opt3:
        offset_yield = st.number_input("Yield Offset Strain:", value=0.0020, step=0.0005, format="%.4f", help="Standard 0.2% offset (0.0020)")
    with c_opt4:
        toe_comp = st.checkbox("Toe Compensation (ASTM D638)", value=True, help="Extrapolates linear elastic slope to zero load axis")

    try:
        results = analyze_stress_strain(
            strain=strain_array,
            stress_mpa=stress_array,
            elastic_strain_min=elastic_min,
            elastic_strain_max=elastic_max,
            offset_strain=offset_yield,
            apply_toe_compensation=toe_comp,
        )
    except Exception as exc:
        st.error(f"Analysis calculation error: {str(exc)}")
        return

    # Visualizer Display
    plot_col, opts_col = st.columns([4, 1])
    with opts_col:
        st.markdown("**Plot Annotations**")
        show_e_fit = st.checkbox("Show Young's Modulus Tangent", value=True)
        show_off = st.checkbox("Show 0.2% Offset Line", value=True)
        show_tough = st.checkbox("Shade Toughness Area", value=True)
        strain_axis_pct = st.checkbox("Display Strain as %", value=True)

    with plot_col:
        fig = create_stress_strain_plot(
            strain=strain_array,
            stress_mpa=stress_array,
            result=results,
            sample_name=file_name.replace(".csv", ""),
            show_offset=show_off,
            show_elastic_fit=show_e_fit,
            show_toughness_fill=show_tough,
            strain_in_pct=strain_axis_pct,
        )
        st.plotly_chart(fig, use_container_width=True)

    # 4. Mechanical Properties Results Grid
    st.subheader("4. Extracted Mechanical Properties")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(
            label="Young's Modulus (E)",
            value=f"{results.youngs_modulus_mpa:.1f} MPa",
            delta=f"{results.youngs_modulus_gpa:.3f} GPa (R²={results.r_squared_elastic:.3f})",
        )
    with kpi2:
        val_str = f"{results.yield_strength_mpa:.1f} MPa" if results.yield_strength_mpa else "N/A"
        st.metric(
            label="Yield Strength (σy)",
            value=val_str,
            delta=f"Method: {results.yield_method}",
        )
    with kpi3:
        st.metric(
            label="Ultimate Tensile Strength (UTS)",
            value=f"{results.ultimate_tensile_strength_mpa:.1f} MPa",
            delta=f"@ ε = {results.strain_at_uts * 100:.1f}%",
        )
    with kpi4:
        st.metric(
            label="Elongation at Break (εb)",
            value=f"{results.elongation_at_break_pct:.1f} %",
            delta=f"Mode: {results.failure_behavior}",
        )

    # Secondary Metrics
    sec1, sec2, sec3 = st.columns(3)
    with sec1:
        st.metric(
            label="Tensile Toughness (Ut)",
            value=f"{results.tensile_toughness_mj_m3:.2f} MJ/m³",
            help="Total absorbed mechanical energy per unit volume up to fracture.",
        )
    with sec2:
        st.metric(
            label="Modulus of Resilience (Ur)",
            value=f"{results.modulus_of_resilience_mj_m3:.3f} MJ/m³",
            help="Elastic energy capacity per unit volume before plastic deformation.",
        )
    with sec3:
        st.metric(
            label="Failure Classification",
            value=results.failure_behavior,
            help="Material deformation phenotype based on yield behavior and elongation.",
        )

    # 5. Scientific Limitations & Metrology Note
    with st.expander("⚠️ Scientific Limitations & Metrology Notice"):
        st.markdown(
            """
            - **Crosshead Compliance Error**: If strain is derived from crosshead stroke rather than a clip-on or video extensometer, the recorded modulus incorporates machine frame and grip compliance, yielding an artificially lower modulus.
            - **Viscoelasticity**: Tensile properties of thermoplastics are sensitive to temperature and strain rate (testing speed). Results are valid only for the ambient test conditions.
            - **0.2% Offset Convention**: For materials without an abrupt yield drop, the 0.2% offset ($R_{p0.2}$) serves as an engineering yield approximation.
            - **Commercial Certification**: Results are for computational screening and research. Formal regulatory compliance requires calibrated physical testing benches following ISO/IEC 17025 accredited procedures.
            """
        )

    # 6. Data Export & Summary Download
    st.markdown("---")
    st.subheader("5. Report & Data Export")

    d_col1, d_col2 = st.columns(2)
    with d_col1:
        export_summary = {
            "specimen": file_name,
            "youngs_modulus_mpa": results.youngs_modulus_mpa,
            "youngs_modulus_gpa": results.youngs_modulus_gpa,
            "elastic_fit_r_squared": results.r_squared_elastic,
            "toe_strain_offset": results.toe_strain_offset,
            "yield_strength_mpa": results.yield_strength_mpa,
            "yield_strain": results.yield_strain,
            "yield_detection_method": results.yield_method,
            "ultimate_tensile_strength_mpa": results.ultimate_tensile_strength_mpa,
            "strain_at_uts": results.strain_at_uts,
            "elongation_at_break_pct": results.elongation_at_break_pct,
            "tensile_toughness_mj_m3": results.tensile_toughness_mj_m3,
            "modulus_of_resilience_mj_m3": results.modulus_of_resilience_mj_m3,
            "failure_behavior": results.failure_behavior,
            "raw_strain_at_uts": results.raw_strain_at_uts,
            "raw_yield_strain": results.raw_yield_strain,
            "raw_strain_at_break": results.raw_strain_at_break,
            "raw_elongation_at_break_pct": results.raw_elongation_at_break_pct,
            "methodology_disclaimer": "Modeled after ASTM D638 / ISO 527. Computational screening tool.",
        }
        json_str = json.dumps(export_summary, indent=2)
        st.download_button(
            label="📥 Download Analysis Report (JSON)",
            data=json_str,
            file_name=f"{file_name}_polymerlab_report.json",
            mime="application/json",
        )

    with d_col2:
        processed_df = pd.DataFrame({
            "Strain (mm/mm)": strain_array,
            "Strain (%)": strain_array * 100.0,
            "Stress (MPa)": stress_array,
        })
        csv_data = processed_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Standardized Curve (CSV)",
            data=csv_data,
            file_name=f"{file_name}_standardized_curve.csv",
            mime="text/csv",
        )

"""
Scientific Visualization with Plotly for PolymerLab AI
"""

from typing import List, Optional
import numpy as np
import plotly.graph_objects as go
from polymerlab.analysis.mechanical import MechanicalAnalysisResult
from polymerlab.database.models import PolymerRecord


def create_stress_strain_plot(
    strain: np.ndarray,
    stress_mpa: np.ndarray,
    result: MechanicalAnalysisResult,
    sample_name: str = "Polymer Test Specimen",
    show_offset: bool = True,
    show_elastic_fit: bool = True,
    show_toughness_fill: bool = True,
    strain_in_pct: bool = False,
) -> go.Figure:
    """
    Constructs an interactive engineering stress-strain curve with standard annotations.
    """
    fig = go.Figure()

    multiplier = 100.0 if strain_in_pct else 1.0
    x_unit = "%" if strain_in_pct else "mm/mm"
    x_curve = strain * multiplier

    # 1. Shaded area for toughness
    if show_toughness_fill:
        fig.add_trace(
            go.Scatter(
                x=x_curve,
                y=stress_mpa,
                fill="tozeroy",
                fillcolor="rgba(33, 150, 243, 0.12)",
                line=dict(width=0),
                name=f"Toughness ({result.tensile_toughness_mj_m3} MJ/m³)",
                hoverinfo="skip",
            )
        )

    # 2. Main Experimental Stress-Strain Curve
    fig.add_trace(
        go.Scatter(
            x=x_curve,
            y=stress_mpa,
            mode="lines",
            name="Experimental Data",
            line=dict(color="#1f77b4", width=2.8),
            hovertemplate=f"Strain: %{{x:.3f}} {x_unit}<br>Stress: %{{y:.2f}} MPa<extra></extra>",
        )
    )

    # 3. Elastic Tangent Line (Young's Modulus)
    if show_elastic_fit and len(result.elastic_fit_strain) > 0:
        fig.add_trace(
            go.Scatter(
                x=result.elastic_fit_strain * multiplier,
                y=result.elastic_fit_stress,
                mode="lines",
                name=f"E Fit ({result.youngs_modulus_gpa} GPa, R²={result.r_squared_elastic})",
                line=dict(color="#2ca02c", width=1.8, dash="dash"),
                hovertemplate=f"Strain: %{{x:.3f}} {x_unit}<br>Linear Stress: %{{y:.2f}} MPa<extra></extra>",
            )
        )

    # 4. 0.2% Offset Line
    if show_offset and result.offset_line_strain is not None and len(result.offset_line_strain) > 0:
        fig.add_trace(
            go.Scatter(
                x=result.offset_line_strain * multiplier,
                y=result.offset_line_stress,
                mode="lines",
                name="0.2% Offset Line",
                line=dict(color="#ff7f0e", width=1.5, dash="dot"),
                hoverinfo="skip",
            )
        )

    # 5. Yield Point Annotation
    if result.yield_strength_mpa is not None and result.yield_strain is not None:
        y_pos_x = (result.raw_yield_strain if result.raw_yield_strain is not None else result.yield_strain) * multiplier
        fig.add_trace(
            go.Scatter(
                x=[y_pos_x],
                y=[result.yield_strength_mpa],
                mode="markers+text",
                name=f"Yield Point ({result.yield_strength_mpa} MPa)",
                marker=dict(color="#ff7f0e", size=10, symbol="diamond"),
                text=["Yield Point"],
                textposition="top left",
                hovertemplate=f"Yield: %{{y:.2f}} MPa @ {result.yield_strain * multiplier:.3f} {x_unit} (ASTM Corrected)<extra></extra>",
            )
        )

    # 6. Ultimate Tensile Strength (UTS) Annotation
    uts_pos_x = (result.raw_strain_at_uts if result.raw_strain_at_uts is not None else result.strain_at_uts) * multiplier
    fig.add_trace(
        go.Scatter(
            x=[uts_pos_x],
            y=[result.ultimate_tensile_strength_mpa],
            mode="markers+text",
            name=f"UTS ({result.ultimate_tensile_strength_mpa} MPa)",
            marker=dict(color="#d62728", size=10, symbol="cross"),
            text=["UTS"],
            textposition="top right",
            hovertemplate=f"UTS: %{{y:.2f}} MPa @ {result.strain_at_uts * multiplier:.3f} {x_unit} (ASTM Corrected)<extra></extra>",
        )
    )

    # 7. Fracture Point Annotation
    break_pos_x = (result.raw_strain_at_break if result.raw_strain_at_break is not None else result.strain_at_break) * multiplier
    fig.add_trace(
        go.Scatter(
            x=[break_pos_x],
            y=[stress_mpa[-1]],
            mode="markers+text",
            name=f"Fracture ({stress_mpa[-1]:.2f} MPa)",
            marker=dict(color="#9467bd", size=9, symbol="x"),
            text=["Fracture"],
            textposition="bottom right",
            hovertemplate=f"Fracture @ {result.strain_at_break * multiplier:.3f} {x_unit} (ASTM Corrected)<extra></extra>",
        )
    )

    # Layout configuration
    max_stress = max(stress_mpa) * 1.15
    fig.update_layout(
        title=f"Tensile Stress–Strain Curve: {sample_name}",
        title_font=dict(size=18, family="Arial, sans-serif"),
        xaxis=dict(
            title=f"Engineering Strain [{x_unit}]",
            showgrid=True,
            gridcolor="#e0e0e0",
            zeroline=True,
            zerolinecolor="#999999",
        ),
        yaxis=dict(
            title="Engineering Stress [MPa]",
            showgrid=True,
            gridcolor="#e0e0e0",
            zeroline=True,
            zerolinecolor="#999999",
            range=[0, max_stress],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.28,
            xanchor="center",
            x=0.5,
        ),
        hovermode="closest",
        margin=dict(l=60, r=40, t=60, b=80),
        template="plotly_white",
    )

    return fig


def create_property_comparison_bar(
    polymers: List[PolymerRecord],
    property_key: str = "youngs_modulus",
) -> go.Figure:
    """
    Renders bar chart comparing a chosen physical/mechanical property across polymers.
    """
    labels = []
    values = []
    error_y_pos = []
    error_y_neg = []

    prop_titles = {
        "youngs_modulus": ("Young's Modulus (Stiffness)", "MPa"),
        "tensile_strength": ("Tensile Strength", "MPa"),
        "elongation_at_break": ("Elongation at Break (Ductility)", "%"),
        "density": ("Mass Density", "g/cm³"),
        "glass_transition_temp": ("Glass Transition Temperature (Tg)", "°C"),
        "max_service_temp": ("Maximum Service Temperature", "°C"),
    }

    title, unit = prop_titles.get(property_key, (property_key, ""))

    for p in polymers:
        prop_range = getattr(p, property_key, None)
        if prop_range is not None:
            labels.append(p.abbreviation)
            values.append(prop_range.typical)
            error_y_pos.append(prop_range.max_val - prop_range.typical)
            error_y_neg.append(prop_range.typical - prop_range.min_val)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels,
            y=values,
            error_y=dict(
                type="data",
                symmetric=False,
                array=error_y_pos,
                arrayminus=error_y_neg,
                color="#555555",
            ),
            marker=dict(
                color="#006699",
                line=dict(color="#003366", width=1.5),
            ),
            hovertemplate=f"Polymer: %{{x}}<br>Typical: %{{y}} {unit}<extra></extra>",
        )
    )

    fig.update_layout(
        title=f"Comparison: {title}",
        xaxis_title="Polymer",
        yaxis_title=f"{title} [{unit}]",
        template="plotly_white",
        margin=dict(l=60, r=40, t=50, b=60),
    )
    return fig


def create_polymer_radar_chart(polymers: List[PolymerRecord]) -> go.Figure:
    """
    Generates multi-attribute radar chart normalized for high-level polymer benchmarking.
    """
    categories = [
        "Tensile Strength",
        "Stiffness (Modulus)",
        "Ductility (Elongation)",
        "Thermal Ceiling",
        "Density",
    ]

    # Reference normalizers (approx. max among standard polymers)
    norm = {
        "tensile": 80.0,
        "modulus": 3500.0,
        "elongation": 600.0,
        "temp": 130.0,
        "density": 1.45,
    }

    fig = go.Figure()
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"]

    for i, p in enumerate(polymers):
        vals = [
            min(100.0, (p.tensile_strength.typical / norm["tensile"]) * 100.0),
            min(100.0, (p.youngs_modulus.typical / norm["modulus"]) * 100.0),
            min(100.0, (p.elongation_at_break.typical / norm["elongation"]) * 100.0),
            min(100.0, (p.max_service_temp.typical / norm["temp"]) * 100.0),
            min(100.0, (p.density.typical / norm["density"]) * 100.0),
        ]
        # Close loop
        vals.append(vals[0])

        fig.add_trace(
            go.Scatterpolar(
                r=vals,
                theta=categories + [categories[0]],
                fill="toself",
                fillcolor=f"rgba({i*35%255}, {(i*80+50)%255}, {(i*120+100)%255}, 0.15)",
                name=p.abbreviation,
                line=dict(color=palette[i % len(palette)], width=2),
            )
        )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix="%",
            )
        ),
        showlegend=True,
        title="Comparative Property Profile (Normalized % of Class Max)",
        template="plotly_white",
        margin=dict(l=60, r=60, t=60, b=60),
    )
    return fig

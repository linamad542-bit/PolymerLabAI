"""
Dashboard Page for PolymerLab AI
"""

import streamlit as st
from polymerlab.database.polymer_db import get_polymer_database
from polymerlab.visualization.plots import create_property_comparison_bar, create_polymer_radar_chart
from polymerlab.config import APP_NAME, APP_TAGLINE, SUPPORTED_STANDARDS


def render_dashboard() -> None:
    st.title(f"🧪 {APP_NAME}")
    st.caption(f"**{APP_TAGLINE}** | Version 1.0.0")

    # Hardware Status Alert Ribbon
    st.info(
        "🔌 **Acquisition Interface Status**: Hardware Disconnected. "
        "Awaiting Arduino load-cell & extensometer link on serial COM port.",
        icon="ℹ️",
    )

    db = get_polymer_database()
    polymers = db.get_all()

    # Top KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Curated Polymers", len(polymers), help="PE (HDPE & LDPE), PP, PET, PVC, PS, PMMA")
    with col2:
        st.metric("Methodologies", "4 Referenced", help="ASTM D638, ISO 527-1/2, ASTM D790, ISO 178 methodologies")
    with col3:
        st.metric("Analysis Engine", "ASTM / ISO Principles", help="Modulus, 0.2% Offset, UTS, Toughness algorithms")
    with col4:
        st.metric("Hardware Architecture", "Modular (Ready)", help="Prepared for Arduino / HX711 acquisition")

    st.markdown("---")

    # Quick Navigation / Cards
    st.subheader("Laboratory Modules")
    m_col1, m_col2, m_col3 = st.columns(3)

    with m_col1:
        with st.container(border=True):
            st.markdown("### 📚 Reference Library")
            st.write(
                "Search verified thermal, physical, and mechanical property handbooks "
                "for PE, PP, PET, PVC, PS, and PMMA."
            )
            st.caption("Includes SPI resin codes, morphology, and ASTM standards.")

    with m_col2:
        with st.container(border=True):
            st.markdown("### 📈 Mechanical Testing")
            st.write(
                "Upload tensile test CSVs or load sample datasets to extract Young's Modulus, "
                "0.2% offset yield strength, UTS, and toughness."
            )
            st.caption("Interactive Plotly curves and ASTM D638 validation.")

    with m_col3:
        with st.container(border=True):
            st.markdown("### 🔌 Hardware & Arduino")
            st.write(
                "Real serial port scanner and architecture prepared for Arduino-driven "
                "load cells and optical extensometers."
            )
            st.caption("Zero-fake policy: reports real serial hardware states.")

    st.markdown("---")

    # Overview Analytics Charts
    st.subheader("Material Benchmarking Overview")
    chart_tabs = st.tabs(["Stiffness vs Tensile Strength", "Multi-Attribute Radar Profile", "Compliance Standards"])

    with chart_tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            fig_mod = create_property_comparison_bar(polymers, property_key="youngs_modulus")
            st.plotly_chart(fig_mod, use_container_width=True)
        with c2:
            fig_str = create_property_comparison_bar(polymers, property_key="tensile_strength")
            st.plotly_chart(fig_str, use_container_width=True)

    with chart_tabs[1]:
        fig_radar = create_polymer_radar_chart(polymers)
        st.plotly_chart(fig_radar, use_container_width=True)

    with chart_tabs[2]:
        st.markdown("#### Referenced Engineering Methodologies")
        for std in SUPPORTED_STANDARDS:
            st.markdown(f"- **{std}**")
        st.caption("Calculations follow ASTM/ISO mathematical principles. Physical validation requires calibrated instruments.")

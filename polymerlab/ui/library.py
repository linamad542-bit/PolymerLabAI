"""
Searchable Reference Library for Engineering Polymers
Covers authentic properties of PE (HDPE & LDPE), PP, PET, PVC, PS, and PMMA.
"""

import streamlit as st
import pandas as pd
from polymerlab.database.polymer_db import get_polymer_database
from polymerlab.visualization.plots import create_polymer_radar_chart, create_property_comparison_bar


def render_library() -> None:
    st.title("📚 Polymer Reference Library")
    st.write(
        "Peer-reviewed scientific reference data for commodity and engineering thermoplastics. "
        "Source: CRC Materials Science and Engineering Handbook & Mark's Polymer Handbook."
    )

    db = get_polymer_database()
    all_polymers = db.get_all()

    view_mode = st.radio("Library View:", ["Browse & Search Polymers", "Comparative Analysis Tool"], horizontal=True)

    if view_mode == "Browse & Search Polymers":
        # Search and Filters in an expander / column layout
        with st.container(border=True):
            f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
            with f_col1:
                search_query = st.text_input(
                    "🔍 Search by name, abbreviation, CAS, or application:",
                    placeholder="e.g. Polyethylene, PP, living hinges, 9002-88-4",
                )
            with f_col2:
                spi_options = ["All SPI Codes", "1 (PETE)", "2 (HDPE)", "3 (PVC)", "4 (LDPE)", "5 (PP)", "6 (PS)", "7 (Other)"]
                selected_spi_label = st.selectbox("Resin Code (SPI):", spi_options)
                spi_filter = None
                if selected_spi_label != "All SPI Codes":
                    spi_filter = int(selected_spi_label.split()[0])
            with f_col3:
                morphology_filter = st.selectbox("Morphology:", ["All", "Semicrystalline", "Amorphous"])
                morph_val = None if morphology_filter == "All" else morphology_filter

        # Execute Search
        filtered = db.search(query=search_query, spi_code=spi_filter, morphology=morph_val)

        st.markdown(f"**Showing {len(filtered)} of {len(all_polymers)} polymers**")

        if not filtered:
            st.warning("No polymers matched your search criteria. Try clearing filters.")
            return

        # Render Polymer Cards / Detail Sections
        for p in filtered:
            with st.expander(f"**{p.name} ({p.abbreviation})** — SPI #{p.spi_code} | {p.morphology.split()[0]}", expanded=(len(filtered) == 1)):
                header_col1, header_col2, header_col3 = st.columns(3)
                with header_col1:
                    st.markdown(f"**Chemical Formula:** `{p.chemical_formula}`")
                    st.markdown(f"**CAS Number:** `{p.cas_number}`")
                with header_col2:
                    st.markdown(f"**Resin Code:** ♳ SPI #{p.spi_code}")
                    st.markdown(f"**Morphology:** {p.morphology}")
                with header_col3:
                    st.markdown(f"**Common Synonyms:** {', '.join(p.common_names)}")

                st.markdown("---")

                # Properties Table
                prop_col1, prop_col2 = st.columns(2)
                with prop_col1:
                    st.markdown("#### 🔬 Physical & Thermal Properties")
                    st.markdown(f"- **Density:** {p.density.to_display()}")
                    st.markdown(f"- **Glass Transition Temp (Tg):** {p.glass_transition_temp.to_display()}")
                    tm_text = p.melting_temp.to_display() if p.melting_temp else "Amorphous (No sharp Tm)"
                    st.markdown(f"- **Melting Point (Tm):** {tm_text}")
                    st.markdown(f"- **Max Service Temp:** {p.max_service_temp.to_display()}")

                with prop_col2:
                    st.markdown("#### ⚙️ Mechanical Properties")
                    st.markdown(f"- **Young's Modulus (E):** {p.youngs_modulus.to_display()}")
                    st.markdown(f"- **Tensile Strength:** {p.tensile_strength.to_display()}")
                    st.markdown(f"- **Elongation at Break:** {p.elongation_at_break.to_display()}")
                    st.markdown(f"- **Flexural Modulus:** {p.flexural_modulus.to_display()}")

                st.markdown("---")

                # Chemical Resistance & Applications
                app_col1, app_col2 = st.columns(2)
                with app_col1:
                    st.markdown("#### 🏭 Typical Industrial Applications")
                    for app in p.typical_applications:
                        st.markdown(f"- {app}")
                    st.markdown("#### ♻️ Recycling & Sustainability")
                    st.write(p.recyclability_notes)

                with app_col2:
                    st.markdown("#### 🧪 Chemical Resistance Profile")
                    st.write(p.chemical_resistance)

                    st.markdown("#### ✅ Advantages")
                    for adv in p.advantages:
                        st.markdown(f"- {adv}")

                    st.markdown("#### ⚠️ Limitations")
                    for lim in p.limitations:
                        st.markdown(f"- {lim}")

                if p.astm_standards:
                    st.caption(f"Relevant ASTM Standards: {', '.join(p.astm_standards)}")

    else:
        # Comparative Analysis Tool
        st.subheader("Side-by-Side Material Comparison")
        selected_ids = st.multiselect(
            "Select polymers to compare:",
            options=[p.id for p in all_polymers],
            default=[p.id for p in all_polymers[:4]],
            format_func=lambda x: db.get_by_id(x).abbreviation if db.get_by_id(x) else x,
        )

        selected_polymers = [db.get_by_id(pid) for pid in selected_ids if db.get_by_id(pid)]

        if not selected_polymers:
            st.info("Select at least one polymer to view comparative analysis.")
            return

        c1, c2 = st.columns([1, 1])
        with c1:
            st.plotly_chart(create_polymer_radar_chart(selected_polymers), use_container_width=True)
        with c2:
            prop_choice = st.selectbox(
                "Compare Property:",
                options=[
                    ("youngs_modulus", "Young's Modulus (MPa)"),
                    ("tensile_strength", "Tensile Strength (MPa)"),
                    ("elongation_at_break", "Elongation at Break (%)"),
                    ("density", "Density (g/cm³)"),
                    ("glass_transition_temp", "Glass Transition Temp (°C)"),
                    ("max_service_temp", "Max Service Temp (°C)"),
                ],
                format_func=lambda x: x[1],
            )[0]
            st.plotly_chart(create_property_comparison_bar(selected_polymers, prop_choice), use_container_width=True)

        # Tabular comparison
        st.markdown("#### Quantitative Property Table")
        table_rows = []
        for p in selected_polymers:
            table_rows.append({
                "Polymer": p.abbreviation,
                "Chemical Name": p.name,
                "SPI #": p.spi_code,
                "Density [g/cm³]": p.density.typical,
                "Tg [°C]": p.glass_transition_temp.typical,
                "Tm [°C]": p.melting_temp.typical if p.melting_temp else "N/A",
                "Young's Modulus [MPa]": p.youngs_modulus.typical,
                "Tensile Strength [MPa]": p.tensile_strength.typical,
                "Elongation [%]": p.elongation_at_break.typical,
                "Flex Modulus [MPa]": p.flexural_modulus.typical,
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True)


"""
PolymerLab AI - Main Application Entry Point
"""

from pathlib import Path

import streamlit as st

# Page configuration must be the first Streamlit command.
st.set_page_config(
    page_title="PolymerLab AI | Chemistry Club",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

from polymerlab.config import APP_NAME, APP_VERSION, APP_TAGLINE
from polymerlab.ui import (
    render_dashboard,
    render_library,
    render_mechanical_testing,
    render_hardware_manager,
)

# Shared logo path
BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "chemistry_logo.png"


def render_club_logo(width: int = 180) -> None:
    """Display the club logo if the image exists."""
    if LOGO_PATH.is_file():
        st.image(str(LOGO_PATH), width=width)
    else:
        st.warning(
            "Club logo not found. Place it at "
            "assets/chemistry_logo.png"
        )


def main() -> None:
    # Sidebar branding and navigation
    with st.sidebar:
        render_club_logo(width=180)
        st.markdown("**The Chemistry Of Happiness Club**")
        st.divider()

        st.title(f"🧪 {APP_NAME}")
        st.caption(f"v{APP_VERSION} • {APP_TAGLINE}")
        st.divider()

        page_selection = st.radio(
            "Navigation:",
            [
                "📊 Dashboard",
                "📚 Reference Library",
                "📈 Mechanical Testing",
                "🔌 Hardware & Arduino",
            ],
            index=0,
        )

        st.divider()
        st.markdown("### 🔬 Quick Overview")
        st.markdown(
            """
            - **Materials:** PE, PP, PET, PVC, PS, PMMA
            - **Standards:** ASTM D638, ISO 527
            - **Units:** MPa, GPa, %, MJ/m³
            - **Hardware:** Arduino / UTM
            """
        )

        st.divider()
        st.caption("© 2026 PolymerLab AI • Research & Laboratory Suite")

    # Main page: logo and club identity appear on every section.
    render_club_logo(width=140)
    st.caption("The Chemistry Of Happiness Club")
    st.divider()

    if page_selection == "📊 Dashboard":
        render_dashboard()

    elif page_selection == "📚 Reference Library":
        render_library()

    elif page_selection == "📈 Mechanical Testing":
        render_mechanical_testing()

    elif page_selection == "🔌 Hardware & Arduino":
        render_hardware_manager()


if __name__ == "__main__":
    main()